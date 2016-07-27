import json

from flask import request, make_response, current_app
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import load_parameters_from_progset_parset, \
    load_target_popsizes, load_progset_summaries, create_progset, \
    save_progset, delete_progset, load_progset_outcome_summaries, \
    save_outcome_summaries, save_program, load_costcov_graph, \
    upload_progset
from server.webapp.resources.common import report_exception
from server.webapp.utils import get_post_data_json, get_upload_file

import pprint


class Progsets(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Return progset summaries')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/progsets
        """
        return load_progset_summaries(project_id)

    @swagger.operation(description='Create a new progset')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/progsets
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return create_progset(project_id, progset_summary)


class Progset(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Update progset with the given id.')
    def put(self, project_id, progset_id):
        """
        PUT /api/project/<uuid:project_id>/progset/<uuid:progset_id>
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return save_progset(project_id, progset_id, progset_summary)

    @swagger.operation(description='Delete progset with the given id.')
    def delete(self, project_id, progset_id):
        """
        DELETE /api/project/<uuid:project_id>/progset/<uuid:progset_id>
        """
        delete_progset(project_id, progset_id)
        return '', 204


class ProgsetUploadDownload(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, progset_id):
        """
        POST /api/project/<uuid:project_id>/progset/<uuid:progset_id>/data
        file-upload
        """
        json_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload progset JSON file '%s'" % json_fname)
        progset_summary = json.load(open(json_fname))
        return upload_progset(project_id, progset_id, progset_summary)


class ProgsetParameters(Resource):

    @swagger.operation(description='Return parameters for progset outcome page')
    def get(self, project_id, progset_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/parameters/<uuid:parset_id>
        """
        return load_parameters_from_progset_parset(project_id, progset_id, parset_id)


class ProgsetOutcomes(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Returns list of outcomes for a progset')
    def get(self, project_id, progset_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects
        """
        return load_progset_outcome_summaries(project_id, progset_id)

    @swagger.operation(summary='Saves the outcomes of a given progset, used in outcome page')
    def put(self, project_id, progset_id):
        """
        PUT /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects
        """
        outcome_summaries = get_post_data_json()
        return save_outcome_summaries(project_id, progset_id, outcome_summaries)


class Program(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Saves a program summary to project')
    def post(self, project_id, progset_id):
        """
        POST /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program
        data-json: programs: program_summary
        """
        program_summary = get_post_data_json()['program']
        save_program(project_id, progset_id, program_summary)
        return 204


class ProgramPopSizes(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Return estimated popsize for a given program and parset')
    def get(self, project_id, progset_id, program_id, parset_id):
        """
        GET /api/project/{project_id}/progsets/{progset_id}/program/{program_id}/parset/{progset_id}/popsizes
        """
        payload = load_target_popsizes(project_id, parset_id, progset_id, program_id)
        return payload, 201


class ProgramCostcovGraph(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Returns an mpld3 dict that can be displayed with the mpld3 plugin')
    def get(self, project_id, progset_id, program_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage/graph
        url-args:
            t: comma-separated list of years (>= startyear in data)
            parset_id: parset ID of project (not related to program targetpars)
            caption: string to display in graph
            xupperlim: maximum dollar shown
            perperson: cost per person shown as data point
        """
        args = request.args

        parset_id = args['parset_id']

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

        print '>>>> Generating plot...'
        return load_costcov_graph(
            project_id, progset_id, program_id, parset_id, t, plotoptions)