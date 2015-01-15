import threading
import sys
import time
from signal import *

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sim.bunch import Bunch, unbunchify
from dbmodels import ProjectDb, WorkingProjectDb

# Sentinel object used for async calculation
sentinel = {
    'exit': False  # This will stop all threads
}

def start_or_report_calculation(user_id, project, func, db_session): #only called from the application
    work_type = func.__name__
    can_start = False
    can_join = False

    project = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
    if project is not None:
        if project.working_project is None:
            db_session.add(WorkingProjectDb(project_id=project.id, model = project.model, is_working = True, work_type = work_type))
            can_start = True
            can_join = True
            db_session.commit()
        else:
            # if work_type is None then is_working flag makes no sense
            if (not project.working_project.is_working) or (project.working_project.work_type is None):
                project.working_project.work_type = work_type
                project.working_project.is_working = True
                db_session.add(project.working_project)
                db_session.commit()
                can_start = True
                can_join = True
            else:
                can_join = work_type == project.working_project.work_type
                work_type = project.working_project.work_type
    else:
        print("No such project %s, cannot start calculation" % project)
    return can_start, can_join, work_type

def cancel_calculation(user_id, project, func, db_session):
    project = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
    if project is not None and project.working_project is not None:
        project.working_project.is_working = False
        project.working_project.work_type = None
        db_session.add(project.working_project)
        db_session.commit()

def check_calculation(user_id, project, func, db_session):
    is_working = not sentinel['exit']
    if is_working:
        project = db_session.query(ProjectDb).filter_by(user_id=user_id, name=project).first()
        is_working = project is not None \
        and project.working_project is not None \
        and project.working_project.is_working \
        and project.working_project.work_type == func.__name__
    else:
        db_session.query(WorkingProjectDb).update({'is_working':False,'work_type':None})
        db_session.commit()
    return is_working

def interrupt(*args):
    global sentinel
    print("stopping all threads")
    sentinel['exit'] = True
    sys.exit()

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, interrupt)


class CalculatingThread(threading.Thread):
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

    def __init__(self, engine, user, project_name, timelimit, func, args):
        super(CalculatingThread, self).__init__()

        self.args = args
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name
        self.func = func
        self.debug_args = unbunchify(args)
        self.timelimit = int(timelimit) # to be sure
        self.db_session = scoped_session(sessionmaker(engine)) #creating scoped_session, eventually bound to engine
        print("starting calculating thread for user: %s project %s for %s seconds" % (self.user_name, self.project_name, self.timelimit))

    def run(self):
        D = self.load_model_user(self.db_session, self.project_name, self.user_id, working_model = False) #we start from the current model
        iterations = 1
        delta_time = 0
        start = time.time()
        while delta_time < self.timelimit:
            if check_calculation(self.user_id, self.project_name, self.func, self.db_session):
                print("Iteration %d for user: %s, args: %s" % (iterations, self.user_name, self.debug_args))
                D = self.func(D, **self.args)
                self.save_model_user(self.db_session, self.project_name, self.user_id, D)
                time.sleep(1)
                delta_time = int(time.time() - start)
            else:
                print("thread for project %s requested to stop" % self.project_name)
                break
            iterations += 1
        print("thread for project %s stopped" % self.project_name)
        cancel_calculation(self.user_id, self.project_name, self.func, self.db_session)
        self.db_session.connection().close() # this line might be redundant (not 100% sure - not clearly described)
        self.db_session.remove()
        self.db_session.bind.dispose() # black magic to actually close the connection by forcing the engine to dispose of garbage (I assume)

    def load_model_user(self, db_session, name, user_id, as_bunch=True, working_model=True):
        project = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        model = None
        if project is not None:
            if project.working_project is None or not working_model:
                print("no working model")
                model = project.model
            else:
                print("getting working model")
                model = project.working_project.model
            if as_bunch:
                model = Bunch.fromDict(model)
        return model

    def save_model_user(self, db_session, name, user_id, model, working_model=True):
        print("save_model_user:%s %s" % (name, user_id))

        project = db_session.query(ProjectDb).filter_by(user_id=user_id, name=name).first()
        if isinstance(model, Bunch):
            model = model.toDict()
        if project is not None:
            if not working_model:
                project.model = model
                db_session.add(project)
            else:
                if project.working_project is None:
                    db_session.add(WorkingProjectDb(project_id=project.id, model = model, is_working = True, work_type = self.func.__name__))
                else:
                    project.working_project.model = model
                    db_session.add(project.working_project)
            db_session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, name))
