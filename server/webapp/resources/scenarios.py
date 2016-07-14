from flask import request
from flask.ext.login import login_required
from flask_restful import Resource

from server.webapp.resources.common import report_exception
from server.webapp.utils import normalize_obj
from server.webapp.dataio import (
    load_project_record, get_scenario_summaries,
    save_scenario_summaries,
    get_parameters_for_scenarios, make_scenarios_graphs)


class Scenarios(Resource):
    """
    /api/project/<uuid:project_id>/scenarios
    - GET: get scenarios for a project
    - PUT: update scenarios; returns scenarios so client-side can check
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id):
        project_record = load_project_record(project_id)
        project = project_record.load()

        return {
            'scenarios': get_scenario_summaries(project),
            'ykeysByParsetId': get_parameters_for_scenarios(project)
        }

    def put(self, project_id):
        data = normalize_obj(request.get_json(force=True))

        project_record = load_project_record(project_id)
        project = project_record.load()

        save_scenario_summaries(project, data['scenarios'])

        project_record.save_obj(project)

        return {'scenarios': get_scenario_summaries(project)}


class ScenarioSimulationGraphs(Resource):
    """
    /api/project/<project-id>/scenarios/results
    - GET: Run scenarios and returns the graphs
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id):
        return make_scenarios_graphs(project_id)

