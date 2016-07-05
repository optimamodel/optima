import json
from pprint import pformat

from flask import request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

import optima as op
from server.webapp.dataio import (
    get_optimization_summaries, save_optimization_summaries, get_default_optimization_summaries,
    load_result_by_optimization_id, load_optimization_record)
from server.webapp.dbmodels import ParsetsDb
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
        return {
            'optimizations': get_optimization_summaries(project_id),
            'defaultOptimizationsByProgsetId': get_default_optimization_summaries(project_id)
        }

    def post(self, project_id):
        optimization_summaries = normalize_obj(request.get_json(force=True))
        save_optimization_summaries(project_id, optimization_summaries)
        return {'optimizations': get_optimization_summaries(project_id)}


class OptimizationCalculation(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results

    - POST: launch the optimization for a project
    - GET: poll running optimization for a project
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Launch optimization calculation')
    def post(self, project_id, optimization_id):

        from server.webapp.tasks import run_optimization, start_or_report_calculation, shut_down_calculation
        from server.webapp.dbmodels import OptimizationsDb, ProgsetsDb

        maxtime = float(json.loads(request.data).get('maxtime'))

        optimization_record = OptimizationsDb.query.get(optimization_id)
        optimization_name = optimization_record.name
        parset_id = optimization_record.parset_id

        calc_state = start_or_report_calculation(
            project_id, parset_id, 'optim-' + optimization_name)

        if calc_state['status'] != 'started':
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
            shut_down_calculation(project_id, parset_id, 'optimization')
            raise Exception(error_msg)

        objectives = normalize_obj(optimization_record.objectives)
        constraints = normalize_obj(optimization_record.constraints)
        constraints["max"] = op.odict(constraints["max"])
        constraints["min"] = op.odict(constraints["min"])
        constraints["name"] = op.odict(constraints["name"])

        run_optimization.delay(
            project_id, optimization_name, parset_name, progset_name, objectives, constraints, maxtime)

        return calc_state, 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        from server.webapp.tasks import check_calculation_status
        optimization_record = load_optimization_record(optimization_id)
        calc_state = check_calculation_status(
            project_id,
            optimization_record.parset_id,
            'optim-' + optimization_record.name)
        print ">>> Checking calc state", pformat(calc_state, indent=2)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state


class OptimizationGraph(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph
    - POST: gets the mpld3 graphs for the optimizations
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Provides optimization graph for the given project')
    def post(self, optimization_id):
        args = normalize_obj(json.loads(request.data))
        which = args.get('which')
        if which is not None:
            which = map(str, which)

        result = load_result_by_optimization_id(optimization_id)
        if result is None:
            return {}
        else:
            return make_mpld3_graph_dict(result, which)
