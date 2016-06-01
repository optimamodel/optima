
import datetime
import dateutil.tz

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session

import optima as op

from server.api import app
from server.webapp.dbmodels import WorkLogDb, WorkingProjectDb
from server.webapp.exceptions import ProjectDoesNotExist
from server.webapp.dataio import save_result_record, load_project_record

from celery import Celery


db = SQLAlchemy(app)

celery_instance = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
celery_instance.conf.update(app.config)

TaskBase = celery_instance.Task


class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)


celery_instance.Task = ContextTask


def init_db_session():
    """
    Create scoped_session, eventually bound to engine
    """
    return scoped_session(sessionmaker(db.engine))


def close_db_session(db_session):
    # this line might be redundant (not 100% sure - not clearly described)
    db_session.connection().close() # pylint: disable=E1101
    db_session.remove()
    # black magic to actually close the connection by forcing the engine to dispose of garbage (I assume)
    db_session.bind.dispose() # pylint: disable=E1101


def start_or_report_calculation(project_id, parset_id, work_type):
    """
    Checks and sets up a WorkLog and WorkingProject for async calculation.
    A WorkingProject takes a given project, a chosen parset and a type of
    calculation to proceed. If a job is requested for a given project with
    the same parset and work_type, then a can-join = True is issued.

    Args:
        project_id: the project that will be extracted and pickled for async calc
        parset_id: the chosen parset for the calculation
        work_type: "autofit" or "optimization"

    Returns:
        A status update on the state of the async queue for the given project.
        {
            'can_start': can_start,
            'can_join': can_join,
            'parset_id': wp_parset_id,
            'work_type': work_type
        }
    """
    print "start_or_report_calculation(%s %s %s)" % (project_id, parset_id, work_type)

    db_session = init_db_session()

    result = {
        'can_start': False,
        'can_join': False,
        'parset_id': parset_id,
        'work_type': work_type
    }

    project_record = load_project_record(project_id, raise_exception=False, db_session=db_session)
    if not project_record:
        close_db_session(db_session)
        raise ProjectDoesNotExist(project_id)

    project = project_record.hydrate()
    project_pickled = op.saves(project)

    working_project_record = db_session.query(WorkingProjectDb).filter_by(id=project_id).first()

    is_already_working = (working_project_record is not None
                          and working_project_record.is_working
                          and (working_project_record.parset_id != parset_id
                               or working_project_record.work_type != work_type))

    if is_already_working:
        print("A WorkingProjectRecord is present for %s with different job settings" % project_id)
        result['work_type'] = working_project_record.work_type
    else:
        work_log = db_session.query(WorkLogDb).filter_by(
            project_id=project_id, parset_id=parset_id, work_type=work_type).first()
        if work_log is None:
            # Log a new job
            work_log = WorkLogDb(project_id=project_id, parset_id=parset_id, work_type=work_type)
            work_log.start_time = datetime.datetime.now(dateutil.tz.tzutc())
        else:
            if work_log.status != 'started':
                working_project_record.is_working = False
                work_log.start_time = datetime.datetime.now(dateutil.tz.tzutc())
        db_session.add(work_log)
        db_session.flush()

        if working_project_record is None:
            print("No working project was found - creating new one")
            db_session.add(
                WorkingProjectDb(
                    project_record.id,
                    parset_id = parset_id,
                    project = project_pickled,
                    is_working = True,
                    work_type = work_type,
                    work_log_id = work_log.id))
            result['can_start'] = True
            result['can_join'] = True

        else:
            is_same_parset_work_type = (working_project_record.parset_id == parset_id
                                        and working_project_record.work_type == work_type)

            print("Found working project for %s: %s %s %s" % (working_project_record.id, working_project_record.work_type, working_project_record.parset_id, working_project_record.is_working))
            result['can_start'] = not working_project_record.is_working
            result['can_join'] = is_same_parset_work_type or not working_project_record.is_working

            if result['can_start']:
                working_project_record.work_type = work_type
                working_project_record.parset_id = parset_id
                working_project_record.is_working = True
                working_project_record.project = project_pickled
                working_project_record.work_log_id = work_log.id
                db_session.add(working_project_record)

            else:
                result['parset_id'] = working_project_record.parset_id
                result['work_type'] = working_project_record.work_type

    db_session.commit()
    close_db_session(db_session)

    return result


def check_calculation_status(project_id):
    db_session = init_db_session()
    wp = db_session.query(WorkingProjectDb).get(project_id)
    work_log = db_session.query(WorkLogDb).get(wp.work_log_id)
    close_db_session(db_session)
    if work_log is not None:
        result = {
            'status': work_log.status,
            'error_text': work_log.error,
            'start_time': work_log.start_time,
            'stop_time': work_log.stop_time,
            'result_id': work_log.result_id
        }
    else:
        result = {
            'status': 'unknown',
            'error_text': None,
            'start_time': None,
            'stop_time': None,
            'result_id': None
        }
    return result


@celery_instance.task()
def run_autofit(project_id, parset_name, maxtime=60):
    import traceback
    app.logger.debug("started autofit: {} {}".format(project_id, parset_name))
    error_text = ""
    status = 'completed'
    db_session = init_db_session()
    wp = db_session.query(WorkingProjectDb).filter_by(id=project_id).first()
    project_instance = op.loads(wp.project)
    close_db_session(db_session)
    result = None
    try:
        project_instance.autofit(
            name=str(parset_name),
            orig=str(parset_name),
            maxtime=maxtime
        )
        result = project_instance.parsets[str(parset_name)].getresults()
        print "result", result
    except Exception:
        var = traceback.format_exc()
        print("ERROR for project_id: %s, args: %s calculation: %s\n %s" % (project_id, parset_name, 'autofit', var))
        error_text = var
        status='error'

    db_session = init_db_session()
    wp = db_session.query(WorkingProjectDb).filter_by(id=project_id).first()
    wp.project = op.saves(project_instance)
    work_log = db_session.query(WorkLogDb).get(wp.work_log_id)
    work_log.status = status
    work_log.error = error_text
    work_log.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    if result:
        result_entry = save_result_record(project_id, result, parset_name, 'autofit', db_session=db_session)
        db_session.add(result_entry)
        db_session.flush()
        work_log.result_id = result_entry.id
    db_session.add(work_log)
    wp.is_working = False
    wp.work_type = None
    db_session.add(wp)
    db_session.commit()
    close_db_session(db_session)
    app.logger.debug("stopped autofit")


@celery_instance.task()
def run_optimization(project_id, optimization_name, parset_name, progset_name, objectives, constraints):
    import traceback
    import pprint
    app.logger.debug('started optimization: {} {} {} {}'.format(
        project_id, optimization_name, parset_name, progset_name, objectives, constraints))
    app.logger.debug(pprint.pformat(objectives, indent=2))
    app.logger.debug(pprint.pformat(constraints, indent=2))

    error_text = ""
    status = 'completed'

    db_session = init_db_session()
    wp = db_session.query(WorkingProjectDb).filter_by(id=project_id).first()
    project_instance = op.loads(wp.project)
    close_db_session(db_session)

    result = None
    if not objectives['budget']:
        objectives['budget'] = 1000000

    try:
        # result = op.defaults.defaultproject('generalized').optimize()
        result = project_instance.optimize(
            name=optimization_name,
            parsetname=parset_name,
            progsetname=progset_name,
            objectives=objectives,
            constraints=constraints
        )
        print "result", result
    except Exception:
        var = traceback.format_exc()
        print("ERROR for project_id: %s, args: %s calculation: %s\n %s" % (project_id, optimization_name, 'optimization', var))
        error_text = var
        status='error'

    db_session = init_db_session()
    wp = db_session.query(WorkingProjectDb).filter_by(id=project_id).first()
    wp.project = op.saves(project_instance)
    work_log = db_session.query(WorkLogDb).get(wp.work_log_id)
    work_log.status = status
    work_log.error = error_text
    work_log.stop_time = datetime.datetime.now(dateutil.tz.tzutc())

    if result:
        result_entry = save_result_record(project_id, result, parset_name, 'optimization', db_session=db_session)
        db_session.add(result_entry)
        db_session.flush()
        work_log.result_id = result_entry.id

    db_session.add(work_log)

    wp.is_working = False
    wp.work_type = None
    db_session.add(wp)
    db_session.commit()
    close_db_session(db_session)

    app.logger.debug("stopped optimization")
