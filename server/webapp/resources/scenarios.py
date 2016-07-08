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


class Scenarios(Resource):
    """
    /api/project/<uuid:project_id>/scenarios
    - GET: get scenarios for a project
    - PUT: update scenarios; returns scenarios so client-side can check
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        check_project_exists(project_id)

        project_record = load_project_record(project_id)
        project = project_record.load()

        return {
            'scenarios': get_scenario_summaries(project),
            'ykeysByParsetId': get_parset_keys_with_y_values(project)
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

    @swagger.operation()
    def get(self, project_id):
        project_entry = load_project_record(project_id)
        project = project_entry.load()
        project.runscenarios()
        return make_mpld3_graph_dict(project.results[-1])
