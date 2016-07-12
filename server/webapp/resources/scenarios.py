from flask import request
from flask.ext.login import login_required
from flask_restful import Resource

from server.webapp.resources.common import report_exception
from server.webapp.utils import normalize_obj
from server.webapp.dataio import (
    load_scenario_summaries, save_scenario_summaries,
    get_parameters_for_scenarios, make_scenarios_graphs,
    load_scenarios_graphs)


class Scenarios(Resource):
    """
    /api/project/<uuid:project_id>/scenarios
    - GET: get scenarios for a project
    - PUT: update scenarios; returns scenarios so client-side can check
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id):
        return {
            'scenarios': load_scenario_summaries(project_id),
            'ykeysByParsetId': get_parameters_for_scenarios(project_id)
        }

    def put(self, project_id):
        data = normalize_obj(request.get_json(force=True))
        save_scenario_summaries(project_id, data['scenarios'])
        return {'scenarios': load_scenario_summaries(project_id)}


class ScenarioSimulationGraphs(Resource):
    """
    /api/project/<project-id>/scenarios/results
    - GET: Run scenarios and returns the graphs
    - POST: Returns stored graphs with optional which
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id):
        return make_scenarios_graphs(project_id)

    def post(self, project_id):
        """
        Post-body-args:
            which: list of graph selectors
        Returns:
            mpld3 graphs
        """
        args = normalize_obj(request.get_json())
        which = args.get('which', None)
        return load_scenarios_graphs(project_id, which)

