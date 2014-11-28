import threading
import sys
import time

from sim.autofit import autofit
from sqlalchemy.orm import sessionmaker, scoped_session
from sim.bunch import Bunch
from dbmodels import ProjectDb, WorkingProjectDb


class CalculatingThread(threading.Thread):
    def __init__(self, engine, sentinel, user, project_name, args):
        super(CalculatingThread, self).__init__()

        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        self.session = Session()

        self.args = args
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name

        self.sentinel = sentinel
        if not self.project_name in self.sentinel['projects']:
            self.sentinel['projects'][project_name] = {}
        self.sentinel['projects'][project_name] = True
        print("starting thread for user: %s" % self.user_name)

    def run(self):
        D = self.load_model_user(self.project_name, self.user_id)

        iterations = 1
        delta_time = 0
        start = time.time()
        while delta_time < self.args['timelimit']:
            if not self.sentinel['exit'] and self.sentinel['projects'][self.project_name]:
                print("Iteration %d for user: %s, args: %s" % (iterations, self.user_name, self.args))
                autofitargs = {'timelimit': 10, 'startyear': self.args['startyear'], 'endyear': self.args['endyear']}
                D = autofit(D, **autofitargs)
                self.save_model_user(self.project_name, self.user_id, D)
                time.sleep(1)
                delta_time = int(time.time() - start)
            else:
                print("stopping requested")
                sys.exit()
            iterations += 1
        print("thread stopped")
        self.sentinel['projects'][self.project_name] = False
        sys.exit()

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
        proj = ProjectDb.query.filter_by(user_id=user_id, name=name).first()
        if isinstance(model, Bunch):
            model = model.toDict()
        if proj is not None:
            if not working_model:
                self.session.query(ProjectDb).update({"id": proj.id, "model": model})
            else:
                if proj.working_project is None:
                    self.session.query(WorkingProjectDb).insert({"id": proj.id, "model": model, "is_calibrating": True})
                else:
                    self.session.query(WorkingProjectDb).update({"id": proj.id, "model": model, "is_calibrating": True})
            self.session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, name))
