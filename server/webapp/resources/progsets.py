import mpld3
import json
from pprint import pprint
import pprint
import math

from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.dataio import (
    load_project_record, load_progset_record, load_project, load_program, load_parset,
    update_or_create_program_record)
from server.webapp.exceptions import (
    ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist, ParsetDoesNotExist)
from server.webapp.resources.common import file_resource, file_upload_form_parser, report_exception
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ParsetsDb, ResultsDb
from server.webapp.jsonhelper import normalize_obj
from server.webapp.inputs import SubParser, Json, RequestParser, TEMPLATEDIR, upload_dir_user

import uuid
from flask_restful import fields

costcov_parser = RequestParser()
costcov_parser.add_arguments({
    'year': {'required': True, 'type':int, 'location': 'json'},
    'cost': {'required': True, 'type': float, 'location': 'json', 'dest': 'cost'},
    'coverage': {'required': True, 'type': float, 'location': 'json', 'dest': 'coverage'},
})


program_parser = RequestParser()
program_parser.add_arguments({
    'name': {'required': True, 'location': 'json'},
    'short': {'location': 'json'},
    'category': {'required': True, 'location': 'json'},
    'active': {'type': bool, 'default': False, 'location': 'json'},
    'targetpars': {'type': list, 'dest': 'pars', 'location': 'json'},
    'populations': {'type': list, 'location': 'json', 'dest': 'targetpops'},
    'costcov': {'type': SubParser(costcov_parser), 'dest': 'costcov', 'action': 'append', 'default': []},
    'criteria': {'type': Json, 'location': 'json'}
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
        project_record = load_project_record(project_id)
        if project_record is None:
            raise ProjectDoesNotExist(id=project_id)

        progsets_record = db.session.query(ProgsetsDb).filter_by(project_id=project_record.id).all()
        for progset_record in progsets_record:
            progset_record.get_extra_data()
            for program_record in progset_record.programs:
                program_record.get_optimizable()

        return progsets_record

    @swagger.operation(
        description='Create a progset for the project with the given id.',
        parameters=progset_parser.swagger_parameters()
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def post(self, project_id):
        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project_record(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        args = progset_parser.parse_args()

        progset_entry = ProgsetsDb(project_id, args['name'])
        db.session.add(progset_entry)
        db.session.flush()

        progset_entry.recreate_programs_from_list(args['programs'], progset_entry.id)

        db.session.commit()

        progset_entry.get_extra_data()

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
        progset_entry = load_progset_record(project_id, progset_id)

        progset_entry.get_extra_data()

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

        progset_entry = load_progset_record(project_id, progset_id)
        args = progset_parser.parse_args()
        progset_entry.name = args['name']
        progset_entry.recreate_programs_from_list(args.get('programs', []), progset_id)

        db.session.commit()

        progset_entry.get_extra_data()

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
        progset_entry = load_progset_record(project_id, progset_id)

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
    def post(self, project_id, progset_id):
        """
        Uploads Data file, uses it to update the progrset and program models.
        Precondition: model should exist.
        """
        from server.webapp.parse import get_default_program_summaries

        current_app.logger.debug("POST /api/project/{}/progsets/{}/data".format(project_id, progset_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

        progset_entry = load_progset_record(project_id, progset_id)

        project_entry = load_project_record(project_id)
        project = project_entry.hydrate()
        if project.data != {}:
            program_list = get_default_program_summaries(project)
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
    'populations': fields.Raw,
    'coverage': fields.Boolean,
}

class ProgsetParams(Resource):

    @swagger.operation(
        description='Get param/populations sets for the selected progset'
    )
    @marshal_with(param_fields)
    def get(self, project_id, progset_id, parset_id):
        from server.webapp.dataio import load_progset_record, load_parset_record

        progset_entry = load_progset_record(project_id, progset_id)
        progset_be = progset_entry.hydrate()

        parset_entry = load_parset_record(project_id, parset_id)
        parset_be = parset_entry.hydrate()

        param_names = set([p['param'] for p in progset_be.targetpars])
        params = [{
            'name': name,
            'populations': [{
                'pop': pop,
                'programs': [{
                    'name': program.name,
                    'short': program.short,
                } for program in progs]
            } for pop, progs in progset_be.progs_by_targetpar(name).iteritems()],
            'coverage': parset_be.pars[0][name].coverage,
            'proginteract': parset_be.pars[0][name].proginteract
        } for name in param_names]

        return params



# stack of resource fields for parsing

program_effect_fields = {
    'name': fields.String,
    'intercept_lower': fields.Float,
    'intercept_upper': fields.Float
}

param_year_effect_fields = {
    'year': fields.Integer,
    'intercept_lower': fields.Float,
    'intercept_upper': fields.Float,
    'interact': fields.String,
    'programs': fields.List(fields.Nested(program_effect_fields), default=[])
}

param_effect_fields = {
    'name': fields.String,
    'pop': fields.Raw,  # ToDo implement a field type that matches String or List of Strings
    'years': fields.List(fields.Nested(param_year_effect_fields), default=[])
}

parset_effect_fields = {
    'parset': fields.String,
    'parameters': fields.List(fields.Nested(param_effect_fields), default=[])
}

progset_effects_fields = {
    'effects': fields.List(fields.Nested(parset_effect_fields), default=[])
}

program_effect_parser = RequestParser()
program_effect_parser.add_arguments({
    'name': {'required': False, 'location': 'json'},
    'intercept_lower': {'required': False, 'type': float, 'location': 'json'},
    'intercept_upper': {'required': False, 'type': float, 'location': 'json'},
})

param_year_effect_parser = RequestParser()
param_year_effect_parser.add_arguments({
    'year': {'type': int, 'required': False, 'location': 'json'},
    'intercept_lower': {'required': False, 'type': float, 'location': 'json'},
    'intercept_upper': {'required': False, 'type': float, 'location': 'json'},
    'interact': {'location': 'json', 'required': False},
    'programs': {
        'type': SubParser(program_effect_parser),
        # 'action': 'append',
        'default': [],
        'location': 'json',
        'required': False,
    },
})

param_effect_parser = RequestParser()
param_effect_parser.add_arguments({
    'name': {'required': False, 'location': 'json'},
    'pop': {'required': False, 'location': 'json', 'type': Json},
    'years': {
        'type': SubParser(param_year_effect_parser),
        # 'action': 'append',
        'default': [],
        'location': 'json',
        'required': False,
    },
})

parset_effect_parser = RequestParser()
parset_effect_parser.add_arguments({
    'parset': {'required': False, 'location': 'json'},
    'parameters': {
        'type': SubParser(param_effect_parser),
        # 'action': 'append',
        'default': [],
        'location': 'json',
        'required': False
    }
})


effect_parser = RequestParser()
effect_parser.add_argument('effects', type=SubParser(parset_effect_parser), action='append')

class ProgsetEffects(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        summary='Get List of existing Progset effects for the selected progset'
    )
    @marshal_with(progset_effects_fields)
    def get(self, project_id, progset_id):
        from server.webapp.dataio import load_progset_record

        progset_entry = load_progset_record(project_id, progset_id)
        return progset_entry

    @swagger.operation(
        summary='Saves a list of Progset effects for the selected progset',
        parameters=effect_parser.swagger_parameters()
    )
    @marshal_with(progset_effects_fields)
    def put(self, project_id, progset_id):
        from server.webapp.dataio import load_progset_record

        progset_entry = load_progset_record(project_id, progset_id)

        args = effect_parser.parse_args()
        progset_entry.effects = args.get('effects', [])

        db.session.add(progset_entry)
        db.session.commit()

        return progset_entry



query_program_parser = RequestParser()
query_program_parser.add_arguments({
    'program': {'required': True, 'type': Json, 'location': 'json'},
})

class Program(Resource):
    """
    Write program to web-server (for cost-coverage and outcome changes)
    The payload is JSON in the form:

    'program': {
      'active': True,
      'category': 'Care and treatment',
      'ccopars': { 'saturation': [[0.9, 0.9]],
                   't': [2016],
                   'unitcost': [[1.136849845773715, 1.136849845773715]]},
      'costcov': [ { 'cost': 16616289, 'coverage': 8173260, 'year': 2012},
                   { 'cost': 234234, 'coverage': 324234, 'year': 2013}],
      'created': 'Mon, 02 May 2016 05:27:48 -0000',
      'criteria': { 'hivstatus': 'allstates', 'pregnant': False},
      'id': '9b5db736-1026-11e6-8ffc-f36c0fc28d89',
      'name': 'HIV testing and counseling',
      'optimizable': True,
      'populations': [ 'FSW',
                       'Clients',
                       'Male Children 0-14',
                       'Female Children 0-14',
                       'Males 15-49',
                       'Females 15-49',
                       'Males 50+',
                       'Females 50+'],
      'progset_id': '9b55945c-1026-11e6-8ffc-130aba4858d2',
      'project_id': '9b118ef6-1026-11e6-8ffc-571b10a45a1c',
      'short': 'HTC',
      'targetpars': [ { 'active': True,
                        'param': 'hivtest',
                        'pops': [ 'FSW',
                                  'Clients',
                                  'Male Children 0-14',
                                  'Female Children 0-14',
                                  'Males 15-49',
                                  'Females 15-49',
                                  'Males 50+',
                                  'Females 50+']}],
      'updated': 'Mon, 02 May 2016 06:22:29 -0000'
    }
    """

    method_decorators = [report_exception, login_required]
    def post(self, project_id, progset_id):
        current_app.logger.debug(
            "/api/project/%s/progsets/%s/program" % (project_id, progset_id))

        args = query_program_parser.parse_args()
        program_summary = normalize_obj(args['program'])
        program_record = update_or_create_program_record(
            project_id, progset_id, program_summary['short'],
            program_summary, program_summary['active'])
        current_app.logger.debug(
            "writing program = \n%s\n" % pprint.pformat(program_summary, indent=2))
        db.session.add(program_record)
        db.session.flush()
        db.session.commit()

        return 204



class ProgramPopSizes(Resource):
    """
    Return estimated popsize for a Program & Parset
    """
    method_decorators = [report_exception, login_required]
    def get(self, project_id, progset_id, program_id, parset_id):
        current_app.logger.debug(
            "/api/project/%s/progsets/%s/program/%s/parset/%s/popsizes" %
            (project_id, progset_id, program_id, parset_id))
        program = load_program(project_id, progset_id, program_id)
        parset = load_parset(project_id, parset_id)
        settings = load_project(project_id).settings

        years = range(int(settings.start), int(settings.end) + 1)
        popsizes = program.gettargetpopsize(t=years, parset=parset)
        payload = normalize_obj(dict(zip(years, popsizes)))

        current_app.logger.debug('popsizes = \n%s\n' % payload)
        return payload, 201



costcov_graph_parser = RequestParser()
costcov_graph_parser.add_arguments({
    't': {'required': True, 'type': str, 'location': 'args'},
    'parset_id': {'required': True, 'type': uuid.UUID, 'location': 'args'},
    'caption': {'type': str, 'location': 'args'},
    'xupperlim': {'type': long, 'location': 'args'},
    'perperson': {'type': bool, 'location': 'args'},
})

class ProgramCostcovGraph(Resource):
    """
    Costcoverage graph for a Program and a Parset (for population sizes).
    """

    method_decorators = [report_exception, login_required]

    def get(self, project_id, progset_id, program_id):
        """
        Args:
            t: comma-separated list of years (>= startyear in data)
            parset_id: parset ID of project (not related to program targetpars)
            caption: string to display in graph
            xupperlim: maximum dollar shown
            perperson: cost per person shown as data point

        Returns an mpld3 dict that can be displayed with the mpld3 plugin
        """
        args = costcov_graph_parser.parse_args()
        parset_id = args['parset_id']

        try:
            t = map(int, args['t'].split(','))
        except ValueError:
            raise ValueError("t must be a year or a comma-separated list of years.")

        plotoptions = {}
        for x in ['caption', 'xupperlim', 'perperson']:
            if args.get(x):
                plotoptions[x] = args[x]

        program = load_program(project_id, progset_id, program_id)
        parset = load_parset(project_id, parset_id)

        plot = program.plotcoverage(t=t, parset=parset, plotoptions=plotoptions)

        mpld3.plugins.connect(plot, mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
        return normalize_obj(mpld3.fig_to_dict(plot))


