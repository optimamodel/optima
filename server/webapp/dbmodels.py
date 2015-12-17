from datetime import datetime
import dateutil

from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy import text
from sqlalchemy.orm import deferred

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, Json


@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

    resource_fields = {
        'id': Uuid,
        'name': fields.String,
        'email': fields.String,
        'is_admin': fields.Boolean,
    }

    id = db.Column(UUID(True), server_default = text("uuid_generate_v1mc()"), primary_key = True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='user', lazy='dynamic')

    def __init__(self, name, email, password, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
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
        'id': Uuid,
        'name': fields.String,
        'user_id': Uuid,
        'dataStart': fields.Integer(attribute='datastart'),
        'dataEnd': fields.Integer(attribute='dataend'),
        'populations': Json,
        'creation_time': fields.DateTime(attribute='created'),
        'updated_time': fields.DateTime(attribute='updated'),
        'data_upload_time': fields.DateTime,
        'has_data': fields.Boolean,
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    datastart = db.Column(db.Integer)
    dataend = db.Column(db.Integer)
    populations = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    version = db.Column(db.Text)
    settings = db.Column(db.LargeBinary)
    data = db.Column(db.LargeBinary)
    working_project = db.relationship('WorkingProjectDb', backref='related_project', uselist=False)
    project_data = db.relationship('ProjectDataDb', backref='project', uselist=False)
    parsets = db.relationship('ParsetsDb', backref='project')
    results = db.relationship('ResultsDb', backref='project')
    progsets = db.relationship('ProgsetsDb', backref='project')

    def __init__(self, name, user_id, datastart, dataend, populations, version,
            created=None, updated=None, settings=None, data=None, parsets=None,
            results=None):
        self.name = name
        self.user_id = user_id
        self.datastart = datastart
        self.dataend = dataend
        self.populations = populations
        if created is not None:
            self.created = created
        if updated is not None:
            self.updated = updated
        self.version = version
        self.settings = settings
        self.data = data
        self.parsets = parsets or []
        self.results = results or []

    def has_data(self):
        return self.data is not None

    def has_model_parameters(self):
        return self.parsets is not None

    @property
    def data_upload_time(self):
        return self.project_data.updated if self.project_data else None

    def hydrate(self):
        from optima.project import Project
        from optima.utils import loads
        project_entry = Project()
        project_entry.uuid = self.id
        project_entry.name = self.name
        project_entry.created = (
            self.created or datetime.now(dateutil.tz.tzutc())
        )
        project_entry.modified = self.updated
        if self.data:
            project_entry.data = loads(self.data)
        if self.settings:
            project_entry.settings = loads(self.settings)
        if self.parsets:
            for parset_record in self.parsets:
                parset_entry = parset_record.hydrate()
                project_entry.addparset(parset_entry.name, parset_entry)
        return project_entry

    def restore(self, project):

        from datetime import datetime
        import dateutil
        from optima.utils import saves

        self.name = project.name
        self.created = project.created
        self.updated = datetime.now(dateutil.tz.tzutc())
        self.settings = saves(project.settings)
        self.data = saves(project.data)
        if project.parsets:
            from server.webapp.utils import update_or_create_parset
            for name, parset in project.parsets.iteritems():
                update_or_create_parset(self.id, name, parset)

    def recursive_delete(self):

        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        db.session.query(WorkLogDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete()
        db.session.query(WorkingProjectDb).filter_by(id=str_project_id).delete()
        db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProgramsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProgsetsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete()


class ParsetsDb(db.Model):

    __tablename__ = 'parsets'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    pars = db.Column(db.LargeBinary)

    def __init__(self, project_id, name, created=None, updated=None, pars=None, id=None):
        self.project_id = project_id
        self.name = name
        if created:
            self.created = created
        if updated:
            self.updated = updated
        self.pars = pars
        if id:
            self.id = id

    def hydrate(self):
        from optima.parameters import Parameterset
        from optima.utils import loads
        parset_entry = Parameterset()
        parset_entry.name = self.name
        parset_entry.uuid = self.id
        parset_entry.created = self.created
        parset_entry.modified = self.updated
        parset_entry.pars = loads(self.pars)
        return parset_entry


class ResultsDb(db.Model):

    __tablename__ = 'results'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    calculation_type = db.Column(db.Text)
    blob = db.Column(db.LargeBinary)

    def __init__(self, parset_id, project_id, calculation_type, blob, id=None):
        self.parset_id = parset_id
        self.project_id = project_id
        self.calculation_type = calculation_type
        self.blob = blob
        if id:
            self.id = id


class WorkingProjectDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'working_projects'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    project = db.Column(db.LargeBinary)
    work_log_id = db.Column(UUID(True), default=None)

    def __init__(self, project_id, is_working=False, project=None, work_type=None, work_log_id=None):  # pylint: disable=R0913
        self.id = project_id
        self.project = project
        self.is_working = is_working
        self.work_type = work_type
        self.work_log_id = work_log_id


class WorkLogDb(db.Model):  # pylint: disable=R0903

    __tablename__ = "work_log"

    work_status = db.Enum('started', 'completed', 'cancelled', 'error', name='work_status')

    id = db.Column(UUID(True), primary_key=True)
    work_type = db.Column(db.String(32), default=None)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)

    def __init__(self, project_id, work_type=None):
        self.project_id = project_id
        self.work_type = work_type


class ProjectDataDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'project_data'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated


@swagger.model
class ProgramsDb(db.Model):

    __tablename__ = 'programs'

    resource_fields = {
        'id': Uuid,
        'progset_id': Uuid,
        'project_id': Uuid,
        'category': fields.String,
        'name': fields.String,
        'parameters': fields.Raw(attribute='pars'),
        'active': fields.Boolean,
        'created': fields.DateTime,
        'updated': fields.DateTime,
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    category = db.Column(db.String)
    name = db.Column(db.String)
    short_name = db.Column(db.String)
    pars = db.Column(JSON)
    active = db.Column(db.Boolean)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def __init__(self, project_id, progset_id, name, short_name, category, active=False, pars=None, created=None, updated=None, id=None):

        self.project_id = project_id
        self.progset_id = progset_id
        self.name = name
        self.short_name = short_name
        self.category = category
        self.pars = pars
        self.active = active
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id


@swagger.model
class ProgsetsDb(db.Model):

    resource_fields = {
        'id': Uuid,
        'project_id': Uuid,
        'name': fields.String,
        'created': fields.DateTime,
        'updated': fields.DateTime,
        'programs': fields.Nested(ProgramsDb.resource_fields)
    }

    __tablename__ = 'progsets'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    programs = db.relationship('ProgramsDb', backref='progset', lazy='joined')

    def __init__(self, project_id, name, created=None, updated=None, id=None):
        self.project_id = project_id
        self.name = name
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id

    def hydrate(self):
        from optima.programs import Programset
        progset_entry = Programset(
            name=self.name,
            programs=None
        )

        return progset_entry

    def create_programs_from_list(self, programs):
        for program in programs:
            kwargs = {}
            for field in ['name', 'short_name', 'category']:
                kwargs[field] = program[field]

            program_entry = ProgramsDb(
                self.project_id,
                self.id,
                active=program.get('active', False),
                pars=program.get('parameters', None),
                **kwargs
            )
            db.session.add(program_entry)
