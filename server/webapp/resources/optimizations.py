import json
from pprint import pprint, pformat

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
    return normalize_obj(result)


def save_optimization_summaries(project_id, optimization_summaries):

    existing_ids = [
        summary['id']
        for summary in optimization_summaries
        if summary.get('id', False)
    ]

    db.session.query(OptimizationsDb) \
        .filter_by(project_id=project_id) \
        .filter(~OptimizationsDb.id.in_(existing_ids)) \
        .delete(synchronize_session='fetch')
    db.session.flush()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            record = OptimizationsDb(
                project_id=project_id,
                parset_id=summary['parset_id'],
                progset_id=summary['progset_id'],
                name=summary['name'],
                which=summary['which'])
        else:
            record = db.session.query(OptimizationsDb).get(id)

        record.update(
            constraints=summary['constraints'],
            objectives=summary['objectives'])

        verb = "Creating" if id is None else "Updating"
        print ">>>", verb, " optimizaton", summary['name']
        pprint(summary)

        db.session.add(record)
        db.session.flush()

    db.session.commit()


def get_default_optimization_summaries(project_id):
    project = load_project(project_id)
    progset_records = ProgsetsDb.query.filter_by(project_id=project_id).all()

    defaults_by_progset_id = {}
    for progset_record in progset_records:
        progset = progset_record.hydrate()
        progset_id = progset_record.id
        default = {
            'constraints': op.defaultconstraints(project=project, progset=progset),
            'objectives': {}
        }
        for which in ['outcomes', 'money']:
            default['objectives'][which] = op.defaultobjectives(
                project=project, progset=progset, which=which)
        defaults_by_progset_id[progset_id] = default

    return normalize_obj(defaults_by_progset_id)


class Optimizations(Resource):
    """
    /api/project/<uuid:project_id>/optimizations

    - GET: get the optimizations
    - POST: save new optimization
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        return {
            'optimizations':
                get_optimization_summaries(project_id),
            'defaultOptimizationsByProgsetId':
                get_default_optimization_summaries(project_id)
        }

    @swagger.operation()
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

    @swagger.operation(summary='Launch optimization')
    def post(self, project_id, optimization_id):

        from server.webapp.tasks import run_optimization, start_or_report_calculation
        from server.webapp.dbmodels import OptimizationsDb, ProgsetsDb

        optimization_record = OptimizationsDb.query.get(optimization_id)
        optimization_name = optimization_record.name
        parset_id = optimization_record.parset_id

        calc_state = start_or_report_calculation(project_id, parset_id, 'optimization')

        if not calc_state['can_start'] or not calc_state['can_join']:
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

    @swagger.operation(description='Provides optimization graph for the given project')
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
