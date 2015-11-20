from sqlalchemy.dialects.postgresql import JSON
from webapp.dbconn import db
from sqlalchemy import text
from sqlalchemy.orm import deferred

class UserDb(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='users',
                                lazy='dynamic')

    def __init__(self, name, email, password, is_admin = False):
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def get_id(self):
        return self.id

    def is_active(self): # pylint: disable=R0201
        return True

    def is_anonymous(self): # pylint: disable=R0201
        return False

    def is_authenticated(self): # pylint: disable=R0201
        return True


class ProjectDb(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    datastart = db.Column(db.Integer)
    dataend = db.Column(db.Integer)
    programs = db.Column(JSON)
    populations = db.Column(JSON)
    model = deferred(db.Column(JSON, server_default=text("'{}'")))
    working_project = db.relationship('WorkingProjectDb', backref='projects',
                                uselist=False)
    project_data = db.relationship('ProjectDataDb', backref='projects',
                                uselist=False)
    creation_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated_time = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def __init__(self, name, user_id, datastart, dataend, programs, populations, model = None, creation_time = None): # pylint: disable=R0913
        self.name = name
        self.user_id = user_id
        self.datastart = datastart
        self.dataend = dataend
        self.programs = programs
        self.populations = populations
        self.model = model if model else {}
        self.creation_time = creation_time

    def has_data(self):
        result = False
        if self.model is not None: #project can have data even if spreadsheet was not uploaded
            result = 'data' in self.model and 'programs' in self.model
        return result

    def has_model_parameters(self):
        result = False
        if self.model is not None:
            result = 'M' in self.model
        return result

    def data_upload_time(self):
        return self.project_data.upload_time if self.project_data else None



class WorkingProjectDb(db.Model): # pylint: disable=R0903
    __tablename__ = 'working_projects'
    id = db.Column(db.Integer,db.ForeignKey('projects.id'), primary_key=True )
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    model = deferred(db.Column(JSON))
    work_log_id = db.Column(db.Integer, default = None)

    def __init__(self, project_id, is_working=False, model = None, work_type = None, work_log_id = None): # pylint: disable=R0913
        self.id = project_id
        self.model = model if model else {}
        self.is_working = is_working
        self.work_type = work_type
        self.work_log_id = work_log_id

class WorkLogDb(db.Model): # pylint: disable=R0903
    __tablename__ = "work_log"

    work_status = db.Enum('started', 'completed', 'cancelled', 'error' , name='work_status')

    id = db.Column(db.Integer, primary_key=True)
    work_type = db.Column(db.String(32), default = None)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), index = True)
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default = None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default = None)

    def __init__(self, project_id, work_type = None):
        self.project_id = project_id
        self.work_type = work_type

class ProjectDataDb(db.Model): # pylint: disable=R0903
    __tablename__ = 'project_data'
    id = db.Column(db.Integer,db.ForeignKey('projects.id'), primary_key=True )
    meta = deferred(db.Column(db.LargeBinary))
    upload_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, upload_time = None):
        self.id = project_id
        self.meta = meta
        self.upload_time = upload_time
