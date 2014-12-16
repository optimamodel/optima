import threading
import sys
import time
from signal import *

from sqlalchemy.orm import sessionmaker, scoped_session
from sim.bunch import Bunch
from dbmodels import ProjectDb, WorkingProjectDb

lock = threading.Lock()

# Sentinel object used for async calculation
sentinel = {
    'exit': False,  # This will stop all threads
    'projects': {}  # This will contain an entry per user project indicating if the calculating thread is running
}

def start_or_report_calculation(project, func):
    name = func.__name__
    can_start = False
    can_join = False
    with lock:
        if not project in sentinel['projects']:
            sentinel['projects'][project] = {}
        if not sentinel['projects'][project]:
            sentinel['projects'][project] = name
            can_start = True
        else:
            name = sentinel['projects'][project]
    can_join = name==func.__name__
    return can_start, can_join, name

def cancel_calculation(project, func):
    with lock:
        if project in sentinel['projects'] and sentinel['projects'][project]==func.__name__: #otherwise there is already other calculation
            sentinel['projects'][project] = False
 
def check_calculation(project, func):
    with lock:
        return project in sentinel['projects'] and sentinel['projects'][project]==func.__name__

def interrupt(*args):
    print("stopping all threads")
    sentinel['exit'] = True
    sys.exit()

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, interrupt)


"""
Asynchronous thread to run potentially long calculations for the given project.
Parameters:
engine: DB engine to connect to
sentinel: reference to sentinel (structure used to watch over threads)
user: current user (new thread does not have the context)
project_name: current project name
timelimit: time limit for this thread to run
func: func which has to be called to perform calculations (receiving D as first argument)
args: additional arguments for this function
"""
class CalculatingThread(threading.Thread):
    def __init__(self, engine, user, project_name, timelimit, func, args):
        super(CalculatingThread, self).__init__()

        self.args = args
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name
        self.engine = engine
        self.func = func
        self.args = args
        self.args['verbose']=0
        self.timelimit = int(timelimit) # to be sure
        print("starting calculating thread for user: %s project %s for %s seconds" % (self.user_name, self.project_name, self.timelimit))

    def run(self):
        D = self.load_model_user(self.project_name, self.user_id, working_model = False) #we start from the current model

        iterations = 1
        delta_time = 0
        start = time.time()
        while delta_time < self.timelimit:
            if check_calculation(self.project_name, self.func):
                print("Iteration %d for user: %s, args: %s" % (iterations, self.user_name, self.args))
                D = self.func(D, **self.args)
                self.save_model_user(self.project_name, self.user_id, D)
                time.sleep(1)
                delta_time = int(time.time() - start)
            else:
                print("thread for project %s requested to stop" % self.project_name)
                break
            iterations += 1
        print("thread for project %s stopped" % self.project_name)
        cancel_calculation(self.project_name, self.func)

    def load_model_user(self, name, user_id, as_bunch=True, working_model=True):
        print("load_model_user:%s %s" % (name, user_id))
        db_session = scoped_session(sessionmaker(self.engine))
        proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        model = None
        if proj is None:
            print("no project found: %s" % name)
        else:
            if proj.working_project is None or not working_model:
                print("no working model")
                model = proj.model
            else:
                print("getting working model")
                model = proj.working_project.model
            if as_bunch:
                model = Bunch.fromDict(model)
        db_session.remove()
        return model

    def save_model_user(self, name, user_id, model, working_model=True):
        print("save_model_user:%s %s" % (name, user_id))
        db_session = scoped_session(sessionmaker(self.engine))

        proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        if isinstance(model, Bunch):
            model = model.toDict()
        if proj is not None:
            if not working_model:
                db_session.query(ProjectDb).update({"id": proj.id, "model": model})
            else:
                if proj.working_project is None:
                    db_session.add(WorkingProjectDb(project_id=proj.id, model = model, is_calibrating = True))
                else:
                    proj.working_project.model = model
                    db_session.add(proj.working_project)
            db_session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, name))
        db_session.remove()
