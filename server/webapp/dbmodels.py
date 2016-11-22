import os
from flask_restful_swagger import swagger
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import deferred
from sqlalchemy.dialects.postgresql import JSON

import optima

from .dbconn import db, redis


@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

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
class PyObjectDb(db.Model):

    __tablename__ = 'objects'

    id = db.Column(
        UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    type = db.Column(db.Text, default=None)
    name = db.Column(db.Text, default=None)
    attr = db.Column(JSON)

    def load(self):
        print(">> Load pyobject " + self.id.hex)
        redis_entry = redis.get(self.id.hex)
        return optima.dataio.loads(redis_entry)

    def save_obj(self, obj):
        print(">> Save pyobject " + self.id.hex)
        redis.set(self.id.hex, optima.dataio.dumps(obj))

    def cleanup(self):
        print(">> Cleanup " + self.id.hex)
        redis.delete(self.id.hex)


@swagger.model
class ProjectDb(db.Model):

    __tablename__ = 'projects'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    results = db.relationship('ResultsDb', backref='project')

    def __init__(self, user_id):
        self.user_id = user_id

    def load(self):
        print(">> Load project " + self.id.hex)
        redis_entry = redis.get(self.id.hex)
        project = optima.dataio.loads(redis_entry)
        if isinstance(project, optima.Project):
            for progset in project.progsets.values():
                if not hasattr(progset, 'inactive_programs'):
                    progset.inactive_programs = optima.odict()
        return project

    def save_obj(self, obj, is_skip_result=False):
        print(">> Save project " + self.id.hex)
        if isinstance(obj, optima.Project):
            # Copy the project, only save what we want...
            new_project = optima.dcp(obj)
            new_project.spreadsheet = None
            if is_skip_result:
                new_project.results = optima.odict()
            redis.set(self.id.hex, optima.dataio.dumps(new_project))
        else:
            redis.set(self.id.hex, optima.dataio.dumps(obj))
        print("Saved " + self.id.hex)

    def as_file(self, loaddir, filename=None):
        project = self.load()
        filename = os.path.join(loaddir, project.name + ".prj")
        optima.saveobj(filename, project)
        return project.name + ".prj"

    def delete_dependent_objects(self, synchronize_session=False):
        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        work_logs = db.session.query(WorkLogDb).filter_by(project_id=str_project_id)
        for work_log in work_logs:
            work_log.cleanup()
        work_logs.delete(synchronize_session)
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectEconDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.flush()

    def recursive_delete(self, synchronize_session=False):
        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        self.delete_dependent_objects(synchronize_session=synchronize_session)
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.flush()


class ProjectDataDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'project_data'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated


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
        return optima.dataio.loads(redis.get("result-" + self.id.hex))

    def save_obj(self, obj):
        print(">> Save result-" + self.id.hex)
        redis.set("result-" + self.id.hex, optima.dataio.dumps(obj))

    def cleanup(self):
        print(">> Cleanup result-" + self.id.hex)
        redis.delete("result-" + self.id.hex)


class WorkLogDb(db.Model):  # pylint: disable=R0903

    __tablename__ = "work_log"

    work_status = db.Enum('started', 'completed', 'cancelled', 'error', 'blocked', name='work_status')

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    work_type = db.Column(db.String(128), default=None)
    task_id = db.Column(db.String(128), default=None)
    project_id = db.Column(UUID(True))
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)

    def __init__(self, project_id, work_type=None):
        self.project_id = project_id
        self.work_type = work_type

    def load(self):
        print(">> Load working-" + self.id.hex)
        return optima.dataio.loads(redis.get("working-" + self.id.hex))

    def save_obj(self, obj):
        print(">> Save working-" + self.id.hex)
        redis.set("working-" + self.id.hex, optima.dataio.dumps(obj))

    def cleanup(self):
        print(">> Cleanup working-" + self.id.hex)
        redis.delete("working-" + self.id.hex)


