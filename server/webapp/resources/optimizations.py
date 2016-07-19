from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import load_optimization_summaries, save_optimization_summaries, \
    load_optimization_graphs, check_optimization_calc_state, launch_optimization
from server.webapp.resources.common import report_exception
from server.webapp.utils import get_post_data_json


class Optimizations(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns list of optimization summaries")
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/optimizations
        """
        return load_optimization_summaries(project_id)

    @swagger.operation(summary="Uploads project with optimization summaries, and returns summaries")
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/optimizations
        data-json: optimization_summaries
        """
        optimization_summaries = get_post_data_json()
        return save_optimization_summaries(project_id, optimization_summaries)


class OptimizationCalculation(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results

    - POST: launch the optimization for a project
    - GET: poll running optimization for a project
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Launch optimization calculation')
    def post(self, project_id, optimization_id):
        """
        POST /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results
        data-json: maxtime: time to run in int
        """
        maxtime = get_post_data_json().get('maxtime')
        return launch_optimization(project_id, optimization_id, maxtime), 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        """
        GET /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results
        """
        return check_optimization_calc_state(project_id, optimization_id)


class OptimizationGraph(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Provides optimization graph for the given project')
    def post(self, project_id, optimization_id):
        """
        POST /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph
        post-json: which: list of graphs to display
        """
        which = get_post_data_json().get('which')
        load_optimization_graphs(project_id, optimization_id, which)
