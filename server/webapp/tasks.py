import traceback
from pprint import pformat
import datetime
import dateutil.tz
import server.webapp.parse

from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session

import optima

from multiprocessing.dummy import Process, Queue

# this is needed to disable multiprocessing in the portfolio
# module so that celery can handle the multiprocessing itself
optima.portfolio.Process = Process
optima.portfolio.Queue = Queue

# must import api first
from ..api import app
from .dbconn import db
from . import dbmodels, parse, dataio


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


def parse_work_log_record(work_log):
    return {
        'status': work_log.status,
        'task_id': work_log.task_id,
        'error_text': work_log.error,
        'start_time': work_log.start_time,
        'stop_time': work_log.stop_time,
        'project_id': work_log.project_id,
        'work_type': work_log.work_type,
        'current_time': datetime.datetime.now(dateutil.tz.tzutc())
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


def setup_work_log(pyobject_id, work_type, pyobject):
    """
    Sets up a work_log for project_id calculation, returns a work_log_record dictionary
    """

    print("> Put on celery, a job of '%s %s'" % (pyobject_id, work_type))

    db_session = init_db_session()

    # if any work_log exists for this project that has started,
    # then this calculation is blocked from starting
    is_ready_to_start = True
    work_log_records = db_session.query(dbmodels.WorkLogDb).filter_by(
        project_id=pyobject_id, work_type=work_type)
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
        work_log_record = dbmodels.WorkLogDb(
            project_id=pyobject_id, work_type=work_type)
        work_log_record.start_time = datetime.datetime.now(dateutil.tz.tzutc())
        db_session.add(work_log_record)
        db_session.flush()

        work_log_record.save_obj(pyobject)
        calc_state = parse_work_log_record(work_log_record)

    db_session.commit()
    close_db_session(db_session)

    return calc_state


def delete_task(pyobject_id, work_type):
    print("> Delete ", pyobject_id, work_type)
    work_log_record = db.session.query(dbmodels.WorkLogDb).filter_by(
        project_id=pyobject_id, work_type=work_type).first()
    if not work_log_record:
        return "Job not found"

    task_id = work_log_record.task_id
    if not task_id:
        return "No celery task found for job"

    task_id = str(task_id)
    print("Delete task", task_id, type(task_id))
    celery_instance.control.revoke(str(task_id))
    work_log = db.session.query(dbmodels.WorkLogDb).filter_by(task_id=task_id).first()
    work_log.status = 'cancelled'
    work_log.cleanup()
    db.session.add(work_log)
    db.session.commit()

    return "Deleted job"


def start_or_report_project_calculation(project_id, work_type):
    project = dataio.load_project(project_id)
    return setup_work_log(project_id, work_type, project)


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
    work_log_records = db_session.query(dbmodels.WorkLogDb).filter_by(
        project_id=project_id, work_type=work_type)
    work_log_records.delete()
    db_session.commit()
    close_db_session(db_session)


def check_calculation_status(pyobject_id, work_type):
    """
    Returns current calculation state of a work_log.
    """
    result = {
        'status': 'unknown',
        'error_text': None,
        'start_time': None,
        'stop_time': None,
        'work_type': ''
    }
    db_session = init_db_session()
    print("Check calculation status", pyobject_id, work_type)
    work_log_record = db_session.query(dbmodels.WorkLogDb)\
        .filter_by(project_id=pyobject_id, work_type=work_type)\
        .first()
    if work_log_record:
        print ">> Found existing job of '%s' with same project" % work_type
        result = parse_work_log_record(work_log_record)
    close_db_session(db_session)
    return result



def check_task(pyobject_id, work_type):
    calc_state = check_calculation_status(pyobject_id, work_type)
    print("> Checking calc state")
    print(pformat(calc_state, indent=2))
    if calc_state['status'] == 'error':
        clear_work_log(pyobject_id, work_type)
        raise Exception(calc_state['error_text'])
    return calc_state


def clear_work_log(project_id, work_type):
    print(">> Deleting work logs of '%s'" % work_type)
    db_session = init_db_session()
    work_logs = db_session.query(dbmodels.WorkLogDb).filter_by(project_id=project_id, work_type=work_type)
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
    work_log = db_session.query(dbmodels.WorkLogDb).filter_by(
        project_id=project_id, work_type=work_type).first()
    close_db_session(db_session)

    if work_log is None:
        print("> Error: couldn't find work log")
        return

    work_log_id = work_log.id

    try:
        project = work_log.load()
        orig_parset = parse.get_parset_from_project_by_id(project, parset_id)
        orig_parset_name = orig_parset.name
        parset_id = orig_parset.uid
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
        del project.parsets[orig_parset_name]
        project.parsets[orig_parset_name] = autofit_parset
        del project.parsets[autofit_parset_name]

        error_text = ""
        status = 'completed'
    except Exception:
        result = None
        error_text = traceback.format_exc()
        status = 'error'
        print(">> Error in autofit")
        print(error_text)

    if result:
        print(">> Save autofitted parset '%s' to '%s' " % (autofit_parset_name, orig_parset_name))
        db_session = init_db_session()
        project_record = dataio.load_project_record(project_id, db_session=db_session)
        project_record.save_obj(project)
        db_session.add(project_record)
        dataio.delete_result_by_parset_id(project_id, parset_id, db_session=db_session)
        result_record = dataio.update_or_create_result_record_by_id(
            result, project_id, orig_parset.uid, 'calibration', db_session=db_session)
        print(">> Save result '%s'" % result.name)
        db_session.add(result_record)
        db_session.commit()
        close_db_session(db_session)

    db_session = init_db_session()
    work_log = db_session.query(dbmodels.WorkLogDb).get(work_log_id)
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
    calc_status = start_or_report_project_calculation(project_id, work_type)
    if calc_status['status'] != "blocked":
        print "> Starting autofit for %s s" % maxtime
        run_autofit.delay(project_id, parset_id, maxtime)
        calc_status['maxtime'] = maxtime
    return calc_status



@celery_instance.task(bind=True)
def run_optimization(self, project_id, optimization_id, maxtime, start=None, end=None):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    work_log = db_session.query(dbmodels.WorkLogDb).filter_by(
        project_id=project_id, work_type='optim-' + str(optimization_id)).first()

    if work_log:
        work_log_id = work_log.id

        work_log.task_id = self.request.id
        print(">> Celery task_id = %s" % work_log.task_id)
        db_session.add(work_log)
        db_session.commit()

        try:
            project = work_log.load()
            optim = parse.get_optimization_from_project(project, optimization_id)
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
            objectives = server.webapp.parse.normalize_obj(optim.objectives)
            constraints = server.webapp.parse.normalize_obj(optim.constraints)
            constraints["max"] = optima.odict(constraints["max"])
            constraints["min"] = optima.odict(constraints["min"])
            constraints["name"] = optima.odict(constraints["name"])
            print(">> maxtime = %f" % maxtime)
            parse.print_odict("objectives", objectives)
            parse.print_odict("constraints", constraints)
            result = project.optimize(
                name=optim.name,
                parsetname=optim.parsetname,
                progsetname=optim.progsetname,
                objectives=objectives,
                constraints=constraints,
                maxtime=maxtime,
                mc=0, # Set this to zero for now while we decide how to handle uncertainties etc.
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
            dataio.delete_result_by_name(project_id, result.name, db_session)
            parset = project.parsets[optim.parsetname]
            result_record = dataio.update_or_create_result_record_by_id(
                result, project_id, parset.uid, 'optimization', db_session=db_session)
            db_session.add(result_record)
            db_session.commit()
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(dbmodels.WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"


def launch_optimization(project_id, optimization_id, maxtime, start=None, end=None):
    calc_state = start_or_report_project_calculation(
        project_id, 'optim-' + str(optimization_id))
    if calc_state['status'] != 'started':
        return calc_state, 208
    run_optimization.delay(project_id, optimization_id, maxtime, start, end)
    return calc_state


def check_optimization(project_id, optimization_id):
    work_type = 'optim-' + str(optimization_id)
    calc_state = check_calculation_status(project_id, work_type)
    print("> Checking calc state")
    print(pformat(calc_state, indent=2))
    if calc_state['status'] == 'error':
        clear_work_log(project_id, work_type)
        raise Exception(calc_state['error_text'])
    return calc_state


def get_gaoptim(project, gaoptim_id):
    for gaoptim in project.gaoptims.values():
        if str(gaoptim.uid) == str(gaoptim_id):
            return gaoptim
    return None


@celery_instance.task(bind=True)
def run_boc(self, portfolio_id, project_id, gaoptim_id, maxtime=2):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {
        'project_id': project_id,
        'work_type': 'gaoptim-' + str(gaoptim_id)
    }
    work_log = db_session.query(dbmodels.WorkLogDb).filter_by(**kwargs).first()
    if work_log:
        work_log_id = work_log.id
        work_log.task_id = self.request.id
        print(">> Celery task_id = %s" % work_log.task_id)
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
            parse.print_odict("gaoptim", gaoptim)
            project.genBOC(objectives=gaoptim.objectives, maxtime=maxtime)
            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if status == 'completed':
            db_session = init_db_session()
            portfolio = dataio.load_portfolio(portfolio_id, db_session)
            project_id = str(project.uid)
            portfolio.projects[project_id] = project
            dataio.save_portfolio(portfolio, db_session)
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(dbmodels.WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"



def launch_boc(portfolio_id, gaoptim_id, maxtime=2):
    portfolio = dataio.load_portfolio(portfolio_id)
    gaoptims = portfolio.gaoptims
    for project in portfolio.projects.values():
        project_id = project.uid
        optima.migrate(project)
        project.gaoptims = gaoptims
        calc_state = setup_work_log(
            project_id, 'gaoptim-' + str(gaoptim_id), project)
        run_boc.delay(portfolio_id, project_id, gaoptim_id, maxtime)



@celery_instance.task(bind=True)
def run_miminize_portfolio(self, portfolio_id, gaoptim_id, maxtime):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {
        'project_id': portfolio_id,
        'work_type': 'portfolio-' + str(gaoptim_id)
    }
    work_log = db_session.query(dbmodels.WorkLogDb).filter_by(**kwargs).first()
    if work_log:
        work_log_id = work_log.id
        work_log.task_id = self.request.id
        print(">> Celery task_id = %s" % work_log.task_id)
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
        try:
            gaoptim = get_gaoptim(portfolio, gaoptim_id)
            objectives = gaoptim.objectives
            print ">> Start BOC:"
            parse.print_odict("gaoptim", gaoptim)
            portfolio.fullGA(objectives=objectives, maxtime=maxtime)
            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if status == 'completed':
            db_session = init_db_session()
            dataio.save_portfolio(portfolio, db_session=db_session)
            close_db_session(db_session)

    db_session = init_db_session()
    work_log_record = db_session.query(dbmodels.WorkLogDb).get(work_log_id)
    work_log_record.status = status
    work_log_record.error = error_text
    work_log_record.stop_time = datetime.datetime.now(dateutil.tz.tzutc())
    work_log_record.cleanup()
    db_session.commit()
    close_db_session(db_session)

    print ">> Finish optimization"



def launch_miminize_portfolio(portfolio_id, gaoptim_id, maxtime=2):
    portfolio = dataio.load_portfolio(portfolio_id)
    for project in portfolio.projects.values():
        optima.migrate(project)
    calc_state = setup_work_log(
        portfolio_id, 'portfolio-' + str(gaoptim_id), portfolio)
    if calc_state['status'] != 'started':
        return calc_state, 208
    run_miminize_portfolio.delay(portfolio_id, gaoptim_id, maxtime)


