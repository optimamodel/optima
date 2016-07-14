import uuid

from pprint import pprint

from flask import current_app, request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import (
    get_progset_summaries, save_progset_summaries, load_project, load_project_record,
    get_target_popsizes, load_parameters_from_progset_parset,
    get_progset_from_project, get_progset_summary, get_parset_from_project,
    get_program_from_progset, save_program_summary)
from server.webapp.parse import parse_outcomes_from_progset, put_outcomes_into_progset
from server.webapp.resources.common import report_exception
from server.webapp.utils import Json, RequestParser, normalize_obj


progset_parser = RequestParser()
progset_parser.add_arguments(
    {'name': {'required': True}, 'programs': {'type': Json, 'location': 'json'}})

class Progsets(Resource):
    """
    GET /api/project/<uuid:project_id>/progsets

    Get progsets for program-set manage page

    POST /api/project/<uuid:project_id>/progsets

    Save newly created progset in the client
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Download progsets')
    def get(self, project_id):
        project = load_project(project_id)

        return get_progset_summaries(project)


    @swagger.operation(description='Save progset')
    def post(self, project_id):
        data = normalize_obj(request.get_json(force=True))
        current_app.logger.debug("DATA progsets for project_id %s is :/n %s" % (project_id, pprint(data)))

        project_record = load_project_record(project_id)
        project = project_record.load()

        save_progset_summaries(project, data)
        project_record.save_obj(project)

        return get_progset_summaries(project)


class Progset(Resource):
    """
    PUT /api/project/<uuid:project_id>/progsets/<uuid:progset_id>

    Update existing progset
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Update progset with the given id.')
    def put(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        data = normalize_obj(request.get_json(force=True))

        project_record = load_project_record(project_id)
        project = project_record.load()

        save_progset_summaries(project, data, progset_id=progset_id)
        project_record.save_obj(project)

        return get_progset_summary(project.progsets[data["name"]])

    @swagger.operation(description='Delete progset with the given id.')
    def delete(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))

        project_record = load_project_record(project_id)
        project = project_record.load()

        progset = get_progset_from_project(project, progset_id)
        project.progsets.pop(progset.name)

        project_record.save_obj(project)
        return '', 204


class ProgsetParameters(Resource):

    """
    GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/parameters/<uuid:parset_id>

    Fetches parameters for a progset/parset combo to be used in outcome functions.
    """
    @swagger.operation(description='Get parameters sets for the selected progset')
    def get(self, project_id, progset_id, parset_id):

        project = load_project(project_id)
        progset = get_progset_from_project(project, progset_id)
        parset = get_parset_from_project(project, parset_id)

        return load_parameters_from_progset_parset(project, progset, parset)



class ProgsetEffects(Resource):
    """
    GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects

    Fetch the effects of a given progset, given in the marshalled fields of
    a ProgsetsDB record, used in cost-coverage-ctrl.js

    PUT /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects

    Saves the effects of a given progset, used in cost-coverage-ctrl.js
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Get List of existing Progset effects for the selected progset')
    def get(self, project_id, progset_id):

        project = load_project(project_id)
        progset = get_progset_from_project(project, progset_id)

        outcomes = parse_outcomes_from_progset(progset)

        # Bosco needs to fix this...

        return { 'effects': [{
            "parset": parset.uid,
            "parameters": outcomes,

        } for parset in project.parsets.values()]}

    @swagger.operation(summary='Saves a list of outcomes')
    def put(self, project_id, progset_id):
        effects = normalize_obj(request.get_json(force=True))

        project_record = load_project_record(project_id)
        project = project_record.load()
        progset = get_progset_from_project(project, progset_id)

        put_outcomes_into_progset(effects[0]["parameters"], progset)

        project_record.save_obj(project)

        outcomes = parse_outcomes_from_progset(progset)

        return { 'effects': [{
            "parset": parset.uid,
            "parameters": outcomes,

        } for parset in project.parsets.values()]}


query_program_parser = RequestParser()
query_program_parser.add_arguments({
    'program': {'required': True, 'type': Json, 'location': 'json'},
})

class Program(Resource):
    """
    POST /api/project/<project_id>/progsets/<progset_id>/program"

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
        args = query_program_parser.parse_args()
        program_summary = normalize_obj(args['program'])

        project_record = load_project_record(project_id)
        project = project_record.load()

        progset = get_progset_from_project(project, progset_id)

        print("> Saving program " + program_summary['name'])
        save_program_summary(progset, program_summary)

        progset.updateprogset()

        project_record.save_obj(project)

        return 204


class ProgramPopSizes(Resource):
    """
    /api/project/{project_id}/progsets/{progset_id}/program/{program_id}/parset/{progset_id}/popsizes

    Return estimated popsize for a given program and parset. Used in
    cost-coverage function page to help estimate populations.
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id, progset_id, program_id, parset_id):

        project = load_project(project_id)
        parset = get_parset_from_project(project, parset_id)
        progset = get_progset_from_project(project, progset_id)
        program = get_program_from_progset(progset, program_id)

        payload = get_target_popsizes(project, parset, progset, program)
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

        print '>>>> Generating plot...'

        try:
            t = map(int, args['t'].split(','))
        except ValueError:
            t = None

        if t is None:
            return {}

        plotoptions = {}
        for x in ['caption', 'xupperlim', 'perperson']:
            if args.get(x):
                plotoptions[x] = args[x]

        project = load_project(project_id)
        progset = get_progset_from_project(project, progset_id)

        program = get_program_from_progset(progset, program_id)
        parset = get_parset_from_project(project, parset_id)
        plot = program.plotcoverage(t=t, parset=parset, plotoptions=plotoptions)
        print '>>>> plot', plot
        from server.webapp.plot import convert_to_mpld3
        return convert_to_mpld3(plot)
