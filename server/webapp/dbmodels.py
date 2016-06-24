from datetime import datetime
from pprint import pprint

import dateutil
from flask_restful import fields, marshal
from flask_restful_swagger import swagger
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON, UUID, ARRAY
from sqlalchemy.orm import deferred

import optima as op
from optima import saves
from server.webapp.dbconn import db, redis
from server.webapp.exceptions import DuplicateProgram
from server.webapp.exceptions import ParsetDoesNotExist
from server.webapp.parse import (
    parse_program_summary, revert_targetpars, revert_ccopars, revert_costcovdata,
    parse_default_program_summaries, parse_outcomes_from_progset, put_outcomes_into_progset, convert_pars_list,
    convert_program_list)
from server.webapp.utils import normalize_obj
from server import serialise


def log_var(name, obj):
    current_app.logger.debug("%s = \n%s\n" % (name, pprint.pformat(obj, indent=2)))



def db_model_as_file(model, loaddir, filename, name_field, extension):
    import os
    from optima.utils import saveobj

    be_object = model.hydrate()
    if filename is None:
        filename = '{}.{}'.format(getattr(model, name_field), extension)
    server_filename = os.path.join(loaddir, filename)

    saveobj(server_filename, be_object)

    return filename


@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

    resource_fields = {
        'id': fields.String,
        'displayName': fields.String(attribute='name'),
        'username': fields.String,
        'email': fields.String,
        'is_admin': fields.Boolean,
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    username = db.Column(db.String(255))
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='user', lazy='dynamic')

    def __init__(self, name, email, password, username, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.username = username
        self.is_admin = is_admin

    def get_id(self):
        return self.id

    def is_active(self):  # pylint: disable=R0201
        return True

    def is_anonymous(self):  # pylint: disable=R0201
        return False

    def is_authenticated(self):  # pylint: disable=R0201
        return True


@swagger.model
class ProjectDb(db.Model):

    __tablename__ = 'projects'

    resource_fields = {
        'id': fields.String,
        'user_id': fields.String,
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    results = db.relationship('ResultsDb', backref='project')

    _loaded = None

    def __init__(self, user_id):
        self.user_id = user_id
        self._loaded = None

    def load(self):
        return serialise.loads(redis.get(self.id.hex))

    def save_obj(self, obj):
        redis.set(self.id.hex, serialise.dumps(obj))
        print("Saved " + self.id.hex)

    def as_file(self, loaddir, filename=None):
        return redis.get(self.id.hex)


class ResultsDb(db.Model):

    CALIBRATION_TYPE = 'calibration'  # 'calibration' or 'optimization'
    # todo make enum when all types are known

    __tablename__ = 'results'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True))
    # When deleting a parset we only delete results of type CALIBRATION
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id', ondelete='SET NULL'))
    calculation_type = db.Column(db.Text)
    blob = db.Column(db.LargeBinary)

    def __init__(self, parset_id, project_id, calculation_type, blob, id=None):
        self.parset_id = parset_id
        self.project_id = project_id
        self.calculation_type = calculation_type
        self.blob = blob
        if id:
            self.id = id

    def hydrate(self):
        result = op.loads(self.blob)
        print ">>>>>>> Hydrate result(%s) '%s'" % (self.calculation_type, result.name)
        return result


class WorkingProjectDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'working_projects'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    parset_id = db.Column(UUID(True)) # not sure if we should make it foreign key here
    work_log_id = db.Column(UUID(True), default=None)

    def __init__(self, project_id, parset_id, is_working=False, work_type=None, work_log_id=None):  # pylint: disable=R0913
        self.id = project_id
        self.parset_id = parset_id
        self.is_working = is_working
        self.work_type = work_type
        self.work_log_id = work_log_id

    def load(self):
        return serialise.loads(redis.get("working-" + self.id.hex))

    def save_obj(self, obj):
        redis.set("working-" + self.id.hex, serialise.dumps(obj))
        print("Saved working-" + self.id.hex)


class WorkLogDb(db.Model):  # pylint: disable=R0903

    __tablename__ = "work_log"

    work_status = db.Enum('started', 'completed', 'cancelled', 'error', name='work_status')

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    work_type = db.Column(db.String(32), default=None)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    parset_id = db.Column(UUID(True))
    result_id = db.Column(UUID(True), default=None)
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)

    def __init__(self, project_id, parset_id, work_type=None):
        self.project_id = project_id
        self.parset_id = parset_id
        self.work_type = work_type


class ProjectEconDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'project_econ'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated
