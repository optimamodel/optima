import traceback
from pprint import pprint, pformat
import datetime
import dateutil.tz
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session
import optima as op

# must import api first
from ..api import app
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

    print "> setup_work_log '%s %s'" % (pyobject_id, work_type)

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
                print ">> setup_work_log cancel job: already exists"
                is_ready_to_start = False

    if is_ready_to_start:
        # clean up completed/error/cancelled records
        if work_log_records.count():
            print ">> setup_work_log cleanup %d oldlogs" %  work_log_records.count()
            for work_log in work_log_records:
                work_log.cleanup()
            work_log_records.delete()

        # create a work_log status is 'started by default'
        print ">> setup_work_log new work log"
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


def start_or_report_project_calculation(project_id, work_type):
    project = dataio.load_project(project_id)
    return setup_work_log(project_id, work_type, project)


def check_calculation_status(pyobject_id, work_type):
    """
    Returns current calculation state of a work_log.
    """
    calc_state = {
        'status': 'unknown',
        'error_text': None,
        'start_time': None,
        'stop_time': None,
        'work_type': ''
    }
    db_session = init_db_session()
    work_log_record = db_session.query(dbmodels.WorkLogDb)\
        .filter_by(project_id=pyobject_id, work_type=work_type)\
        .first()
    if work_log_record:
        print ">> check_calculation_status: existing job of '%s' with same project" % work_type
        calc_state = parse_work_log_record(work_log_record)
    print ">> check_calculation_status", pyobject_id, work_type, calc_state['status']
    close_db_session(db_session)
    if calc_state['status'] == 'error':
        raise Exception(calc_state['error_text'])
    else:
        return calc_state



def check_task(pyobject_id, work_type):
    calc_state = check_calculation_status(pyobject_id, work_type)
    if calc_state['status'] == 'error':
        clear_work_log(pyobject_id, work_type)
        raise Exception(calc_state['error_text'])
    return calc_state


def clear_work_log(project_id, work_type):
    print ">> clear_work_log '%s'" % work_type
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
        result.uid = op.uuid()
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
            optim.projectref = op.Link(project) # Need to restore project link
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
            print(">> Start optimization '%s' for maxtime = %f" % (optim.name, maxtime))
            result = project.optimize(
                name=optim.name,
                parsetname=optim.parsetname,
                progsetname=optim.progsetname,
                objectives=optim.objectives,
                constraints=optim.constraints,
                maxtime=maxtime,
                mc=0, # Set this to zero for now while we decide how to handle uncertainties etc.
            )
            
            print(">> %s" % result.budgets)
            result.uid = op.uuid()
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


@celery_instance.task(bind=True)
def run_boc(self, portfolio_id, project_id, maxtime=2, objectives=None):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {'project_id': project_id, 'work_type':'boc'}
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
        try:
            print ">> Start BOC:"
            project.genBOC(maxtime=maxtime, objectives=objectives, mc=0) # WARNING, might want to run with MC one day
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



def launch_boc(portfolio_id, maxtime=2):
    portfolio = dataio.load_portfolio(portfolio_id)
    for project in portfolio.projects.values():
        project_id = project.uid
        setup_work_log(project_id, 'boc', project)
        run_boc.delay(portfolio_id, project_id, maxtime=maxtime, objectives=portfolio.objectives)



@celery_instance.task(bind=True)
def run_miminize_portfolio(self, portfolio_id, maxtime):

    status = 'started'
    error_text = ""

    db_session = init_db_session()
    kwargs = {'project_id': portfolio_id, 'work_type': 'portfolio'}
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
            print(">> Start GA with maxtime=%s and budget=%s:" % (maxtime, portfolio.objectives['budget']))
            portfolio.runGA(maxtime=maxtime, mc=0, batch=False)
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



def launch_miminize_portfolio(portfolio_id, maxtime=2):
    portfolio = dataio.load_portfolio(portfolio_id)
    calc_state = setup_work_log(portfolio_id, 'portfolio', portfolio)
    if calc_state['status'] != 'started':
        return calc_state, 208
    run_miminize_portfolio.delay(portfolio_id, maxtime)


def make_reconcile_work_type(project_id, progset_id, parset_id, year):
    return "reconcile:" + ":".join([project_id, progset_id, parset_id, str(year)])


@celery_instance.task(bind=True)
def run_reconcile(self, project_id, progset_id, parset_id, year, maxtime):

    status = 'started'
    error_text = ""
    work_type = make_reconcile_work_type(project_id, progset_id, parset_id, year)
    print ">> tasks.run_reconcile", work_type

    db_session = init_db_session()
    kwargs = {'project_id': project_id, 'work_type': work_type}
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
        try:
            print(">> run_reconcile %s" % work_type, maxtime)
            progset = parse.get_progset_from_project(project, progset_id)
            parset = parse.get_parset_from_project_by_id(project, parset_id)
            progset.reconcile(parset, year, uselimits=True, maxtime=maxtime)

            status = 'completed'
        except Exception:
            status = 'error'
            error_text = traceback.format_exc()
            print(">> Error in calculation")
            print(error_text)

        if status == 'completed':
            print(">> run_reconcile save project")
            db_session = init_db_session()
            project_record = dataio.load_project_record(project_id, db_session=db_session)
            project_record.save_obj(project)
            db_session.add(project_record)
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



def launch_reconcile(project_id, progset_id, parset_id, year, maxtime=2):
    work_type = make_reconcile_work_type(project_id, progset_id, parset_id, year)
    print ">> launch_reconcile", work_type
    project = dataio.load_project(project_id)
    calc_state = setup_work_log(project_id, work_type, project)
    if calc_state['status'] == 'started':
        run_reconcile.delay(project_id, progset_id, parset_id, year, maxtime)
    return calc_state


