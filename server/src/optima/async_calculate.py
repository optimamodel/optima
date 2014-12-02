import threading
import sys
import time
from signal import *

from sqlalchemy.orm import sessionmaker, scoped_session
from sim.bunch import Bunch
from dbmodels import ProjectDb, WorkingProjectDb

# Sentinel object used for async calculation
sentinel = {
    'exit': False,  # This will stop all threads
    'projects': {}  # This will contain an entry per user project indicating if the calculating thread is running
}

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
    def __init__(self, engine, sentinel, user, project_name, timelimit, func, args):
        super(CalculatingThread, self).__init__()

        self.args = args
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name
        self.engine = engine
        self.func = func
        self.args = args
        self.timelimit = int(timelimit) # to be sure

        self.sentinel = sentinel
        if not self.project_name in self.sentinel['projects']:
            self.sentinel['projects'][project_name] = {}
        self.sentinel['projects'][project_name] = func.__name__
        print("starting calculating thread for user: %s project %s for %s seconds" % (self.user_name, self.project_name, self.timelimit))

    def run(self):
        D = self.load_model_user(self.project_name, self.user_id, working_model = False) #we start from the current model

        iterations = 1
        delta_time = 0
        start = time.time()
        while delta_time < self.timelimit:
            if not self.sentinel['exit'] and self.sentinel['projects'][self.project_name]:
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
        if self.sentinel['projects'][self.project_name]==self.func.__name__:
            self.sentinel['projects'][self.project_name] = False

    def load_model_user(self, name, user_id, as_bunch=True, working_model=True):
        print("load_model_user:%s %s" % (name, user_id))
        proj = ProjectDb.query.filter_by(user_id=user_id, name=name).first()
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
