from pprint import pformat

from flask import request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

import optima as op
from server.webapp.dataio import (
    load_project_record,
    get_optimization_summaries, save_optimization_summaries, get_default_optimization_summaries)
from server.webapp.dbconn import db
from server.webapp.dbmodels import ResultsDb
from server.webapp.plot import make_mpld3_graph_dict
from server.webapp.resources.common import report_exception
from server.webapp.utils import normalize_obj


class Optimizations(Resource):
    """
    /api/project/<uuid:project_id>/optimizations

    - GET: get optimizations
    - POST: save optimization
    """
    method_decorators = [report_exception, login_required]

    def get(self, project_id):

        project_record = load_project_record(project_id)
        project = project_record.load()

        return {
            'optimizations': get_optimization_summaries(project),
            'defaultOptimizationsByProgsetId': get_default_optimization_summaries(project)
        }

    def post(self, project_id):

        project_record = load_project_record(project_id)
        project = project_record.load()

        optimization_summaries = normalize_obj(request.get_json(force=True))
        save_optimization_summaries(project, optimization_summaries)

        project_record.save_obj(project)

        return {'optimizations': get_optimization_summaries(project)}


class OptimizationCalculation(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results

    - POST: launch the optimization for a project
    - GET: poll running optimization for a project
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Launch optimization calculation')
    def post(self, project_id, optimization_id):

        from server.webapp.tasks import run_optimization, start_or_report_calculation
        from server.webapp.dbmodels import OptimizationsDb, ProgsetsDb

        optimization_record = OptimizationsDb.query.get(optimization_id)
        optimization_name = optimization_record.name
        parset_id = optimization_record.parset_id

        calc_state = start_or_report_calculation(project_id, parset_id, 'optimization')

        if not calc_state['can_start']:
            calc_state['status'] = 'running'
            return calc_state, 208

        parset_entry = ParsetsDb.query.get(parset_id)
        parset_name = parset_entry.name

        progset_id = optimization_record.progset_id
        progset_entry = ProgsetsDb.query.get(progset_id)
        progset = progset_entry.hydrate()
        progset_name = progset_entry.name

        if not progset.readytooptimize():
            error_msg = "Not ready to optimize\n"
            costcov_errors = progset.hasallcostcovpars(detail=True)
            if costcov_errors:
                error_msg += "Missing: cost-coverage parameters of:\n"
                error_msg += pformat(costcov_errors, indent=2)
            covout_errors = progset.hasallcovoutpars(detail=True)
            if covout_errors:
                error_msg += "Missing: coverage-outcome parameters of:\n"
                error_msg += pformat(covout_errors, indent=2)
            raise Exception(error_msg)

        objectives = normalize_obj(optimization_record.objectives)
        constraints = normalize_obj(optimization_record.constraints)
        constraints["max"] = op.odict(constraints["max"])
        constraints["min"] = op.odict(constraints["min"])
        constraints["name"] = op.odict(constraints["name"])

        run_optimization.delay(
            project_id, optimization_name, parset_name, progset_name, objectives, constraints)

        calc_state['status'] = 'started'

        return calc_state, 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        from server.webapp.tasks import check_calculation_status
        calc_state = check_calculation_status(project_id)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state



class OptimizationGraph(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph
    - GET: gets the mpld3 graphs for the optimizations
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Provides optimization graph for the given project')
    def get(self, project_id, optimization_id):
        result_entry = db.session.query(ResultsDb)\
            .filter_by(project_id=project_id, calculation_type='optimization')\
            .first()
        if not result_entry:
            return {"result_id": None}
        else:
            return make_mpld3_graph_dict(result_entry.hydrate())
