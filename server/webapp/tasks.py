import datetime
import pprint
import traceback

import dateutil.tz
from celery import Celery
from celery.task.control import revoke
from flask.ext.login import current_user
from flask.ext.sqlalchemy import SQLAlchemy

import optima

# must import api before all other server modules
from server.api import app
from server.webapp.dataio import load_project_record
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb

from server.webapp.parse import print_odict
from sqlalchemy.orm import sessionmaker, scoped_session

from .dataio import update_or_create_result_record, \
    load_project, load_project_record, delete_result_by_name
from .dbmodels import WorkLogDb
from .parse import get_optimization_from_project, get_parset_from_project_by_id
from .utils import normalize_obj

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


def delete_task(task_id):
    task_id = str(task_id)
    print("Delete task", task_id, type(task_id))
    celery_instance.control.revoke(str(task_id))
    work_log = db.session.query(WorkLogDb).filter_by(task_id=task_id).first()
    work_log.status = 'cancelled'
    work_log.cleanup()
    db.session.add(work_log)
    db.session.commit()
    return "success"


def parse_work_log_record(work_log):
    return {
        'status': work_log.status,
        'task_id': work_log.task_id,
        'error_text': work_log.error,
        'start_time': work_log.start_time,
        'stop_time': work_log.stop_time,
        'project_id': work_log.project_id,
        'work_type': work_log.work_type,
        'current_time': datetime.datetime.now(dateutil.tz.tzutc()),
    }


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


def start_or_report_calculation(project_id, work_type):
    """
    Checks and sets up a WorkLog and WorkingProject for async calculation.
    A WorkingProject takes a given project, a chosen parset and a type of
    calculation to proceed. If a job is requested for a given project with
    the same parset and work_type, then a can-join = True is issued.

    Only one job per project_id is allowed to run. There should only be
    one existing WorkingProjectDb in existence for a project id. Obviously.
    This WorkingProjectDb should be deleted when the job is finished. The
    results are saved in a ResultsDb and a ParsetsDb (for autofit).

    There should only be one WorkLogDb active with a self.status == 'started'.
    Other WorkLogDb must have self.status == 'completed', 'cancelled', 'error'.


    Args:
        project_id: uuid of project that will be extracted and pickled for async calc
        work_type: "autofit" or "optimization"

    Returns:
        A status update on the state of the async queue for the given project.
    Returns:
        {
            'status': 'started', 'ready', 'completed', 'cancelled', 'error', 'blocked'
            'error_text': str
            'start_time': datetime
            'stop_time': datetime
            'work_type': 'autofit' or 'optim-*'
        }
    """

    print "> Put on celery, a job of '%s'" % work_type

    db_session = init_db_session()

    # if any work_log exists for this project that has started,
    # then this calculation is blocked from starting
    is_ready_to_start = True
    work_log_records = db_session.query(WorkLogDb).filter_by(
        project_id=project_id, work_type=work_type)
    if work_log_records:
        for work_log_record in work_log_records:
            if work_log_record.status == 'started':
                calc_state = parse_work_log_record(work_log_record)
                calc_state["status"] = "blocked"
                print ">> Cancel job: already exists similar job"
                is_ready_to_start = False

    if is_ready_to_start:
        # clean up completed/error/cancelled records
        if work_log_records.count():
            print ">> Cleanup %d outdated work logs" %  work_log_records.count()
            for work_log in work_log_records:
                work_log.cleanup()
            work_log_records.delete()

        # create a work_log status is 'started by default'
        print ">> Create work log"
        work_log_record = WorkLogDb(
            project_id=project_id, work_type=work_type)
        work_log_record.start_time = datetime.datetime.now(dateutil.tz.tzutc())
        db_session.add(work_log_record)
        db_session.flush()

        project = load_project(project_id, db_session=db_session)
        work_log_record.save_obj(project)
        calc_state = parse_work_log_record(work_log_record)

    db_session.commit()
    close_db_session(db_session)

    return calc_state


def shut_down_calculation(project_id, work_type):
    """
    Deletes all associated work_log_record's associated with these
    parameters so that the celery tasks with these parameters can
    be restarted in the future. Mainly to delete work_log_record
    that have started but found to fail somewhere else

    Args:
        project_id: uuid of project that will be extracted and pickled for async calc
        work_type: "autofit" or "optimization"
    """
    db_session = init_db_session()
    work_log_records = db_session.query(WorkLogDb).filter_by(
        project_id=project_id, work_type=work_type)
    work_log_records.delete()
    db_session.commit()
    close_db_session(db_session)


def check_calculation_status(project_id, work_type):
    """
    Checks the current calculation state of a project.

    Args:
        project_id: uuid of project

    Returns:
        {
            'status': 'started', 'completed', 'cancelled', 'error', 'blocked'
            'error_text': str
            'start_time': datetime
            'stop_time': datetime
            'work_type': 'autofit' or 'optim-*'
        }
    """

    db_session = init_db_session()
    work_log_record = db_session.query(WorkLogDb)\
        .filter_by(project_id=project_id, work_type=work_type)\
        .first()
    if work_log_record:
        print ">> Found existing job of '%s' with same project" % work_type
        result = parse_work_log_record(work_log_record)
    else:
        result = {
            'status': 'unknown',
            'error_text': None,
            'start_time': None,
            'stop_time': None,
            'work_type': ''
        }
    close_db_session(db_session)
    return result


def clear_work_log(project_id, work_type):
    print(">> Deleting work logs of '%s'" % work_type)
    db_session = init_db_session()
    work_logs = db_session.query(WorkLogDb).filter_by(project_id=project_id, work_type=work_type)
    for work_log in work_logs:
        work_log.cleanup()
    work_logs.delete()
    db_session.commit()
    close_db_session(db_session)


@celery_instance.task()
def run_autofit(project_id, parset_id, maxtime=60):
    import traceback

    work_type = 'autofit-' + str(parset_id)
    print("> Start autofit for project '%s' work_type='%s'" % (project_id, work_type))

    db_session = init_db_session()
    work_log = db_session.query(WorkLogDb).filter_by(
        project_id=project_id, work_type=work_type).first()
    close_db_session(db_session)

    if work_log is None:
        print("> Error: couldn't find work log")
        return

    work_log_id = work_log.id

    result = None
    try:
        project = work_log.load()
        orig_parset = get_parset_from_project_by_id(project, parset_id)
        orig_parset_name = orig_parset.name
        autofit_parset_name = "autofit-"+str(orig_parset_name)

        project.autofit(
            name=autofit_parset_name,
            orig=orig_parset_name,
            maxtime=maxtime
        )

        result = project.parsets[autofit_parset_name].getresults()
        result.uid = optima.uuid()
        result_name = 'parset-' + orig_parset_name
        result.name = result_name

        autofit_parset = project.parsets[autofit_parset_name]
        autofit_parset.name = orig_parset.name
        autofit_parset.uid = orig_parset.uid
        project.parsets.pop(orig_parset_name)
        project.parsets[orig_parset_name] = autofit_parset
        del project.parsets[autofit_parset_name]

        error_text = ""
        status = 'completed'
    except Exception:
        error_text = traceback.format_exc()
        status = 'error'
        print(">> Error in autofit")
        print(error_text)

    if result:
        print(">> Save autofitted parset '%s' to '%s' " % (autofit_parset_name, orig_parset_name))
        print(">> Check parset '%s': %s " % (orig_parset_name, orig_parset_name in project.parsets))
        print(">> Check parset '%s': %s " % (autofit_parset_name, autofit_parset_name in project.parsets))
        db_session = init_db_session()
        project_record = load_project_record(project_id, db_session=db_session)
        project_record.save_obj(project)
        db_session.add(project_record)
        delete_result_by_name(project_id, result_name, db_session=db_session)
        result_record = update_or_create_result_record(
            project, result, orig_parset_name, 'calibration', db_session=db_session)
        print(">> Save result '%s'" % result.name)
        db_session.add(result_record)
        db_session.commit()
        close_db_session(db_session)

    db_session = init_db_session()
    work_log = db_session.query(WorkLogDb).get(work_log_id)
    work_log.status = status
    work_log.error = error_text
    work_log.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log.cleanup()
    db_session.add(work_log)
    db_session.commit()
    close_db_session(db_session)

    print("> Finish autofit")



def launch_autofit(project_id, parset_id, maxtime):
    work_type = 'autofit-' + str(parset_id)
    calc_status = start_or_report_calculation(project_id, work_type)
    if calc_status['status'] != "blocked":
        print "> Starting autofit for %s s" % maxtime
        run_autofit.delay(project_id, parset_id, maxtime)
        calc_status['maxtime'] = maxtime
    return calc_status



@celery_instance.task(bind=True)
def run_optimization(self, project_id, optimization_id, maxtime):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    work_log = db_session.query(WorkLogDb).filter_by(
        project_id=project_id, work_type='optim-' + str(optimization_id)).first()

    if work_log:
        work_log_id = work_log.id

        work_log.task_id = self.request.id
        print(">> Celery task_id = %s" % work_log.task_id)
        db_session.add(work_log)
        db_session.commit()

        try:
            project = work_log.load()
            optim = get_optimization_from_project(project, optimization_id)
            progset = project.progsets[optim.progsetname]
            if not progset.readytooptimize():
                status = 'error'
                error_text = "Not ready to optimize\n"
                costcov_errors = progset.hasallcostcovpars(detail=True)
                if costcov_errors:
                    error_text += "Missing: cost-coverage parameters of:\n"
                    error_text += pprint.pformat(costcov_errors, indent=2)
                covout_errors = progset.hasallcovoutpars(detail=True)
                if covout_errors:
                    error_text += "Missing: coverage-outcome parameters of:\n"
                    error_text += pprint.pformat(covout_errors, indent=2)
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in initialization")
            print(error_text)

    close_db_session(db_session)

    if work_log is None:
        print(">> Error: couldn't find work log")
        return

    if status == 'started':
        result = None
        try:
            print ">> Start optimization '%s'" % optim.name
            objectives = normalize_obj(optim.objectives)
            constraints = normalize_obj(optim.constraints)
            constraints["max"] = optima.odict(constraints["max"])
            constraints["min"] = optima.odict(constraints["min"])
            constraints["name"] = optima.odict(constraints["name"])
            print(">> maxtime = %f" % maxtime)
            print_odict("objectives", objectives)
            print_odict("constraints", constraints)
            result = project.optimize(
                name=optim.name,
                parsetname=optim.parsetname,
                progsetname=optim.progsetname,
                objectives=objectives,
                constraints=constraints,
                maxtime=maxtime,
            )
            result.uid = optima.uuid()
            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if result:
            db_session = init_db_session()
            delete_result_by_name(project_id, result.name, db_session)
            result_record = update_or_create_result_record(
                project, result, optim.parsetname, 'optimization', db_session=db_session)
            db_session.add(result_record)
            db_session.commit()
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"


def launch_optimization(project_id, optimization_id, maxtime):
    calc_state = start_or_report_calculation(
        project_id, 'optim-' + str(optimization_id))
    if calc_state['status'] != 'started':
        return calc_state, 208
    run_optimization.delay(project_id, optimization_id, maxtime)
    return calc_state


def get_gaoptim(project, gaoptim_id):
    for gaoptim in project.gaoptims.values():
        if str(gaoptim.uid) == str(gaoptim_id):
            return gaoptim
    return None


@celery_instance.task(bind=True)
def run_boc(self, project_id, gaoptim_id):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {
        'project_id': project_id,
        'work_type': 'gaoptim-' + str(gaoptim_id)
    }
    work_log = db_session.query(WorkLogDb).filter_by(**kwargs).first()
    if work_log:
        work_log_id = work_log.id
        work_log.task_id = self.request.id
        try:
            project = work_log.load()
            db_session.add(work_log)
            db_session.commit()
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in initialization")
            print(error_text)
    close_db_session(db_session)

    if work_log is None:
        print(">> Error: couldn't find work log")
        return

    if status == 'started':
        result = None
        try:
            gaoptim = get_gaoptim(project, gaoptim_id)
            print ">> Start BOC:"
            print_odict("gaoptim", gaoptim)
            result = project.genBOC(objectives=gaoptim.objectives)
            result.uid = optima.uuid()
            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if result:
            db_session = init_db_session()
            delete_result_by_name(project_id, result.name, db_session)
            result_record = update_or_create_result_record(
                project, result, optim.parsetname, 'optimization', db_session=db_session)
            db_session.add(result_record)
            db_session.commit()
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"



def launch_boc(portfolio_id, gaoptim_id):
    portfolio = optima.loadobj("server/example/malawi-decent-two-state.prt", verbose=0)
    gaoptims = portfolio.gaoptims
    for project in portfolio.projects.values():
        project_id = project.uid
        project.gaoptims = gaoptims
        project_record = load_project_record(project_id, raise_exception=False)
        if not project_record:
            project_record = ProjectDb(current_user.id)
            project_record.id = project.uid
            db.session.add(project_record)
            db.session.commit()
        project_record.save_obj(project)
        calc_state = start_or_report_calculation(
            project_id, 'gaoptim-' + str(gaoptim_id))
        if calc_state['status'] != 'started':
            return calc_state, 208
        run_boc.delay(project_id, gaoptim_id)



@celery_instance.task(bind=True)
def run_miminize_portfolio(self, portfolio_id, gaoptim_id):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {
        'project_id': portfolio_id,
        'work_type': 'portfolio-' + str(gaoptim_id)
    }
    work_log = db_session.query(WorkLogDb).filter_by(**kwargs).first()
    if work_log:
        work_log_id = work_log.id
        work_log.task_id = self.request.id
        try:
            portfolio = work_log.load()
            db_session.add(work_log)
            db_session.commit()
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in initialization")
            print(error_text)
    close_db_session(db_session)

    if work_log is None:
        print(">> Error: couldn't find work log")
        return

    if status == 'started':
        result = None
        try:
            gaoptim = get_gaoptim(portfolio, gaoptim_id)
            objectives = gaoptim.objectives
            print ">> Start BOC:"
            print_odict("gaoptim", gaoptim)
            outcomes = portfolio.fullGA(objectives=objectives)
            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if result:
            db_session = init_db_session()
            delete_result_by_name(project_id, result.name, db_session)
            result_record = update_or_create_result_record(
                project, result, optim.parsetname, 'optimization', db_session=db_session)
            db_session.add(result_record)
            db_session.commit()
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"



def launch_miminize_portfolio(portfolio_id, gaoptim_id):
    # We for the project record to take a portfolio
    # eventually we want to replace the project_record
    # to object id, this is part of a future refactoring
    portfolio = optima.loadobj("server/example/malawi-decent-two-state.prt", verbose=0)
    project_record = load_project_record(portfolio_id, raise_exception=False)
    if not project_record:
        project_record = ProjectDb(current_user.id)
        project_record.id = portfolio.uid
        db.session.add(project_record)
        db.session.commit()
    project_record.save_obj(portfolio, is_skip_result=False)
    calc_state = start_or_report_calculation(
        portfolio_id, 'portfolio-' + str(gaoptim_id))
    if calc_state['status'] != 'started':
        return calc_state, 208

    run_miminize_portfolio.delay(portfolio_id, gaoptim_id)
