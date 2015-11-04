import threading
import sys
import time
from signal import *

from sqlalchemy.orm import sessionmaker, scoped_session
from sim.dataio import fromjson, tojson
from optima.dbmodels import ProjectDb, WorkingProjectDb, WorkLogDb

# Sentinel object used for async calculation
sentinel = {
    'exit': False  # This will stop all threads
}

# acceptable exit statuses
good_exit_status = set(['completed', 'cancelled'])

# CONSIDER: methods in async_calculate are never called directly (i.e. from FE), so we don't have to prevent a user from opening the project.


def start_or_report_calculation(user_id, project_id, func, db_session): #only called from the application
    work_type = func.__name__
    can_start = False
    can_join = False

    project = db_session.query(ProjectDb).filter_by(id=project_id).first()
    if project is not None:
        work_log = WorkLogDb(project_id=project.id, work_type = work_type)
        db_session.add(work_log)
        db_session.flush()
        if project.working_project is None:
            db_session.add(WorkingProjectDb(project_id=project.id, model = project.model, \
                is_working = True, work_type = work_type, work_log_id = work_log.id))
            can_start = True
            can_join = True
            db_session.commit()
        else:
            # if work_type is None then is_working flag makes no sense
            if (not project.working_project.is_working) or (project.working_project.work_type is None):
                project.working_project.work_type = work_type
                project.working_project.is_working = True
                project.working_project.work_log_id = work_log.id
                db_session.add(project.working_project)
                db_session.commit()
                can_start = True
                can_join = True
            else:
                can_join = work_type == project.working_project.work_type
                work_type = project.working_project.work_type
    else:
        print("No such project %s, cannot start calculation" % project_id)
    return can_start, can_join, work_type


def finish_calculation(user_id, project_id, func, db_session, status='completed', error_text=None, stop_now = False): # pylint: disable=W0613, R0913
    import datetime
    import dateutil.tz
    project = db_session.query(ProjectDb).filter_by(id=project_id).first()
    if project is not None and project.working_project is not None \
    and (project.working_project.is_working or stop_now):
        if project.working_project.work_log_id is not None:
            work_log = db_session.query(WorkLogDb).get(project.working_project.work_log_id)
            work_log.status = status
            work_log.error = error_text
            stop_time = datetime.datetime.now(dateutil.tz.tzutc())
            if not stop_now: stop_time = stop_time + datetime.timedelta(seconds=180) #hopefully enough time to finish one iteration?
            if (not work_log.stop_time) or work_log.stop_time>stop_time: work_log.stop_time = stop_time
            db_session.add(work_log)
        else:
            print("cannot find work_log_id for the project %s" % project.id)
        project.working_project.is_working = False
        project.working_project.work_type = None
        db_session.add(project.working_project)
        db_session.commit()

def cancel_calculation(user_id, project_id, func, db_session):
    finish_calculation(user_id, project_id, func, db_session, status='cancelled')

def check_calculation(user_id, project_id, func, db_session):
    is_working = not sentinel['exit']
    if is_working:
        project = db_session.query(ProjectDb).filter_by(id=project_id).first()
        is_working = project is not None \
        and project.working_project is not None \
        and project.working_project.is_working \
        and project.working_project.work_type == func.__name__
    else:
        finish_calculation(user_id, project_id, func, db_session, 'cancelled','Application Exit', True)

    return is_working

def check_calculation_status(user_id, project_id, func, db_session):
    from sqlalchemy import desc
    status = 'unknown'
    error_text = None
    stop_time = None
    project = db_session.query(ProjectDb).filter_by(id=project_id).first()
    if project is not None:
        work_log = db_session.query(WorkLogDb).filter_by(project_id=project.id, work_type=func.__name__). \
        order_by(desc(WorkLogDb.start_time)).first()
        if work_log is not None:
            status = work_log.status
            error_text = work_log.error
            stop_time = work_log.stop_time
    return status, error_text, stop_time

def interrupt(*args): # pylint: disable=W0613
    global sentinel # pylint: disable=W0602
    print("stopping all threads")
    sentinel['exit'] = True
    sys.exit()

for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, interrupt)


class CalculatingThread(threading.Thread):
    """
    Asynchronous thread to run potentially long calculations for the given project.

    Parameters:
    engine: DB engine to connect to
    sentinel: reference to sentinel (structure used to watch over threads)
    user: current user (new thread does not have the context)
    project_id: current project id
    timelimit: time limit for this thread to run
    func: func which has to be called to perform calculations (receiving D as first argument)
    args: additional arguments for this function

    """

    def __init__(self, engine, user, project_id, timelimit, numiter, func, args, with_stoppingfunc = False): # pylint: disable=R0913
        super(CalculatingThread, self).__init__()

        self.args = args
        self.user_name = user.name
        self.user_id = user.id
        self.project_id = project_id
        self.func = func
        self.debug_args = fromjson(args)
        self.timelimit = int(timelimit) # to be sure
        self.engine = engine
        self.stop_flag = False
        self.leap_seconds = 10
        self.with_stoppingfunc = with_stoppingfunc
        self.last_time_checked = None
        self.start_time = None
        self.db_session = None
        self.max_iterations = numiter
        self.iterations = 0
        print("starting calculating thread for user: %s project %s for %s seconds" % (self.user_name, self.project_id, self.timelimit))

    def init_db_session(self):
        self.db_session = scoped_session(sessionmaker(self.engine)) #creating scoped_session, eventually bound to engine

    def close_db_session(self):
        # this line might be redundant (not 100% sure - not clearly described)
        self.db_session.connection().close() # pylint: disable=E1101
        self.db_session.remove()
        # black magic to actually close the connection by forcing the engine to dispose of garbage (I assume)
        self.db_session.bind.dispose() # pylint: disable=E1101


    def check_stop_flag(self):
        print "has_stop_flag called"
        if self.max_iterations is not None and self.iterations>self.max_iterations:
            print "max number of iterations has passed"
            self.stop_flag = True
        else:
            new_time_checked = time.time()
            if new_time_checked-self.start_time>=self.timelimit:
                print "max allotted time has passed"
                self.stop_flag = True
            elif new_time_checked-self.last_time_checked>=self.leap_seconds:
                print "calling check calculation..."
                self.init_db_session()
                self.stop_flag = not check_calculation(self.user_id, self.project_id, self.func, self.db_session)
                self.close_db_session()
                print "check_calculation(%s) called, stop_flag=%s" % (self.project_id, self.stop_flag)
                self.last_time_checked = new_time_checked


    def has_stop_flag(self):
        if not self.stop_flag: self.check_stop_flag()
        return self.stop_flag

    def call_finish_calculation(self, cancel_status, error_text):
        finish_calculation(self.user_id, self.project_id, self.func, self.db_session, cancel_status, error_text, True)


    def run(self):
        import traceback
        self.start_time = time.time()
        # never checked anything yet
        self.last_time_checked = self.start_time - self.leap_seconds - 1
        self.init_db_session()
        # we start from the current model
        D = self.load_model_user(self.project_id, self.user_id, working_model=False)
        self.close_db_session()
        self.iterations = 1
        error_text = None
        cancel_status = 'completed'
        if self.with_stoppingfunc:
            self.args['stoppingfunc'] = getattr(self, 'has_stop_flag')

        #run the thing once.
        while True:
            # do we have to stop?
            if self.has_stop_flag():
                print("thread for project %s requested to stop" % self.project_id)
                cancel_status = 'cancelled'
                break
            # now we can continue with the iteration
            print("Iteration %d for user: %s, args: %s" % (self.iterations, self.user_name, self.debug_args))
            try:
                D = self.func(D, **self.args)
                self.init_db_session()
                self.save_model_user(self.project_id, self.user_id, D)
                self.close_db_session()
            except Exception:
                var = traceback.format_exc()
                print("ERROR in Iteration %s for user: %s, args: %s calculation: %s\n %s" % (self.iterations, self.user_name, self.debug_args, self.func.__name__, var))
                error_text = var
                cancel_status='error'
                break
            time.sleep(0.5)
            self.iterations += 1
        self.init_db_session()
        self.call_finish_calculation(cancel_status, error_text)
        self.close_db_session()
        print("thread for project %s stopped" % self.project_id)

    def load_model_user(self, project_id, user_id, from_json=True, working_model=True):
        project = self.db_session.query(ProjectDb).filter_by(id=project_id).first()
        model = None
        if project is not None:
            if project.working_project is None or not working_model:
                model = project.model
            else:
                model = project.working_project.model
            if from_json:
                model = fromjson(model)
        return model

    def save_model_user(self, project_id, user_id, model, working_model=True):
        print("save_model_user:%s %s" % (project_id, user_id))
        project = self.db_session.query(ProjectDb).filter_by(id=project_id).first()
        model = tojson(model)
        if project is not None:
            if not working_model:
                project.model = model
                self.db_session.add(project)
            else:
                if project.working_project is None:
                    self.db_session.add(WorkingProjectDb(project_id=project.id, model = model, is_working = True, work_type = self.func.__name__))
                else:
                    project.working_project.model = model
                    self.db_session.add(project.working_project)
            self.db_session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, project_id))
