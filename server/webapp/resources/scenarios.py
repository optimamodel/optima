from flask import request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import (
    load_project_record, check_project_exists, get_scenario_summaries,
    save_scenario_summaries, get_parset_keys_with_y_values)
from server.webapp.plot import make_mpld3_graph_dict
from server.webapp.resources.common import report_exception
from server.webapp.utils import normalize_obj


class ScenarioParameterKeys(Resource):
    """
    /api/project/<uuid:project_id>/parsets/ykeys

    - GET: Get the keys of parameters that are controllable by programs
    """
    @swagger.operation(summary='get parsets ykeys')
    def get(self, project_id):
        return {'keys': get_parset_keys_with_y_values(project_id)}


class Scenarios(Resource):
    """
    /api/project/<uuid:project_id>/scenarios

    Used in the scenario pages

    - GET: get scenarios for a project
    - PUT: update and add scenarios
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        check_project_exists(project_id)
        return get_scenario_summaries(project_id)

    def put(self, project_id):
        data = normalize_obj(request.get_json(force=True))
        save_scenario_summaries(project_id, data['scenarios'])
        return get_scenario_summaries(project_id)


class ScenarioSimulationGraphs(Resource):
    """
    /api/project/<project-id>/scenarios/results

    - GET: Run scenarios and returns the graphs
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        project_entry = load_project_record(project_id)
        project = project_entry.hydrate()
        project.runscenarios()
        return make_mpld3_graph_dict(project.results[-1])


