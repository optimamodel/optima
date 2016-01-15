from datetime import datetime
import dateutil
from collections import defaultdict

from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import JSON, UUID, ARRAY
from sqlalchemy import text
from sqlalchemy.orm import deferred

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, Json

import optima as op


@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

    resource_fields = {
        'id': Uuid,
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
        'id': Uuid,
        'name': fields.String,
        'user_id': Uuid,
        'dataStart': fields.Integer(attribute='datastart'),
        'dataEnd': fields.Integer(attribute='dataend'),
        'populations': Json,
        'creation_time': fields.DateTime(attribute='created'),
        'updated_time': fields.DateTime(attribute='updated'),
        'data_upload_time': fields.DateTime,
        'has_data': fields.Boolean(attribute='has_data_now'),
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
        return self.data is not None and len(self.data)

    def has_model_parameters(self):
        return self.parsets is not None

    @property
    def data_upload_time(self):
        return self.project_data.updated if self.project_data else None

    def hydrate(self):
        project_entry = op.Project()
        project_entry.uid = self.id
        project_entry.name = self.name
        project_entry.created = (
            self.created or datetime.now(dateutil.tz.tzutc())
        )
        project_entry.modified = self.updated
        if self.data:
            project_entry.data = op.loads(self.data)
        if self.settings:
            project_entry.settings = op.loads(self.settings)
        if self.parsets:
            for parset_record in self.parsets:
                parset_entry = parset_record.hydrate()
                project_entry.addparset(parset_entry.name, parset_entry)
        if self.progsets:
            for progset_record in self.progsets:
                progset_entry = progset_record.hydrate()
                project_entry.addprogset(progset_entry.name, progset_entry)
        return project_entry

    def as_file(self, loaddir, filename=None):
        import os
        from optima.utils import save

        be_project = self.hydrate()
        if filename is None:
            filename = '{}.prj'.format(self.name)
        server_filename = os.path.join(loaddir, filename)

        save(server_filename, be_project)

        return filename

    def restore(self, project):

        # Attention: this method adds only dependent objects to the session
        from datetime import datetime
        import dateutil

        same_project = str(project.uid) == str(self.id)
        str_project_id = str(self.id)
        print "same_project:", same_project, project.uid, self.id
        db.session.query(ProgramsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProgsetsDb).filter_by(project_id=str_project_id).delete()
        if same_project:
            self.name = project.name
        else:
            db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete()
            db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete()
        db.session.flush()

        self.created = project.created
        self.updated = project.modified or datetime.now(dateutil.tz.tzutc())
        self.settings = op.saves(project.settings)
        self.data = op.saves(project.data)

        if project.data:
            self.datastart = int(project.data['years'][0])
            self.dataend = int(project.data['years'][-1])
            self.populations = []
            project_pops = project.data['pops']
            for i in range(len(project_pops['short'])):
                new_pop = {
                    'name': project_pops['long'][i], 'short_name': project_pops['short'][i],
                    'female': project_pops['female'][i], 'male': project_pops['male'][i],
                    'age_from': int(project_pops['age'][i][0]), 'age_to': int(project_pops['age'][i][1])
                }
                self.populations.append(new_pop)
        else:
            self.datastart = self.datastart or op.default_datastart
            self.dataend = self.dataend or op.default_dataend
            self.populations = self.populations or {}
        if project.parsets:
            from server.webapp.utils import update_or_create_parset
            for name, parset in project.parsets.iteritems():
                if not same_project:
                    parset.uid = op.uuid()  # so that we don't get same parset in two different projects
                update_or_create_parset(self.id, name, parset)

        # Expects that progsets or programs should not be deleted from restoring a project
        # This is the same behaviour as with parsets.
        if project.progsets:
            from server.webapp.utils import update_or_create_progset, update_or_create_program
            from server.webapp.programs import get_default_programs

            if project.data != {}:
                program_list = get_default_programs(project)
            else:
                program_list = []

            for name, progset in project.progsets.iteritems():
                progset_record = update_or_create_progset(self.id, name, progset)

                # only active programs are hydrated
                # therefore we need to retrieve the default list of programs
                loaded_programs = set()
                for program in program_list:
                    program_name = program['name']
                    if program_name in progset.programs:
                        loaded_programs.add(program_name)
                        program = progset.programs[program_name].__dict__
                        program['parameters'] = program.get('targetpars', [])
                        active = True
                    else:
                        active = False

                    update_or_create_program(self.id, progset_record.id, program_name, program, active)

                # In case programs from prj are not in the defaults
                for program_name, program in progset.programs.iteritems():
                    if program_name not in loaded_programs:
                        program = program.__dict__
                        program['parameters'] = program.get('targetpars', [])
                        update_or_create_program(self.id, progset_record.id, program_name, program, True)

    def recursive_delete(self, synchronize_session=False):

        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        db.session.query(WorkLogDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(WorkingProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProgramsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProgsetsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.flush()


class ParsetsDb(db.Model):

    __tablename__ = 'parsets'

    resource_fields = {
        'id': Uuid(attribute='uid'),
        'project_id': Uuid,
        'name': fields.String,
        'created': fields.DateTime,
        'updated': fields.DateTime,
        'pars': Json,
    }

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
        parset_entry = op.Parameterset()
        parset_entry.name = self.name
        parset_entry.uid = self.id
        parset_entry.created = self.created
        parset_entry.modified = self.updated
        if self.pars:
            parset_entry.pars = op.loads(self.pars)
        return parset_entry


class ResultsDb(db.Model):

    CALIBRATION_TYPE = 'calibration'  # todo make enum when all types are known

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

    def hydrate(self):
        return op.loads(self.blob)


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
        'short_name': fields.String(attribute='short'),
        'name': fields.String,
        'parameters': fields.Raw(attribute='pars'),
        'active': fields.Boolean,
        'populations': fields.List(fields.String, attribute='targetpops'),
        'criteria': fields.Raw(),
        'created': fields.DateTime,
        'updated': fields.DateTime,
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    category = db.Column(db.String)
    name = db.Column(db.String)
    short = db.Column('short_name', db.String)
    pars = db.Column(JSON)
    active = db.Column(db.Boolean)
    targetpops = db.Column(ARRAY(db.String), default=[])
    criteria = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def __init__(self, project_id, progset_id, name, short='',
                 category='No category', active=False, pars=None, created=None,
                 updated=None, id=None, targetpops=[], criteria=None):

        self.project_id = project_id
        self.progset_id = progset_id
        self.name = name
        self.short = short if short is not None else name
        self.category = category
        self.pars = pars
        self.active = active
        self.targetpops = targetpops
        self.criteria = criteria
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id

    def pars_to_program_pars(self):
        """From API Program to BE Program"""

        if self.pars is None:
            return []

        parameters = []

        for param in self.pars:
            if param.get('active', False):
                parameters.extend([{
                    'param': param['param'],
                    'pop': pop if type(pop) in (str, unicode) else tuple(pop)
                } for pop in param['pops']])

        return parameters

    @classmethod
    def program_pars_to_pars(cls, targetpars):
        """From BE Program to API Program"""

        parameters = defaultdict(list)
        for parameter in targetpars:
            parameters[parameter['param']].append(parameter['pop'])

        pars = [{
                'active': True,
                'param': short_name,
                'pops': pop,
                } for short_name, pop in parameters.iteritems()]

        return pars

    def hydrate(self):
        program_entry = op.Program(
            self.short,
            targetpars=self.pars_to_program_pars(),
            name=self.name,
            category=self.category,
            targetpops=self.targetpops,
            criteria=self.criteria
        )
        program_entry.id = self.id
        return program_entry


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
        # In BE, programs don't have an "active" flag
        # therefore only hydrating active programs
        progset_entry = op.Programset(
            name=self.name,
            programs=[
                program.hydrate()
                for program in self.programs if program.active
            ]
        )

        return progset_entry

    def create_programs_from_list(self, programs):
        for program in programs:
            kwargs = {}
            for field in ['name', 'short', 'category', 'targetpops', 'pars']:
                kwargs[field] = program[field]

            program_entry = ProgramsDb(
                self.project_id,
                self.id,
                active=program.get('active', False),
                **kwargs
            )
            db.session.add(program_entry)

    def recursive_delete(self, synchronize_session=False):
        db.session.query(ProgramsDb).filter_by(progset_id=str(self.id)).delete(synchronize_session)
        db.session.query(ProgsetsDb).filter_by(id=str(self.id)).delete(synchronize_session)
        db.session.flush()
