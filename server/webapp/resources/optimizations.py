import json
from pprint import pprint

from flask import current_app, helpers, request, Response

from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with, fields, marshal
from flask_restful_swagger import swagger

import optima as op

from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ResultsDb, OptimizationsDb, ProgsetsDb
from server.webapp.resources.common import report_exception
from server.webapp.utils import RequestParser, OptimaJSONEncoder, normalize_obj
from server.webapp.dataio import load_progset_record, load_project_record, load_project


def get_optimization_summaries(project_id):
    optimization_records = db.session.query(OptimizationsDb) \
        .filter_by(project_id=project_id).all()
    result = marshal(optimization_records, OptimizationsDb.resource_fields)
    result = normalize_obj(result)
    return result


def update_or_create_optimization_record(project_id,  optimization_summaries):
    existing_ids = [
        summary['id'] for summary in optimization_summaries if summary.get('id', False)]
    db.session.query(OptimizationsDb) \
        .filter_by(project_id=project_id) \
        .filter(~OptimizationsDb.id.in_(existing_ids)) \
        .delete(synchronize_session='fetch')
    db.session.flush()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            print ">>> Creating optimizaton", summary['name']
            record = OptimizationsDb(
                project_id=project_id,
                parset_id=summary['parset_id'],
                progset_id=summary['progset_id'],
                name=summary['name'],
                which=summary['which'])
        else:
            print ">>> Updating optimizaton", summary['name']
            record = db.session.query(OptimizationsDb).get(id)
        constraints = summary['constraints']
        objectives = summary['objectives']
        record.update(constraints=constraints, objectives=objectives)
        pprint(summary)

        db.session.add(record)
        db.session.flush()

    db.session.commit()


class Optimizations(Resource):
    """
    /api/project/<uuid:project_id>/optimizations

    - GET: get the optimizations
    - POST: save new optimization
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        project = load_project(project_id)
        progset_records = ProgsetsDb.query.filter_by(project_id=project_id).all()
        defaults = {}
        objective_types = ['outcomes', 'money']
        for progset_record in progset_records:
            progset = progset_record.hydrate()
            progset_id = progset_record.id
            defaults[progset_id] = {
                'constraints': op.defaultconstraints(project=project, progset=progset),
                'objectives': {}
            }
            for which in objective_types:
                defaults[progset_id]['objectives'][which] = \
                    op.defaultobjectives(project=project, progset=progset, which=which)
        return {
            'optimizations': get_optimization_summaries(project_id),
            'defaultsByProgsetId': normalize_obj(defaults)
        }

    @swagger.operation()
    def post(self, project_id):
        optimization_summaries = normalize_obj(request.get_json(force=True))
        update_or_create_optimization_record(project_id, optimization_summaries)
        optimization_summaries = get_optimization_summaries(project_id)
        print "Save optimizations"
        pprint(optimization_summaries)
        return {'optimizations': optimization_summaries}


class OptimizationCalculation(Resource):
    """
    /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results

    - POST: launch the optimization for a project
    - GET: poll running optimization for a project
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Launch optimization')
    def post(self, project_id, optimization_id):

        from server.webapp.tasks import run_optimization, start_or_report_calculation
        from server.webapp.dbmodels import OptimizationsDb, ProgsetsDb

        optimization_record = OptimizationsDb.query.get(optimization_id)
        optimization_name = optimization_record.name
        parset_id = optimization_record.parset_id
        progset_id = optimization_record.progset_id

        parset_entry = ParsetsDb.query.get(parset_id)
        parset_name = parset_entry.name

        progset_entry = ProgsetsDb.query.get(progset_id)
        progset_name = progset_entry.name

        calc_state = start_or_report_calculation(project_id, parset_id, 'optimization')
        if not calc_state['can_start'] or not calc_state['can_join']:
            calc_state['status'] = 'running'
            return calc_state, 208
        else:
            objectives = optimization_record.objectives
            constraints = optimization_record.constraints
            run_optimization.delay(
                project_id, optimization_name, parset_name,
                progset_name, objectives, constraints)
            calc_state['status'] = 'started'
            return calc_state, 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        from server.webapp.tasks import check_calculation_status
        calc_state = check_calculation_status(project_id)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state


optimization_which_parser = RequestParser()
optimization_which_parser.add_argument('which', location='args', default=None, action='append')

optimization_fields = {
    "optimization_id": fields.String,
    "graphs": fields.Raw,
    "selectors": fields.Raw,
    "result_id": fields.String,
}


class OptimizationGraph(Resource):

    method_decorators = [report_exception, login_required]

    def _result_to_jsons(self, result, which):
        import mpld3
        import json
        graphs = op.plotting.makeplots(result, figsize=(4, 3), toplot=[str(w) for w in which])  # TODO: store if that becomes an efficiency issue
        jsons = []
        for graph in graphs:
            # Add necessary plugins here
            mpld3.plugins.connect(graphs[graph], mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
            # a hack to get rid of NaNs, javascript JSON parser doesn't like them
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph]), cls=OptimaJSONEncoder)
            jsons.append(json.loads(json_string))
        return jsons

    def _selectors_from_result(self, result, which):
        graph_selectors = op.getplotselections(result)
        keys = graph_selectors['keys']
        names = graph_selectors['names']
        if which is None:
            checks = graph_selectors['defaults']
        else:
            checks = [key in which for key in keys]
        selectors = [{'key': key, 'name': name, 'checked': checked}
                     for (key, name, checked) in zip(keys, names, checks)]
        return selectors

    def _which_from_selectors(self, graph_selectors):
        return [item['key'] for item in graph_selectors if item['checked']]

    @swagger.operation(
        description='Provides optimization graph for the given project',
        notes="""
        Returns the set of corresponding graphs.
        """,
        parameters=optimization_which_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(optimization_fields, envelope="optimization")
    def get(self, project_id, optimization_id):
        current_app.logger.debug("/api/project/{}/optimizations/{}/graph".format(project_id, optimization_id))
        args = optimization_which_parser.parse_args()
        which = args.get('which')

        # TODO actually filter for the proper optimization id (Which would have to be saved for the given result)
        result_entry = db.session.query(ResultsDb).filter_by(project_id=project_id, calculation_type='optimization').first()
        if result_entry:
            result = result_entry.hydrate()
            selectors = self._selectors_from_result(result, which)
            which = which or self._which_from_selectors(selectors)
            graphs = self._result_to_jsons(result, which)
            payload = {
                "optimization_id": optimization_id,
                "graphs": graphs,
                "selectors": selectors,
                "result_id": result_entry.id if result_entry else None
            }
        else:
            payload = {
                "result_id": None
            }

        return payload
