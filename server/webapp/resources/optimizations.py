import json
from pprint import pformat

from flask import request
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

import optima as op
from server.webapp.dataio import (
    load_project_record, get_optimization_from_project, load_result_by_optimization, load_project,
    get_optimization_summaries, save_optimization_summaries, get_default_optimization_summaries)
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

        from server.webapp.tasks import run_optimization, start_or_report_calculation, shut_down_calculation

        maxtime = float(json.loads(request.data).get('maxtime'))

        project_record = load_project_record(project_id)
        project = project_record.load()

        optim = get_optimization_from_project(project, optimization_id)
        parset = project.parsets[optim.parsetname]

        calc_state = start_or_report_calculation(
            project_id, parset.uid, 'optim-' + optim.name)

        if calc_state['status'] != 'started':
            return calc_state, 208

        progset = project.progsets[optim.progsetname]

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
            shut_down_calculation(project_id, parset.uid, 'optimization')
            raise Exception(error_msg)

        objectives = normalize_obj(optim.objectives)
        constraints = normalize_obj(optim.constraints)
        constraints["max"] = op.odict(constraints["max"])
        constraints["min"] = op.odict(constraints["min"])
        constraints["name"] = op.odict(constraints["name"])

        run_optimization.delay(
            project_id, optim.name, parset.name, progset.name, objectives, constraints, maxtime)

        return calc_state, 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        from server.webapp.tasks import check_calculation_status

        project_record = load_project_record(project_id)
        project = project_record.load()

        optim = get_optimization_from_project(project, optimization_id)
        parset = project.parsets[optim.parsetname]

        print "> Checking calc state"
        calc_state = check_calculation_status(
            project_id,
            parset.uid,
            'optim-' + optim.name)
        print pformat(calc_state, indent=2)
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
    def post(self, project_id, optimization_id):
        args = normalize_obj(json.loads(request.data))
        which = args.get('which')
        if which is not None:
            which = map(str, which)

        project = load_project(project_id)
        optimization = get_optimization_from_project(project, optimization_id)

        result = load_result_by_optimization(project, optimization)
        if result is None:
            return {}
        else:
            return make_mpld3_graph_dict(result, which)
