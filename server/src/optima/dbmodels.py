from sqlalchemy.dialects.postgresql import JSON
from dbconn import db

class UserDb(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    projects = db.relationship('ProjectDb', backref='users',
                                lazy='dynamic')

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


from datetime import datetime
from sqlalchemy import text

class ProjectDb(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    datastart = db.Column(db.Integer)
    dataend = db.Column(db.Integer)
    econ_dataend = db.Column(db.Integer)
    programs = db.Column(JSON)
    populations = db.Column(JSON)
    model = db.Column(JSON, server_default=text("'{}'"))
    working_project = db.relationship('WorkingProjectDb', backref='projects',
                                uselist=False)
    creation_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    data_upload_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, name, user_id, datastart, dataend, \
        econ_dataend, programs, populations, model = {}, creation_time = None, data_upload_time = None):
        the_now = datetime.utcnow()
        self.name = name
        self.user_id = user_id
        self.datastart = datastart
        self.dataend = dataend
        self.econ_dataend = econ_dataend
        self.programs = programs
        self.populations = populations
        self.model = model
        self.creation_time = creation_time
        self.data_upload_time = data_upload_time

class WorkingProjectDb(db.Model):
    __tablename__ = 'working_projects'
    id = db.Column(db.Integer,db.ForeignKey('projects.id'), primary_key=True )
    is_calibrating = db.Column(db.Boolean, unique=False, default=False)
    model = db.Column(JSON)

    def __init__(self, project_id, is_calibrating=False, model = {}):
        self.id = project_id
        self.model = model
        self.is_calibrating = is_calibrating
