from flask import request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import (
    load_project_record, check_project_exists, get_scenario_summaries,
    save_scenario_summaries, get_parset_keys_with_y_values,
    save_result)
from server.webapp.plot import make_mpld3_graph_dict
from server.webapp.resources.common import report_exception
from server.webapp.utils import normalize_obj

from server.webapp.dbconn import db
from server.webapp.dbmodels import ResultsDb


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
        return {
            'scenarios': get_scenario_summaries(project_id),
            'ykeysByParsetId': get_parset_keys_with_y_values(project_id)
        }

    def put(self, project_id):
        data = normalize_obj(request.get_json(force=True))
        save_scenario_summaries(project_id, data['scenarios'])
        return {'scenarios': get_scenario_summaries(project_id)}


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
        result = project.results[-1]
        result_records = db.session.query(ResultsDb).filter_by(
            project_id=project_id, calculation_type="scenario"
        )
        result_records.delete()
        result_record = save_result(project_id, result, project.parsets[0].name, "scenario")
        db.session.add(result_record)
        db.session.commit()
        return make_mpld3_graph_dict(result)


