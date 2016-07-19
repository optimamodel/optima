from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import make_scenarios_graphs, save_scenario_summaries, load_scenario_summaries
from server.webapp.resources.common import report_exception
from server.webapp.utils import get_post_data_json


class Scenarios(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='get scenarios for a project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/scenarios
        """
        return load_scenario_summaries(project_id)

    @swagger.operation(summary='update scenarios; returns scenarios so client-side can check')
    def put(self, project_id):
        """
        PUT /api/project/<uuid:project_id>/scenarios
        data-josn: scenarios: scenario_summaries
        """
        data = get_post_data_json()
        scenario_summaries = data['scenarios']
        return save_scenario_summaries(project_id, scenario_summaries)

class ScenarioSimulationGraphs(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Run scenarios and returns the graphs')
    def get(self, project_id):
        """
        GET /api/project/<project-id>/scenarios/results
        """
        return make_scenarios_graphs(project_id)

