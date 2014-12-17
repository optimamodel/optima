import threading
import sys
import time
from signal import *

from sqlalchemy.orm import sessionmaker, scoped_session
from sim.bunch import Bunch
from dbmodels import ProjectDb, WorkingProjectDb

# Sentinel object used for async calculation
sentinel = {
    'exit': False  # This will stop all threads
}

def start_or_report_calculation(user_id, project, func, engine): #only called from the application
    work_type = func.__name__
    can_start = False
    can_join = False

    db_session = scoped_session(sessionmaker(engine))
    proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
    model = None
    if proj is not None:
        if proj.working_project is None:
            db_session.add(WorkingProjectDb(project_id=proj.id, model = proj.model, is_working = True, work_type = work_type))
            can_start = True
            can_join = True
            db_session.commit()
        else:
            # if work_type is None then is_working flag makes no sense
            if (not proj.working_project.is_working) or (proj.working_project.work_type is None):
                proj.working_project.work_type = work_type
                proj.working_project.is_working = True
                db_session.add(proj.working_project)
                db_session.commit()
                can_start = True
                can_join = True
            else:
                can_join = work_type == proj.working_project.work_type
                work_type = proj.working_project.work_type
    else:
        print("No such project %s, cannot start calculation" % project)
    db_session.close()    
    return can_start, can_join, work_type

def cancel_calculation(user_id, project, func, engine):
    db_session = scoped_session(sessionmaker(engine))
    proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
    if proj is not None and proj.working_project is not None:
        proj.working_project.is_working = False
        proj.working_project.work_type = None
        db_session.add(proj.working_project)
        db_session.commit()
    db_session.close()
 
def check_calculation(user_id, project, func, engine):
    is_working = not sentinel['exit']
    db_session = scoped_session(sessionmaker(engine))
    if is_working:
        proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
        is_working = proj is not None \
        and proj.working_project is not None \
        and proj.working_project.is_working \
        and proj.working_project.work_type == func.__name__
    else:
        db_session.query(WorkingProjectDb).update({'is_working':False,'work_type':None})
        db_session.commit()
    db_session.close()
    return is_working

def interrupt(*args):
    global sentinel
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
        self.timelimit = int(timelimit) # to be sure
        print("starting calculating thread for user: %s project %s for %s seconds" % (self.user_name, self.project_name, self.timelimit))

    def run(self):
        D = self.load_model_user(self.project_name, self.user_id, working_model = False) #we start from the current model
        iterations = 1
        delta_time = 0
        start = time.time()
        while delta_time < self.timelimit:
            if check_calculation(self.user_id, self.project_name, self.func, self.engine):
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
        cancel_calculation(self.user_id, self.project_name, self.func, self.engine)

    def load_model_user(self, name, user_id, as_bunch=True, working_model=True):
        db_session = scoped_session(sessionmaker(self.engine))
        proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        model = None
        if proj is not None:
            if proj.working_project is None or not working_model:
                print("no working model")
                model = proj.model
            else:
                print("getting working model")
                model = proj.working_project.model
            if as_bunch:
                model = Bunch.fromDict(model)
        db_session.close()
        return model

    def save_model_user(self, name, user_id, model, working_model=True):
        print("save_model_user:%s %s" % (name, user_id))
        db_session = scoped_session(sessionmaker(self.engine))

        proj = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        if isinstance(model, Bunch):
            model = model.toDict()
        if proj is not None:
            if not working_model:
                proj.model = model
                db_session.add(proj)
            else:
                if proj.working_project is None:
                    db_session.add(WorkingProjectDb(project_id=proj.id, model = model, is_working = True, work_type = self.func.__name__))
                else:
                    proj.working_project.model = model
                    db_session.add(proj.working_project)
            db_session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, name))
        db_session.close()
