import traceback
from pprint import pprint
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session
import optima as op


__doc__ = """

tasks.py
========

this file has dual purpose:

1. it is a point-of-entry for async calcuationns for api.py
2. it is a stand-alone file for the celery server to receive file

That is, the key function `run_task` is both the sender and receiver
for celery-based async task.

As sender, `run_task.delay` is run, and the function will receive
the function. The key restriction of that the parameters to the
function must be json-compatible data-types: strings, float/int,
dicts and lists.

The celery tasks interacts with the database defined in dbmodels.py,
which is a mix of Postgres and Redis storage.

A special table is used to track jobs in the celery server. This
is `WorkLogDb`. A WorkLogDb entry is created whenever a job is
put on the celery queue.

- A worklog tracks
    - a unique `task_id` that represents the job
    - when the job was started
    - the current time - this is done as time-zones are easily
      lost, so it is better to issue the current-time and
      start-time from the same source, and calculate the difference
      when it is needed at the client

- `parse_work_log_record` converts it into a JSON object that
  can be consumed by the web-client

- in any async function, access to the db has to be carefully
  circumsribed. This is done through a paired call to
  `init_db_session` and `close_db_session`

The function `run_task.delay` should not need to be run directly,
and should be accessed through `launch_task`, which will
set up the worklog before running the task

"""


# this sets up the connection to the flask app and database
# that has already been setup

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
        'task_id': work_log.task_id,
        'current_time': op.today()
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


def check_task(task_id):
    """
    Returns current calculation state of a work_log.
    """
    calc_state = {
        'status': 'unknown',
        'error_text': None,
        'start_time': None,
        'stop_time': None,
        'task_id': ''
    }
    db_session = init_db_session()
    work_log_record = db_session.query(dbmodels.WorkLogDb)\
        .filter_by(task_id=task_id)\
        .first()
    if work_log_record:
        print ">> check_task: existing job of '%s' with same project" % task_id
        calc_state = parse_work_log_record(work_log_record)
    print ">> check_task", task_id, calc_state['status']
    close_db_session(db_session)
    if calc_state['status'] == 'error':
        raise Exception(calc_state['error_text'])
    else:
        return calc_state


def check_if_task_started(task_id):
    calc_state = check_task(task_id)
    if calc_state['status'] == 'error':
        db_session = init_db_session()
        worklogs = db_session.query(dbmodels.WorkLogDb).filter_by(task_id=task_id)
        worklogs.delete()
        db_session.commit()
        raise Exception(calc_state['error_text'])
    return calc_state


@celery_instance.task()
def run_task(task_id, fn_name, args):
    if fn_name in globals():
        task_fn = globals()[fn_name]
    else:
        raise Exception("run_task error: couldn't find '%s'" % fn_name)

    print '>> run_task %s %s' % (fn_name, args)
    try:
        task_fn(*args)
        print ">> run_task completed"
        error_text = ""
        status = 'completed'
    except Exception:
        error_text = traceback.format_exc()
        status = 'error'
        print ">> run_task error"
        print(error_text)

    db_session = init_db_session()
    worklog = db_session.query(dbmodels.WorkLogDb).filter_by(task_id=task_id).first()
    worklog.status = status
    worklog.error = error_text
    worklog.stop_time = op.today()
    db_session.add(worklog)
    db_session.commit()
    close_db_session(db_session)


def launch_task(task_id, fn_name, args):
    print ">> launch_task", task_id, fn_name, args

    db_session = init_db_session()
    query = db_session.query(dbmodels.WorkLogDb)
    work_log_records = query.filter_by(task_id=task_id)
    if work_log_records:
        # if any work_log exists for this project that has started,
        # then this calculation is blocked from starting
        is_ready_to_start = True
        for work_log_record in work_log_records:
            if work_log_record.status == 'started':
                calc_state = parse_work_log_record(work_log_record)
                calc_state["status"] = "blocked"
                print ">> launch_task job already exists"
                is_ready_to_start = False

    if is_ready_to_start:
        # clean up completed/error/cancelled records
        if work_log_records.count():
            print ">> launch_task cleanup %d logs" %  work_log_records.count()
            work_log_records.delete()

        # create a work_log status is 'started by default'
        print ">> launch_task new work log"
        work_log_record = dbmodels.WorkLogDb(task_id=task_id)
        work_log_record.start_time = op.today()
        db_session.add(work_log_record)
        db_session.flush()

        calc_state = parse_work_log_record(work_log_record)

    db_session.commit()
    close_db_session(db_session)

    if calc_state['status'] != "blocked":
        run_task.delay(task_id, fn_name, args)

    return calc_state


### PROJECT DEFINED TASKS


# To add tasks, simply create a new function here:
#
# - all parameters must be JOSN compatible: strings, numbers, lists or dicts
# - access to database must be done through an db_session created
#   by init_db_session
# - db_session must be closed
# - once registered, you can call these functions via
#   the `rpcService.runAsyncTask('launch_task')` interface


def autofit(project_id, parset_id, maxtime):

    db_session = init_db_session()
    project = dataio.load_project(project_id, db_session=db_session, authenticate=False)
    close_db_session(db_session)

    orig_parset = parse.get_parset_from_project_by_id(project, parset_id)
    orig_parset_name = orig_parset.name
    print ">> autofit '%s' '%s'" % (project_id, orig_parset_name)
    parset_id = orig_parset.uid
    autofit_parset_name = "autofit-" + str(orig_parset_name)

    project.autofit(
        name=autofit_parset_name,
        orig=orig_parset_name,
        maxtime=float(maxtime)
    )

    result = project.parsets[autofit_parset_name].getresults()
    result_name = 'parset-' + orig_parset_name
    result.name = result_name

    print(">> autofit parset '%s' -> '%s' " % (autofit_parset_name, orig_parset_name))
    autofit_parset = project.parsets[autofit_parset_name]
    autofit_parset.name = orig_parset.name
    autofit_parset.uid = orig_parset.uid
    del project.parsets[orig_parset_name]
    project.parsets[orig_parset_name] = autofit_parset
    del project.parsets[autofit_parset_name]

    db_session = init_db_session()

    # save project
    project_record = dataio.load_project_record(project_id, db_session=db_session)
    project_record.save_obj(project)
    db_session.add(project_record)

    # save result
    dataio.delete_result_by_parset_id(project_id, parset_id, db_session=db_session)
    result_record = dataio.update_or_create_result_record_by_id(
        result, project_id, orig_parset.uid, 'calibration', db_session=db_session)
    db_session.add(result_record)

    db_session.commit()
    close_db_session(db_session)

    print("> autofit finish")


def optimize(project_id, optimization_id, maxtime):

    db_session = init_db_session()
    project = dataio.load_project(project_id, db_session=db_session, authenticate=False)
    close_db_session(db_session)

    optim = parse.get_optimization_from_project(project, optimization_id)
    print(">> optimize '%s' for maxtime = %s" % (optim.name, maxtime))

    optim.projectref = op.Link(project)  # Need to restore project link
    progset = project.progsets[optim.progsetname]
    if not progset.readytooptimize():
        error_text = "Not ready to optimize\n"
        costcov_errors = progset.hasallcostcovpars(detail=True)
        if costcov_errors:
            error_text += "Missing: cost-coverage parameters of:\n"
            error_text += pprint.pformat(costcov_errors, indent=2)
        covout_errors = progset.hasallcovoutpars(detail=True)
        if covout_errors:
            error_text += "Missing: coverage-outcome parameters of:\n"
            error_text += pprint.pformat(covout_errors, indent=2)
        raise Exception(error_text)

    print(">> optimize start")
    result = project.optimize(optim=optim, maxtime=float(maxtime), mc=0)  # Set this to zero for now while we decide how to handle uncertainties etc.

    print(">> optimize budgets %s" % result.budgets)
    
    # save project
    db_session = init_db_session()
    project_record = dataio.load_project_record(project_id, db_session=db_session)
    project_record.save_obj(project)
    db_session.add(project_record)

    # save result
    dataio.delete_result_by_name(project_id, result.name, db_session)
    parset = project.parsets[optim.parsetname]
    result_record = dataio.update_or_create_result_record_by_id(
        result, project_id, parset.uid, 'optimization', db_session=db_session)
    print(">> optimize results '%s'" % result.name)
    db_session.add(result_record)
    db_session.commit()
    close_db_session(db_session)

    print ">> optimize finish"
    
    print('TEMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMP')
    print project.optims
    print('FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO')



def reconcile(project_id, progset_id, parset_id, year, maxtime):
    year = int(year)
    maxtime = int(maxtime)

    db_session = init_db_session()
    project = dataio.load_project(project_id, db_session=db_session, authenticate=False)
    close_db_session(db_session)

    print(">> reconcile started")
    progset = parse.get_progset_from_project(project, progset_id)
    parset = parse.get_parset_from_project_by_id(project, parset_id)
    progset.reconcile(parset, year, uselimits=True, maxtime=float(maxtime))

    print(">> reconcile save project")
    db_session = init_db_session()
    project_record = dataio.load_project_record(project_id, db_session=db_session)
    project_record.save_obj(project)
    db_session.add(project_record)
    db_session.commit()
    close_db_session(db_session)

    print ">> reconcile finish"



def boc(portfolio_id, project_id, maxtime=2, objectives=None):

    db_session = init_db_session()
    portfolio = dataio.load_portfolio(portfolio_id, db_session)
    close_db_session(db_session)

    for project in portfolio.projects.values():
        if project_id == str(project.uid):
            break
    else:
        raise Exception("Couldn't find project in portfolio")

    project.genBOC(maxtime=float(maxtime), objectives=objectives, mc=0) # WARNING, might want to run with MC one day

    project_id = str(project.uid)
    db_session = init_db_session()
    portfolio = dataio.load_portfolio(portfolio_id, db_session) # Reload portfolio, since another BOC task probably changed it
    portfolio.projects[project_id] = project
    dataio.save_portfolio(portfolio, db_session)
    close_db_session(db_session)

    print ">> boc finish"



def ga_optimize(portfolio_id, maxtime):

    db_session = init_db_session()
    portfolio = dataio.load_portfolio(portfolio_id, db_session)
    close_db_session(db_session)

    portfolio.runGA(maxtime=float(maxtime), mc=0, batch=False)

    db_session = init_db_session()
    dataio.save_portfolio(portfolio, db_session=db_session)
    close_db_session(db_session)

    print ">> ga_optimize finish"




