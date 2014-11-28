import threading
import sys
import time
from sim.autofit import autofit
from sqlalchemy.orm import sessionmaker, scoped_session

from sim.bunch import Bunch
from dbmodels import ProjectDb, WorkingProjectDb



class CalculatingThread(threading.Thread):
    def __init__(self, engine, sentinel, limit, user, project_name):
        super(CalculatingThread, self).__init__()

        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        self.session = Session()

        self.limit = limit
        self.sentinel = sentinel
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name
        if not self.project_name in self.sentinel['projects']:
            self.sentinel['projects'][project_name] = {}
        self.sentinel['projects'][project_name] = True
        print("starting thread for user: %s" % self.user_name)

    def run(self):
        #just a demo that it can
        D = self.load_model_user(self.project_name, self.user_id)

        for i in range(self.limit):
            if not self.sentinel['exit'] and self.sentinel['projects'][self.project_name]:
                print("i=%s" %i)
                print("user: %s" % self.user_name)
                args = {'timelimit':5, 'startyear':2000,'endyear':2015}
                D = autofit(D, **args)
                self.save_model_user(self.project_name, self.user_id, D)
                time.sleep(1)
            else:
                print("stopping requested")
                sys.exit()
        print("thread stopped")
        self.sentinel['projects'][self.project_name] = False
        sys.exit()


    def load_model_user(self, name, user_id, as_bunch = True, working_model = True):
        print("load_model_user:%s %s" % (name, user_id))
        proj = ProjectDb.query.filter_by(user_id=user_id, name=name).first()
        model = None
        if proj is None:
            print("no project found: %s" % name)
        else:
            if proj.working_project is None or working_model == False:
                print("no working model")
                model = proj.model
            else:
                print("getting working model")
                model = proj.working_project.model
            if as_bunch:
                model = Bunch.fromDict(model)
        return model


    def save_model_user(self, name, user_id, model, working_model = True):
        print("save_model_user:%s %s" % (name, user_id))
        proj = ProjectDb.query.filter_by(user_id=user_id, name=name).first()
        if isinstance(model, Bunch):
            model = model.toDict()
        if proj is not None:
            if not working_model:
                proj.model = model
                self.session.add(proj)
            else:
                if proj.working_project is None:
                    working_project = WorkingProjectDb(proj.id, model=model, is_calibrating=True)
                else:
                    proj.working_project.model = model
                    working_project = proj.working_project
                self.session.add(working_project)
            self.session.commit()
        else:
            print("no such model: user %s project %s" % (user_id, name))
