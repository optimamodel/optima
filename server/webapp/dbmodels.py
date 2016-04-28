from datetime import datetime
import dateutil
from collections import defaultdict
from copy import deepcopy
from pprint import pprint

from flask_restful_swagger import swagger
from flask_restful import fields
from server.webapp.fields import Json
from server.webapp.exceptions import DuplicateProgram

from sqlalchemy.dialects.postgresql import JSON, UUID, ARRAY
from sqlalchemy import text
from sqlalchemy.orm import deferred

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, Json, LargeInt
from server.webapp.exceptions import ParsetDoesNotExist
from server.webapp.jsonhelper import OptimaJSONEncoder, normalize_obj

from werkzeug.utils import secure_filename
import optima as op


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
        'has_econ': fields.Boolean,
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
    has_econ = db.Column(db.Boolean)
    blob = db.Column(db.LargeBinary)
    working_project = db.relationship('WorkingProjectDb', backref='related_project', uselist=False)
    project_data = db.relationship('ProjectDataDb', backref='project', uselist=False)
    project_econ = db.relationship('ProjectEconDb', backref='project', uselist=False)
    parsets = db.relationship('ParsetsDb', backref='project')
    results = db.relationship('ResultsDb', backref='project')
    progsets = db.relationship('ProgsetsDb', backref='project')
    scenarios = db.relationship('ScenariosDb', backref='project')
    optimizations = db.relationship('OptimizationsDb', backref='project')

    def __init__(self, name, user_id, datastart, dataend, populations, version,
                 created=None, updated=None, settings=None, data=None, has_econ=False, parsets=None,
                 results=None, scenarios=None, optimizations=None):
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
        self.has_econ = has_econ
        self.parsets = parsets or []
        self.results = results or []
        self.scenarios = scenarios or []
        self.optimizations = optimizations or []
        self.blob = None

    def has_data(self):
        return self.data is not None and len(self.data)

    def has_model_parameters(self):
        return self.parsets is not None

    @property
    def data_upload_time(self):
        return self.project_data.updated if self.project_data else None

    def hydrate(self):
        # the problem here: if a record gets created outside of project, we have a big problem.
        # (which is currently the case for progsets)
        # TODO: make it possible to uncomment the two lines of code below :)
#        if self.blob and len(self.blob):
#            project_entry = op.loads(self.blob)
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
            for key, parset in project_entry.parsets.iteritems():
                parset.project = project_entry
                project_entry.parsets[key] = parset
        if self.progsets:
            for progset_record in self.progsets:
                progset_entry = progset_record.hydrate()
                project_entry.addprogset(progset_entry.name, progset_entry)
        if self.scenarios:
            for scenario_record in self.scenarios:
                if scenario_record.active:
                    scenario_entry = scenario_record.hydrate()
                    project_entry.addscen(scenario_entry.name, scenario_entry)
        if self.optimizations:
            for optimization_record in self.optimizations:
                optimization_record._ensure_current(self)
                parset_name = None
                progset_name = None
                if optimization_record.parset_id:
                    parset_name = [parset.name for parset in self.parsets if parset.id == optimization_record.parset_id]
                    if parset_name:
                        parset_name = parset_name[0]
                if optimization_record.progset_id:
                    progset_name = [progset.name for progset in self.progsets if progset.id == optimization_record.progset_id]
                    if progset_name:
                        progset_name = progset_name[0]
                optim = op.Optim(project_entry, name=optimization_record.name,
                    objectives=optimization_record.objectives,
                    constraints=optimization_record.constraints, parsetname=parset_name, progsetname=progset_name)
                project_entry.addoptim(optim)
        if self.results:
            for result_entry in self.results:
                result = result_entry.hydrate()
                project_entry.addresult(result)
                if result_entry.parset_id and result_entry.calculation_type == ResultsDb.CALIBRATION_TYPE:
                    for parset in project_entry.parsets.values():
                        if parset.uid == result_entry.parset_id:
                            parset.resultsref = result.uid
        return project_entry

    def as_file(self, loaddir, filename=None):
        return db_model_as_file(self, loaddir, filename, 'name', 'prj')

    def restore(self, project):

        # Attention: this method adds only dependent objects to the session
        from datetime import datetime
        import dateutil
        import pytz

        is_same_project = str(project.uid) == str(self.id)
        str_project_id = str(self.id)
        db.session.query(ProgramsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProgsetsDb).filter_by(project_id=str_project_id).delete()
        if is_same_project:
            self.name = project.name
        else:
            db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete()
            db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete()
        db.session.flush()

        # BE projects are not always TZ aware
        project.uid = self.id
        self.blob = op.saves(project)
        self.created = pytz.utc.localize(project.created) if project.created.tzinfo is None else project.created
        if project.modified:
            self.updated = pytz.utc.localize(project.modified) if project.modified.tzinfo is None else project.modified
        else:
            self.updated = datetime.now(dateutil.tz.tzutc())
        self.settings = op.saves(project.settings)

        # self.data is a pickled blob, maybe should be called data_blob
        self.data = op.saves(project.data)

        if project.data:
            self.has_econ = 'econ' in project.data
            self.datastart = int(project.data['years'][0])
            self.dataend = int(project.data['years'][-1])

            print(">>>> Gather populations in project")
            self.populations = []
            project_pops = normalize_obj(project.data['pops'])
            # pprint(project_pops)
            for i in range(len(project_pops['short'])):
                new_pop = {
                    'name': project_pops['long'][i],
                    'short_name': project_pops['short'][i],
                    'female': project_pops['female'][i],
                    'male': project_pops['male'][i],
                    'age_from': int(project_pops['age'][i][0]),
                    'age_to': int(project_pops['age'][i][1])
                }
                self.populations.append(new_pop)
        else:
            self.has_econ = False
            self.datastart = self.datastart or op.default_datastart
            self.dataend = self.dataend or op.default_dataend
            self.populations = self.populations or {}
        if project.parsets:
            from server.webapp.utils import update_or_create_parset_record
            for name, parset in project.parsets.iteritems():
                if not is_same_project:
                    parset.uid = op.uuid()  # so that we don't get same parset in two different projects
                update_or_create_parset_record(self.id, name, parset)

        # Expects that progsets or programs should not be deleted from restoring a project
        # This is the same behaviour as with parsets.
        if project.progsets:
            from server.webapp.utils import update_or_create_progset_record
            from server.webapp.programs import get_default_program_summaries

            program_summaries = get_default_program_summaries(project)

            for name, progset in project.progsets.iteritems():
                progset_record = update_or_create_progset_record(self.id, name, progset)
                progset_record.restore(progset, program_summaries)


        if project.scens:
            from server.webapp.utils import update_or_create_scenario_record
            for name in project.scens:
                update_or_create_scenario_record(self.id, project, name)

        if project.optims:
            from server.webapp.utils import update_or_create_optimization_record
            for name in project.optims:
                update_or_create_optimization_record(self.id, project, name)

        if project.results:
            # only save optimization ones for now...
            from server.webapp.utils import save_result
            for name in project.results:
                if name.startswith('optim-') and isinstance(project.results[name], op.Multiresultset):  # bold assumption...
                    result = project.results[name]
                    # print "simpars", result.simpars[0], type(result.simpars[0])
                    result_entry = save_result(self.id, result,
                        project.parsets[0].name, # TODO : will break if more than one parset
                        'optimization')
                    db.session.add(result_entry)
                    db.session.flush()

    def recursive_delete(self, synchronize_session=False):

        str_project_id = str(self.id)
        # delete all relevant entries explicitly
        db.session.query(OptimizationsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ScenariosDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(WorkLogDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectEconDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(WorkingProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProgramsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProgsetsDb).filter_by(project_id=str_project_id).delete(synchronize_session)
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete(synchronize_session)
        db.session.flush()

    def find_parset(self, parset_id):
        parset_entry = [item for item in self.parsets if item.id == parset_id]
        if parset_entry:
            parset_entry = parset_entry[0]
        else:
            raise ParsetDoesNotExist(parset_id, self.id)
        return parset_entry


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
        parset_instance = op.Parameterset()
        parset_instance.name = self.name
        parset_instance.uid = self.id
        parset_instance.created = self.created
        parset_instance.modified = self.updated
        if self.pars:
            parset_instance.pars = op.loads(self.pars)
        return parset_instance

    def as_file(self, loaddir, filename=None):
        return db_model_as_file(self, loaddir, filename, 'name', 'par')

    def restore(self, parset_instance):
        same_parset = (parset_instance.uid == self.id)
        if same_parset:
            self.name = parset_instance.name
        self.pars = op.saves(parset_instance.pars)


class ResultsDb(db.Model):

    CALIBRATION_TYPE = 'calibration'  # todo make enum when all types are known

    __tablename__ = 'results'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
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
        return op.loads(self.blob)


class WorkingProjectDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'working_projects'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    project = db.Column(db.LargeBinary)
    parset_id = db.Column(UUID(True)) # not sure if we should make it foreign key here
    work_log_id = db.Column(UUID(True), default=None)

    def __init__(self, project_id, parset_id, is_working=False, project=None, work_type=None, work_log_id=None):  # pylint: disable=R0913
        self.id = project_id
        self.parset_id = parset_id
        self.project = project
        self.is_working = is_working
        self.work_type = work_type
        self.work_log_id = work_log_id


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


class ProjectDataDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'project_data'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated

class ProjectEconDb(db.Model):  # pylint: disable=R0903

    __tablename__ = 'project_econ'

    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated


costcov_fields = {
    'year': fields.Integer,
    'spending': LargeInt(attribute='cost'),
    'coverage': LargeInt(attribute='coverage'),
}


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
        'addData': fields.Nested(costcov_fields, allow_null=True, attribute='costcov'),
        'optimizable': fields.Raw,
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
    costcov = db.Column(JSON)
    ccopars = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def __init__(self, project_id, progset_id, name, short='',
                 category='No category', active=False, pars=None, created=None,
                 updated=None, id=None, targetpops=[], criteria=None, costcov=None,
                 ccopars=None):

        self.project_id = project_id
        self.progset_id = progset_id
        self.name = name
        self.short = short if short is not None else name
        self.category = category
        self.pars = pars
        self.active = active
        self.targetpops = targetpops
        self.criteria = criteria
        self.costcov = costcov
        self.ccopars = ccopars
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id

    def fetch_program_targetpars(self):
        """From API Program to BE Program"""
        if self.pars is None:
            return []
        parameters = []
        for param in self.pars:
            if param.get('active', False):
                parameters.extend([
                    {
                        'param': param['param'],
                        'pop': pop if type(pop) in (str, unicode) else tuple(pop)
                    }
                    for pop in param['pops']
                ])
        return parameters

    def datapoint_api_to_db(self, pt):
        return {'cost': pt['spending'], 'year': pt['year'], 'coverage': pt['coverage']}

    def datapoint_db_to_api(self, pt):
        return {'spending': pt['cost'], 'year': pt['year'], 'coverage': pt['coverage']}

    def data_api_to_db(self, data):
        costcov_data = [self.datapoint_api_to_db(x) for x in data]
        return costcov_data

    def data_db_to_api(self):
        costcov_data = [self.datapoint_db_to_api(x) for x in (self.costcov or [])]
        return costcov_data

    def _conv_lg_num(self, num):
        return int(float(num))

    def hydrate(self):
        pluck = lambda l, k: [e[k] for e in l if e[k] is not None]
        costcovdata = {}
        if self.costcov is not None:
            costcovdata = {
                't': pluck(self.costcov, 'year'),
                'cost': pluck(self.costcov, 'cost'),
                'coverage': pluck(self.costcov, 'coverage'),
            }
        ccopars = None
        if self.ccopars:
            ccopars = {
                't': self.ccopars['t'],
                'saturation': map(tuple, self.ccopars['saturation']),
                'unitcost': map(tuple, self.ccopars['unitcost'])
            }
        program_instance = op.Program(
            self.short,
            targetpars=self.fetch_program_targetpars(),
            name=self.name,
            category=self.category,
            targetpops=self.targetpops,
            criteria=self.criteria,
            costcovdata=costcovdata,
            ccopars=ccopars,
        )
        program_instance.id = self.id
        return program_instance

    def pprint(self):
        pprint({
            'short': self.short,
            'name': self.name,
            'pars': self.pars,
            'category': self.category,
            'targetpops': self.targetpops,
            'criteria': self.criteria,
            'costcov': self.costcov,
            'ccopars': self.ccopars
        })

    def get_optimizable(self):
        be_program = self.hydrate()
        self.optimizable = be_program.optimizable()

    def restore(self, program):
        print(">>>>> Restore program '%s'" % program.short)
        from server.webapp.programs import parse_targetpars, parse_costcovdata
        self.category = program.category
        self.name = program.name
        self.short = program.short
        self.pars = parse_targetpars(program.targetpars)
        self.targetpops = normalize_obj(program.targetpops)
        self.criteria = program.criteria
        self.costcov = parse_costcovdata(program.costcovdata)
        self.ccopars = normalize_obj(program.costcovfn.ccopars)
        self.pprint()


@swagger.model
class ProgsetsDb(db.Model):

    resource_fields = {
        'id': Uuid,
        'project_id': Uuid,
        'name': fields.String,
        'created': fields.DateTime,
        'updated': fields.DateTime,
        'programs': fields.Nested(ProgramsDb.resource_fields),
        'targetpartypes': fields.Raw,
        'readytooptimize': fields.Boolean
    }

    __tablename__ = 'progsets'

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    programs = db.relationship('ProgramsDb', backref='progset', lazy='joined')
    effects = db.Column(JSON)

    def __init__(self, project_id, name, created=None, updated=None, id=None, effects=[]):
        self.project_id = project_id
        self.name = name
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id
        self.targetpartypes = []
        self.effects = effects

    def hydrate(self):
        # In BE, programs don't have an "active" flag
        # therefore only hydrating active programs
        progset = op.Programset(
            name=self.name,
            programs=[
                program.hydrate()
                for program in self.programs
                if program.active
            ]
        )
        for parset_effect in self.effects:
            for program_effect in parset_effect['parameters']:
                for year in program_effect['years']:
                    effect = {
                        'intercept': (year['intercept_lower'], year['intercept_upper']),
                        't': int(year['year']),
                        'interact': year['interact'],
                    }

                    for row in year["programs"]:
                        if row['intercept_lower'] is not None and row['intercept_upper'] is not None:
                            effect[row['name']] = (row['intercept_lower'], row['intercept_upper'])
                        else:
                            effect[row['name']] = None

                    if program_effect['name'] not in progset.covout:
                        continue

                    islist = isinstance(program_effect['pop'], list)
                    poptuple = tuple(program_effect['pop']) if islist else program_effect['pop']
                    covout = progset.covout[program_effect['name']]
                    if poptuple in covout:
                        covout[poptuple].addccopar(effect, overwrite=True)

        return progset

    def get_extra_data(self):
        be_progset = self.hydrate()
        be_progset.gettargetpartypes()
        self.targetpartypes = be_progset.targetpartypes
        self.readytooptimize = be_progset.readytooptimize()

    def restore(self, progset, default_program_summaries):
        from server.webapp.utils import update_or_create_program_record
        from server.webapp.programs import parse_program

        print(">>>>>>>> Restore progset_record '%s'" % progset.name)
        self.name = progset.name

        # store programs including default programs that are not progset
        loaded_shorts = set()
        for program_summary in default_program_summaries:
            short = unicode(program_summary['short'])
            if short in progset.programs:
                loaded_shorts.add(short)
                program = progset.programs[short]
                loaded_program_summary = parse_program(program)
                for replace_key in ['ccopars', 'costcov', 'targetpops', 'parameters']:
                    if replace_key in loaded_program_summary:
                        program_summary[replace_key] = loaded_program_summary[replace_key]
                active = True
            else:
                active = False
            desc = "default active" if active else "default inactive"
            print '>>>> Parse %s program "%s" - "%s"' % (desc, short, program_summary['name'])
            update_or_create_program_record(self.project.id, self.id, short, program_summary, active)

        # save programs that are not in defaults
        for short, program in progset.programs.iteritems():
            if short not in loaded_shorts:
                print '>>>> Parse custom active "%s" - "%s"' % (short, program_summary['name'])
                program_summary = parse_program(program)
                update_or_create_program_record(self.project.id, self.id, short, program_summary, True)

        effects = []
        for targetpartype in progset.targetpartypes:
            for thispop in progset.progs_by_targetpar(targetpartype).keys():
                item = {
                    'name': targetpartype,
                    'pop': thispop,
                    'years': [
                        {
                            'intercept_upper': progset.covout[targetpartype][thispop].ccopars['intercept'][i][1],
                            'intercept_lower': progset.covout[targetpartype][thispop].ccopars['intercept'][i][0],
                            'interact': progset.covout[targetpartype][thispop].ccopars['interact'][i] if 'interact' in progset.covout[targetpartype][thispop].ccopars.keys() else 'random',
                            'programs': [
                                {
                                    'name': k,
                                    'intercept_lower': v[i][0] if len(v) > i else None,
                                    'intercept_upper': v[i][1] if len(v) > i else None,
                                }
                                for k, v in progset.covout[targetpartype][thispop].ccopars.iteritems()
                                if k not in ['intercept', 't', 'interact']
                            ],
                            'year': progset.covout[targetpartype][thispop].ccopars['t'][i]
                        } for i in range(len(progset.covout[targetpartype][thispop].ccopars['t']))
                    ]
                }
                effects.append(item)
        print('##### Restore effects')
        print(effects)
        parset = ParsetsDb.query.filter_by(project_id=str(self.project.id)).first()
        self.effects = [
            {
                'parset': str(parset.id) if parset else None,
                'parameters': effects
            }
        ]
        db.session.commit()

    def recreate_programs_from_list(self, programs, progset_id):
        prog_shorts = []
        desired_shorts = set([program.get('short_name', program.get('short', '')) for program in programs])
        print "desired_shorts", desired_shorts
        existing_programs = db.session.query(ProgramsDb).filter_by(progset_id=progset_id)

        existing_shorts = {}
        for program in existing_programs:
            if program.short not in desired_shorts:
                db.session.delete(program)
            else:
                existing_shorts[program.short]=program
        db.session.flush()


        for program in programs:
            # Kind of a hack but sometimes we receive short ans sometimes short_name
            short = program.get('short_name', program.get('short', ''))
            if short in existing_shorts:
                print "Updating program %s" % short
                program_entry = existing_shorts[short]
                for field in ['name', 'category', 'targetpops', 'pars', 'costcov', 'criteria']:
                    setattr(program_entry, field, program[field])
                program_entry.active = program.get('active', False)
                db.session.add(program_entry)
            else:
                print "Creating new program %s" % short
                kwargs = {}
                for field in ['name', 'category', 'targetpops', 'pars', 'costcov', 'criteria']:
                    kwargs[field] = program[field]

                kwargs['short'] = short
                if not 'pregnant' in kwargs['criteria']:
                    kwargs['criteria']['pregnant'] = False

                if kwargs['short'] in prog_shorts:
                    raise DuplicateProgram(kwargs['short'])
                else:
                    prog_shorts.append(kwargs['short'])

                program_entry = ProgramsDb(
                    self.project_id,
                    self.id,
                    active=program.get('active', False),
                    **kwargs
                )

                program_instance = program_entry.hydrate()
                program_entry.restore(program_instance)
                db.session.add(program_entry)

    def recursive_delete(self, synchronize_session=False):
        db.session.query(ProgramsDb).filter_by(progset_id=str(self.id)).delete(synchronize_session)
        db.session.query(ProgsetsDb).filter_by(id=str(self.id)).delete(synchronize_session)
        db.session.flush()

    def as_file(self, loaddir, filename=None):
        return db_model_as_file(self, loaddir, filename, 'name', 'prg')


@swagger.model
class ScenariosDb(db.Model):

    __tablename__ = 'scenarios'

    resource_fields = {
        'id': Uuid,
        'progset_id': Uuid,
        'scenario_type': fields.String,
        'active': fields.Boolean,
        'name': fields.String,
        'parset_id': Uuid,
        'pars': Json(attribute='pars'),
        'budget': Json(attribute='budget'),
        'coverage': Json(attribute='coverage'),
        'years': Json(attribute='years')
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    scenario_type = db.Column(db.String)
    active = db.Column(db.Boolean)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    blob = db.Column(JSON)

    def __init__(self, project_id, parset_id, name, scenario_type,
                 active=False, progset_id=None, blob={}):

        self.project_id = project_id
        self.name = name
        self.scenario_type = scenario_type
        self.active = active
        self.progset_id = progset_id
        self.parset_id = parset_id
        self.blob = blob

    @property
    def pars(self):
        # print(self.blob)
        return self.blob.get('pars', [])

    @property
    def budget(self):
        return self.blob.get('budget', [])

    @property
    def coverage(self):
        return self.blob.get('coverage', [])

    @property
    def years(self):
        return self.blob.get('years', [])

    def hydrate(self):

        from server.webapp.utils import load_progset_record, load_parset_record

        parset = load_parset_record(self.project_id, self.parset_id)

        progset = None

        if self.progset_id:
            progset = load_progset_record(self.project_id, self.progset_id)

        blob = deepcopy(self.blob)

        key = self.scenario_type
        if key == 'parameter':
            if 'pars' in blob and blob['pars']:
                blob['pars'] = [
                    {
                        'name': item['name'],
                        'startyear': item['startyear'],
                        'endval': item['endval'],
                        'endyear': item['endyear'],
                        'startval': item['startval'],
                        'for': [
                            tuple([str(i) for i in for_item]) if isinstance(for_item, list) else str(for_item)
                            for for_item in item['for']
                        ]
                    } for item in blob['pars'] if 'pars' in blob
                ]
            else:
                blob['pars'] = []
        else:
            print(blob)
            blob[key] = {
                str(k): v
                for k, v in blob[key].iteritems() if key in blob
            }

        if self.scenario_type == "budget":

            blob.pop('coverage', None)
            blob.pop('pars', None)

            # TODO: remove this hack (dummy values)
            if 'years' not in blob:
                blob['t'] = 2030
            else:
                blob['t'] = blob['years']
                del blob['years']
            print "blob", blob
            return op.Budgetscen(name=self.name,
                               parsetname=parset.name,
                               progsetname=progset.name,
                               **blob)

        if self.scenario_type == "coverage":

            blob.pop('budget', None)
            blob.pop('pars', None)

            # TODO: remove this hack (dummy values)
            if 'years' not in blob:
                blob['t'] = 2030
            else:
                blob['t'] = blob['years']
                del blob['years']
            return op.Coveragescen(name=self.name,
                               parsetname=parset.name,
                               progsetname=progset.name,
                               **blob)

        elif self.scenario_type == "parameter":

            blob.pop('coverage', None)
            blob.pop('budget', None)

            return op.Parscen(name=self.name,
                              parsetname=parset.name,
                              **blob)



@swagger.model
class OptimizationsDb(db.Model):

    __tablename__ = 'optimizations'

    resource_fields = {
        'id': Uuid,
        'which': fields.String,
        'name': fields.String,
        'parset_id': Uuid,
        'progset_id': Uuid,
        'objectives': Json(),
        'constraints': Json()
    }

    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    which = db.Column(db.String)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    objectives = db.Column(JSON)
    constraints = db.Column(JSON)

    def __init__(self, project_id, parset_id, progset_id, name, which,
                 objectives={}, constraints={}):

        self.project_id = project_id
        self.name = name
        self.which = which
        self.progset_id = progset_id
        self.parset_id = parset_id
        self.objectives = objectives
        self.constraints = constraints

        self._ensure_current()

    def _ensure_current(self, project=None):
        """
        Make sure the objectives and constraints are current.
        """
        from server.webapp.utils import load_parset_record, load_progset_record, load_project_record, remove_nans

        if not self.constraints:
            self.constraints = {}

        if not self.objectives:
            self.objectives = {}

        if project is None:
            project = load_project_record(self.project_id).hydrate()
        progset = load_progset_record(self.project_id, self.progset_id).hydrate()
        parset = load_parset_record(self.project_id, self.parset_id).hydrate()

        constraints = op.defaultconstraints(project=project, progset=progset)

        # Update the min and the max according to what the user put, do not
        # update the names, that should change from the programs.
        constraints['max'].update({
            x:y for x,y in self.constraints.get('min', {}).items() if x in constraints})
        constraints['min'].update({
            x:y for x,y in self.constraints.get('max', {}).items() if x in constraints})


        self.constraints = constraints

        objectives = op.defaultobjectives(project=project, progset=progset,
                                          which=self.which)

        objectives.update({
            x:y for x,y in self.objectives.items() if x not in ['keys', 'keylabels']})

        self.objectives = remove_nans(objectives)
