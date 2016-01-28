from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.inputs import SubParser, Json as JsonInput
from server.webapp.fields import Json, Uuid
from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import load_project, load_progset, RequestParser, report_exception
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser

from server.webapp.dbconn import db

from server.webapp.dbmodels import ProgsetsDb, ProgramsDb


costcov_parser = RequestParser()
costcov_parser.add_arguments({
    'year': {'required': True, 'location': 'json'},
    'spending': {'required': True, 'type': float, 'location': 'json', 'dest': 'cost'},
    'coverage': {'required': True, 'type': float, 'location': 'json', 'dest': 'cov'},
})

program_parser = RequestParser()
program_parser.add_arguments({
    'name': {'required': True, 'location': 'json'},
    'short': {'location': 'json'},
    'short_name': {'location': 'json'},
    'category': {'required': True, 'location': 'json'},
    'active': {'type': bool, 'default': False, 'location': 'json'},
    'parameters': {'type': list, 'dest': 'pars', 'location': 'json'},
    'populations': {'type': list, 'location': 'json', 'dest': 'targetpops'},
    'addData': {'type': SubParser(costcov_parser), 'dest': 'costcov', 'action': 'append', 'default': []},
})


progset_parser = RequestParser()
progset_parser.add_arguments({
    'name': {'required': True},
    'programs': {'required': True, 'type': SubParser(program_parser), 'action': 'append'}
})


class Progsets(Resource):
    """
    Progsets for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Download progsets for the project with the given id.',
        notes="""
            if project exists, returns progsets for it
            if project does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields, envelope='progsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ProgsetsDb).filter_by(project_id=project_entry.id).all()
        for progset in reply:
            progset.get_targetpartypes()
        return reply

    @swagger.operation(
        description='Create a progset for the project with the given id.',
        parameters=progset_parser.swagger_parameters()
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def post(self, project_id):
        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        args = progset_parser.parse_args()

        progset_entry = ProgsetsDb(project_id, args['name'])
        db.session.add(progset_entry)
        db.session.flush()

        progset_entry.create_programs_from_list(args['programs'])

        db.session.commit()

        progset_entry.get_targetpartypes()

        return progset_entry, 201


class Progset(Resource):
    """
    An individual progset.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Download progset with the given id.',
        notes="""
            if progset exists, returns it
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def get(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = load_progset(project_id, progset_id)

        progset_entry.get_targetpartypes()

        return progset_entry

    @swagger.operation(
        description='Update progset with the given id.',
        notes="""
            if progset exists, returns the updated version
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def put(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))

        progset_entry = load_progset(project_id, progset_id)
        args = progset_parser.parse_args()
        progset_entry.name = args['name']
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()

        progset_entry.create_programs_from_list(args.get('programs', []))

        db.session.commit()

        progset_entry.get_targetpartypes()

        return progset_entry

    @swagger.operation(
        description='Delete progset with the given id.',
        notes="""
            if progset exists, deletes it
            if progset does not exist, returns an error.
        """
    )
    def delete(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = db.session.query(ProgsetsDb).get(progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        if progset_entry.project_id != project_id:
            raise ProgsetDoesNotExist(id=progset_id)

        progset_entry.name
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()
        db.session.delete(progset_entry)
        db.session.commit()
        return '', 204


class ProgsetData(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/x-gzip',
        description='Download progset with the given id as Binary.',
        notes="""
            if progset exists, returns it
            if progset does not exist, returns an error.
        """,

    )
    def get(self, project_id, progset_id):
        current_app.logger.debug("GET /api/project/{}/progsets/{}/data".format(project_id, progset_id))
        progset_entry = load_progset(project_id, progset_id)

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = progset_entry.as_file(loaddir)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created progset',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @marshal_with(file_resource)
    def post(self, project_id, progset_id, parset_id):
        """
        Uploads Data file, uses it to update the progrset and program models.
        Precondition: model should exist.
        """
        from server.webapp.programs import get_default_programs

        current_app.logger.debug("POST /api/project/{}/progsets/{}/data".format(project_id, progset_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

        progset_entry = load_progset(project_id, progset_id)

        project_entry = load_project(project_id)
        project = project_entry.hydrate()
        if project.data != {}:
            program_list = get_default_programs(project)
        else:
            program_list = []

        from optima.utils import loadobj
        new_progset = loadobj(uploaded_file)
        progset_entry.restore(new_progset, program_list)
        db.session.add(progset_entry)

        db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Progset %s is updated' % progset_entry.name,
        }
        return reply

param_fields = {
        'name': fields.String,
        'populations': Json,
        'coverage': fields.Boolean,
    }


class ProgsetParams(Resource):

    @swagger.operation(
        description='Get param/populations sets for the selected progset'
    )
    @marshal_with(param_fields)
    def get(self, project_id, progset_id, parset_id):
        from server.webapp.utils import load_progset, load_parset

        progset_entry = load_progset(project_id, progset_id)
        progset_be = progset_entry.hydrate()

        parset_entry = load_parset(project_id, parset_id)
        parset_be = parset_entry.hydrate()

        param_names = set([p['param'] for p in progset_be.targetpars])
        params = [{
            'name': name,
            'populations': [{
                'pop': pop,
                'programs': [program.name for program in progs]
            } for pop, progs in progset_be.progs_by_targetpar(name).iteritems()],
            'coverage': parset_be.pars[0][name].coverage,
            'proginteract': parset_be.pars[0][name].proginteract
        } for name in param_names]

        return params


program_effect_parser = RequestParser()
program_effect_parser.add_arguments({
    'name': {'required': False, 'location': 'json'},
    'intercept_lower': {'required': False, 'type': float, 'location': 'json'},
    'intercept_upper': {'required': False, 'type': float, 'location': 'json'},
})


param_year_effect_parser = RequestParser()
param_year_effect_parser.add_arguments({
    'year': {'required': False, 'location': 'json'},
    'intercept_lower': {'required': False, 'type': float, 'location': 'json'},
    'intercept_upper': {'required': False, 'type': float, 'location': 'json'},
    'interact': {'location': 'json', 'required': False},
    'programs': {
        'type': SubParser(program_effect_parser),
        'action': 'append',
        'default': [],
        'location': 'json',
        'required': False,
    },
})


param_effect_parser = RequestParser()
param_effect_parser.add_arguments({
    'name': {'required': False, 'location': 'json'},
    'pop': {'required': False, 'location': 'json', 'type': JsonInput},
    'years': {
        'type': SubParser(param_year_effect_parser),
        'action': 'append',
        'default': [],
        'location': 'json',
        'required': False,
    },
})


parset_effect_parser = RequestParser()
parset_effect_parser.add_arguments({
    'parset': {'required': True, 'location': 'json'},
    'parameters': {
        'type': SubParser(param_effect_parser),
        'action': 'append',
        'type': JsonInput,
        'default': [],
        'location': 'json',
        'required': False
    }
})


effect_parser = RequestParser()
effect_parser.add_argument('effects', type=SubParser(parset_effect_parser), action='append')


program_effect_fields = {
    'name': fields.String,
    'intercept_lower': fields.Float,
    'intercept_upper': fields.Float
}


param_year_effect_fields = {
    'year': fields.Integer,
    'intercept_lower': fields.Float,
    'intercept_upper': fields.Float,
    'interact': fields.List(fields.String),
    'programs': fields.List(fields.Nested(program_effect_fields), default=[])
}

param_effect_fields = {
    'name': fields.String,
    'pop': fields.Raw,
    'years': fields.List(fields.Nested(param_year_effect_fields), default=[])
}

parset_effect_fields = {
    'parset': Uuid,
    'parameters': fields.List(fields.Nested(param_effect_fields), default=[])
}

progset_effects_fields = {
    'effects': fields.List(fields.Nested(parset_effect_fields), default=[])
}


class ProgsetEffects(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Get List of Progset effects  for the selected progset'
    )
    @marshal_with(progset_effects_fields)
    def get(self, project_id, progset_id):
        from server.webapp.utils import load_progset

        progset_entry = load_progset(project_id, progset_id)
        return progset_entry

    @swagger.operation(
        description='Get List of Progset effects  for the selected progset',
        parameters=effect_parser.swagger_parameters()
    )
    @marshal_with(progset_effects_fields)
    def put(self, project_id, progset_id):
        from server.webapp.utils import load_progset

        progset_entry = load_progset(project_id, progset_id)

        args = effect_parser.parse_args()
        # raise Exception(args)
        progset_entry.effects = args.get('effects', [])

        db.session.commit()

        return progset_entry
