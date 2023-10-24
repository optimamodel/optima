import os
#from flask_restful_swagger import swagger
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
import optima as op
from .dbconn import db, redis


#@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    username = db.Column(db.String(255))
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    country = db.Column(db.String(60))
    organization = db.Column(db.String(60))
    position = db.Column(db.String(60)) 
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='user', lazy='dynamic')
    
    def __init__(self, name, email, password, username, country, organization, 
        position, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.username = username
        self.country = country
        self.organization = organization
        self.position = position
        self.is_admin = is_admin

    def get_id(self):
        return self.id

    def is_active(self):  # pylint: disable=R0201
        return True

    def is_anonymous(self):  # pylint: disable=R0201
        return False

    def is_authenticated(self):  # pylint: disable=R0201
        return True


#@swagger.model
class PyObjectDb(db.Model):

    __tablename__ = 'objects'

    id = db.Column(
        UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default=None)
    attr = db.Column(JSON)

    def load(self):
        print(">> PyObjectDb.load " + self.id.hex)
        redis_entry = redis.get(self.id.hex)
        print(redis_entry)
        if redis_entry is None:
            print('WARNING, object %s not found' % self.id.hex) 
            return None
        else:
            return op.loadstr(redis_entry)

    def save_obj(self, obj):
        print(">> PyObjectDb.save " + self.id.hex)
        redis.set(self.id.hex, op.dumpstr(obj))

    def cleanup(self):
        print(">> PyObjectDb.cleanup " + self.id.hex)
        redis.delete(self.id.hex)
    
    def as_portfolio_file(self, loaddir, filename=None):
        portfolio = self.load()
        filename = os.path.join(loaddir, portfolio.name + ".prt")
        filename = op.saveobj(filename, portfolio)
        return filename

import pickle

#@swagger.model
class ProjectDb(db.Model):

    __tablename__ = 'projects'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    results = db.relationship('ResultsDb', backref='project')

    def __init__(self, user_id):
        self.user_id = user_id



    def load(self):
        import sciris as sc
        print(">> ProjectDb.load " + self.id.hex)
        redis_entry = redis.get(self.id.hex)
        # print('redis_entry', redis_entry)
        start = sc.tic()
        project = pickle.loads(redis_entry)
        project = op.loadproj(project, fromdb=True)
        # project = op.loadproj(redis_entry, fromdb=True)
        sc.toc(start=start)
        print('ASDHFI@(#$&')
        return project

    def save_obj(self, obj):
        print(">> ProjectDb.save " + self.id.hex)
        redis.set(self.id.hex, pickle.dumps(obj))

    def as_file(self, loaddir, filename=None):
        project = self.load()
        filename = os.path.join(loaddir, project.name + ".prj")
        op.saveobj(filename, project)
        return project.name + ".prj"

    def delete_dependent_objects(self, synchronize_session=False):
        str_project_id = str(self.id)        
        # Pull out all results rows with Project UID matching str_project_id.
        result_records = db.session.query(ResultsDb).filter_by(project_id=str_project_id)
        
        # Call the cleanup for each record (i.e., deleting the Redis entries).
        for result_record in result_records:
            result_record.cleanup()
            
        # Now delete the Postgres results entries.
        result_records.delete(synchronize_session)
        
        # Pull out all undo_stacks rows with Project UID matching str_project_id.
        undo_stack_records = db.session.query(UndoStackDb).filter_by(project_id=str_project_id)
        
        # Call the cleanup for each record (i.e., deleting the Redis entries).
        for undo_stack_record in undo_stack_records:
            undo_stack_record.cleanup()
            
        # Now delete the Postgres undo_stacks entries.
        undo_stack_records.delete(synchronize_session)
        
        db.session.flush()

    def recursive_delete(self, synchronize_session=False):
        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        self.delete_dependent_objects(synchronize_session=synchronize_session)
        # db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.flush()


class ResultsDb(db.Model):

    DEFAULT_CALCULATION_TYPE = 'calibration'  # 'calibration' or 'optimization'
    # todo make enum when all types are known

    __tablename__ = 'results'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id', ondelete='SET NULL'))
    calculation_type = db.Column(db.Text)

    def __init__(self, parset_id, project_id, calculation_type, id=None):
        self.parset_id = parset_id
        self.project_id = project_id
        self.calculation_type = calculation_type
        if id:
            self.id = id

    def load(self):
        print(">> ResultsDb.load result-" + self.id.hex)
        return op.loadstr(redis.get("result-" + self.id.hex))

    def save_obj(self, obj):
        print(">> ResultsDb.save result-" + self.id.hex)
        redis.set("result-" + self.id.hex, op.dumpstr(obj))

    def cleanup(self):
        print(">> ResultsDb.cleanup result-" + self.id.hex)
        redis.delete("result-" + self.id.hex)


class WorkLogDb(db.Model):  # pylint: disable=R0903
    __tablename__ = "work_log"
    work_status = db.Enum('started', 'completed', 'cancelled', 'error', 'blocked', name='work_status')
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    task_id = db.Column(db.String(128), default=None)
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)


class UndoStackDb(db.Model):

    __tablename__ = 'undo_stacks'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id', ondelete='SET NULL'))

    def __init__(self, project_id, id=None):
        self.project_id = project_id
        if id:
            self.id = id

    def load(self):
        print(">> UndoStackDb.load undo-stack-" + self.id.hex)
        return op.loadstr(redis.get("undo-stack-" + self.id.hex))

    def save_obj(self, obj):
        print(">> UndoStackDb.save undo-stack-" + self.id.hex)
        redis.set("undo-stack-" + self.id.hex, op.dumpstr(obj))

    def cleanup(self):
        print(">> UndoStackDb.cleanup undo-stack-" + self.id.hex)
        redis.delete("undo-stack-" + self.id.hex)