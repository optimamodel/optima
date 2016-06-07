import uuid
from datetime import datetime
from pprint import pprint

import dateutil
from flask import current_app, helpers, request
from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger

import optima as op
from server.webapp.dataio import (
    load_project_record, TEMPLATEDIR, upload_dir_user, save_result_record, load_result,
    load_project, load_parset_record, load_parset_list, get_parset_from_project)
from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ResultsDb, ScenariosDb,OptimizationsDb
from server.webapp.exceptions import ParsetDoesNotExist, ParsetAlreadyExists
from server.webapp.parse import get_parset_parameters, put_parameters_in_parset
from server.webapp.resources.common import report_exception
from server.webapp.utils import AllowedSafeFilenameStorage, RequestParser, normalize_obj

copy_parser = RequestParser()
copy_parser.add_arguments({
    'name': {'required': True},
    'parset_id': {'type': uuid.UUID}
})



class Parsets(Resource):
    """
    GET /api/project/<project_id>/parsets

    Returns the parsets of a projects that are marshalled from the parset records.

    POST /api/project/<project_id>/parsets

    Makes a copy of the parset that is passed in as an argument in the body as parset_id,
    and or makes a new parset
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Download parsets for the project with the given id.')
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def get(self, project_id):
        current_app.logger.debug("/api/project/%s/parsets" % str(project_id))
        return load_parset_list(project_id)

    @swagger.operation(description='Create new parset with default settings or copy existing parset')
    def post(self, project_id):
        current_app.logger.debug("POST /api/project/{}/parsets".format(project_id))
        args = copy_parser.parse_args()
        print "args", args
        name = args['name']
        parset_id = args.get('parset_id')

        project_entry = load_project_record(project_id)
        project = project_entry.hydrate()

        if name in project.parsets:
            raise ParsetAlreadyExists(project_id, name)
        if not parset_id:
            # create new parset with default settings
            project.makeparset(name, overwrite=False)
            new_result = project.runsim(name)
            project_entry.restore(project)
            db.session.add(project_entry)

            result_record = save_result_record(project_entry.id, new_result, name)
            db.session.add(result_record)
        else:
            # dealing with uid's directly might be messy...
            original_parset = [item for item in project_entry.parsets if item.id == parset_id]
            if not original_parset:
                raise ParsetDoesNotExist(parset_id, project_id=project_id)
            original_parset = original_parset[0]
            parset_name = original_parset.name
            project.copyparset(orig=parset_name, new=name)
            project_entry.restore(project)
            db.session.add(project_entry)

            old_result_record = db.session.query(ResultsDb).filter_by(
                parset_id=str(parset_id), project_id=str(project_id),
                calculation_type=ResultsDb.CALIBRATION_TYPE).first()
            old_result = old_result_record.hydrate()
            new_result = op.dcp(old_result)
            new_result_record = save_result_record(project_entry.id, new_result, name)
            db.session.add(new_result_record)

        db.session.commit()

        rv = []
        for item in project_entry.parsets:
            rv_item = item.hydrate().__dict__
            rv_item['id'] = item.id
            rv.append(rv_item)

        return rv


rename_parser = RequestParser()
rename_parser.add_argument('name', required=True)

class ParsetsDetail(Resource):
    """
    DELETE /api/project/<uuid:project_id>/parsets/<uuid:parset_id>

    Deletes given parset

    PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>

    Renames the given parset
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Delete parset with parset_id.')
    @report_exception
    def delete(self, project_id, parset_id):

        current_app.logger.debug("DELETE /api/project/{}/parsets/{}".format(project_id, parset_id))
        project_entry = load_project_record(project_id, raise_exception=True)

        parset = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id, id=parset_id).first()
        if parset is None:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)

        # TODO: also delete the corresponding calibration results
        db.session.query(ResultsDb).filter_by(
            project_id=project_id, id=parset_id, calculation_type=ResultsDb.CALIBRATION_TYPE).delete()
        db.session.query(ScenariosDb).filter_by(project_id=project_id,
            parset_id=parset_id).delete()
        db.session.query(OptimizationsDb).filter_by(project_id=project_id,
            parset_id=parset_id).delete()
        db.session.query(ParsetsDb).filter_by(project_id=project_id, id=parset_id).delete()
        db.session.commit()

        return '', 204

    @swagger.operation(description='Rename parset with parset_id')
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def put(self, project_id, parset_id):
        """
        For consistency, let's always return the updated parsets for operations on parsets
        (so that FE doesn't need to perform another GET call)
        """

        current_app.logger.debug("PUT /api/project/{}/parsets/{}".format(project_id, parset_id))
        args = rename_parser.parse_args()
        name = args['name']

        project_record = load_project_record(project_id, raise_exception=True)
        parset_records = [record for record in project_record.parsets if record.id == parset_id]
        if not parset_records:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)
        parset_record = parset_records[0]
        parset_record.name = name
        db.session.add(parset_record)
        db.session.commit()
        return [record.hydrate() for record in project_record.parsets]



calibration_fields = {
    "parset_id": fields.String,
    "parameters": fields.Raw,
    "graphs": fields.Raw,
    "selectors": fields.Raw,
    "result_id": fields.String,
}

calibration_parser = RequestParser()
calibration_parser.add_argument('which', location='args', default=None, action='append')
calibration_parser.add_argument('autofit', location='args', default=False, type=bool)

calibration_update_parser = RequestParser()
calibration_update_parser.add_arguments({
    'which': {'default': None, 'action': 'append'},
    'parameters': {'required': True, 'type': dict, 'action': 'append'},
    'doSave': {'default': False, 'type': bool, 'location': 'args'},
    'autofit': {'default': False, 'type': bool, 'location': 'args'}
})

parset_save_with_autofit_parser = RequestParser()
parset_save_with_autofit_parser.add_arguments({
    'parameters': {'type': fields.Raw, 'required': True, 'action': 'append'},
    'result_id': {'type': uuid.UUID, 'required': True},
})

class ParsetsCalibration(Resource):
    """
    GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration

    Returns parameter summaries and graphs for a project/parset

    PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration

    Saves the parameters and gets graphs

    POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration

    Save parameters without fetching graphs
    """

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
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph])).replace('NaN', 'null')
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
        description='Provides calibration information for the given parset',
        notes="""
        Returns data suitable for manual calibration and the set of corresponding graphs.
        """,
        parameters=calibration_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(calibration_fields, envelope="calibration")
    def get(self, project_id, parset_id):
        current_app.logger.debug("/api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        args = calibration_parser.parse_args()
        which = args.get('which')
        autofit = args.get('autofit', False)
        calculation_type = 'autofit' if autofit else ResultsDb.CALIBRATION_TYPE
        print ">>>> Calculation type:", calculation_type

        parset_record = load_parset_record(project_id, parset_id)
        parset = parset_record.hydrate()
        result = load_result(project_id, parset_id, calculation_type)
        print ">>>> Result(%s) found: %s" % (calculation_type, result is not None)
        if result is None:
            print ">>>> Runsim for new calibration results..."
            project = load_project(project_id, autofit)
            simparslist = parset.interp()
            result = project.runsim(simpars=simparslist)
            record = save_result_record(project_id, result, parset.name, calculation_type)
            db.session.add(record)
            db.session.flush()
            db.session.commit()
            # print "Checking calibration result save %s" % result
        else:
            print ">>>> Fetch result(%s) '%s' for parset '%s'" % (calculation_type, result.name, parset.name)

        # generate graphs
        selectors = self._selectors_from_result(result, which)
        print ">>>>> Generating calibration graphs with selectors", which
        which = which or self._which_from_selectors(selectors)
        graphs = self._result_to_jsons(result, which)

        return {
            "parset_id": parset_id,
            "parameters": get_parset_parameters(parset),
            "graphs": graphs,
            "selectors": selectors,
            "result_id": result.uid if result else None
        }

    @report_exception
    @marshal_with(calibration_fields, envelope="calibration")
    def put(self, project_id, parset_id):
        current_app.logger.debug("PUT /api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        args = calibration_update_parser.parse_args()
        parameters = args.get('parameters', [])
        which = args.get('which')
        doSave = args.get('doSave')
        autofit = args.get('autofit', False)

        parset_record = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset_record is None or parset_record.project_id!=project_id:
            raise ParsetDoesNotExist(id=parset_id)

        # save parameters
        parset = parset_record.hydrate()
        put_parameters_in_parset(parameters, parset)

        # recalculate
        project_record = load_project_record(parset_record.project_id, raise_exception=True)
        project = project_record.hydrate()
        simparslist = parset.interp()
        result = project.runsim(simpars=simparslist)
        result_record = None

        if doSave:  # save the updated results
            parset_record.pars = op.saves(parset.pars)
            parset_record.updated = datetime.now(dateutil.tz.tzutc())
            db.session.add(parset_record)
            result_record = [item for item in project_record.results if
                            item.parset_id == parset_id and item.calculation_type == ResultsDb.CALIBRATION_TYPE]
            if result_record:
                result_record = result_record[-1]
                result_record.blob = op.saves(result)
            else:
                result_record = ResultsDb(
                    parset_id=parset_id,
                    project_id=project_record.id,
                    calculation_type=ResultsDb.CALIBRATION_TYPE,
                    blob=op.saves(result)
                )
            db.session.add(result_record)
            db.session.commit()

        # generate graphs
        selectors = self._selectors_from_result(result, which)
        which = which or self._which_from_selectors(selectors)
        graphs = self._result_to_jsons(result, which)

        return {
            "parset_id": parset_id,
            "parameters": get_parset_parameters(parset),
            "graphs": graphs,
            "selectors": selectors,
            "result_id": result_record.id if result_record is not None else None
        }

    @report_exception
    def post(self, project_id, parset_id):
        current_app.logger.debug("POST /api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        data = normalize_obj(request.get_json(force=True))

        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset_entry is None or parset_entry.project_id != project_id:
            raise ParsetDoesNotExist(id=parset_id)
        parset_instance = parset_entry.hydrate()
        put_parameters_in_parset(data['parameters'], parset_instance)

        parset_entry.pars = op.saves(parset_instance.pars)
        parset_entry.updated = datetime.now(dateutil.tz.tzutc())
        db.session.add(parset_entry)

        ResultsDb.query \
            .filter_by(
                parset_id=parset_id, project_id=project_id,
                calculation_type=ResultsDb.CALIBRATION_TYPE) \
            .delete()

        db.session.commit()

        return 200


manual_calibration_parser = RequestParser()
manual_calibration_parser.add_argument('maxtime', required=False, type=int, default=60)


class ParsetsAutomaticCalibration(Resource):
    """
    POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration

    Starts celery task to autofit parameters to historical data, returns:
    {
        'can_start': can_start,
        'can_join': can_join,
        'parset_id': wp_parset_id,
        'work_type': work_type
    }

    GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration

    Returns the status for the current job:
     {
        'status': work_log.status,
        'error_text': work_log.error,
        'start_time': work_log.start_time,
        'stop_time': work_log.stop_time,
        'result_id': work_log.result_id
    }
    """

    @swagger.operation(
        summary='Launch auto calibration for the selected parset',
        parameters=manual_calibration_parser.swagger_parameters()
    )
    @report_exception
    def post(self, project_id, parset_id):
        from server.webapp.tasks import run_autofit, start_or_report_calculation
        args = manual_calibration_parser.parse_args()
        parset_name = load_parset_record(project_id, parset_id).name
        result = start_or_report_calculation(project_id, parset_id, 'autofit')
        if not result['can_start'] or not result['can_join']:
            result['status'] = 'running'
            return result, 208
        else:
            run_autofit.delay(project_id, parset_name, args['maxtime'])
            result['status'] = 'started'
            result['maxtime'] = args['maxtime']
            return result, 201

    @report_exception
    def get(self, project_id, parset_id):
        from server.webapp.tasks import check_calculation_status
        return check_calculation_status(project_id)


file_upload_form_parser = RequestParser()
file_upload_form_parser.add_argument('file', type=AllowedSafeFilenameStorage, location='files', required=True)


class ParsetsData(Resource):
    """
    Export and import of the existing parset in / from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/x-gzip',
        summary='Download data for the parset with the given id from project with the given id',
        notes="""
        if parset exists, returns data for it
        if parset does not exist, returns an error.
        """
    )
    @report_exception
    def get(self, project_id, parset_id):
        current_app.logger.debug("GET /api/project/{0}/parset/{1}/data".format(project_id, parset_id))
        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id, project_id=project_id).first()
        if parset_entry is None:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = parset_entry.as_file(loaddir)

        response = helpers.send_from_directory(loaddir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)

        return response

    @swagger.operation(
        summary='Upload data for the parset with the given id in project with the given id',
        notes="""
        if parset exists, updates it with data from the file
        if parset does not exist, returns an error"""
    )
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def post(self, project_id, parset_id):
        # TODO replace this with app.config
        current_app.logger.debug("POST /api/project/{0}/parset/{1}/data".format(project_id, parset_id))

        print request.files, request.args
        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        project_entry = load_project_record(project_id, raise_exception=True)

        parset_entry = project_entry.find_parset(parset_id)
        parset_instance = op.loadobj(uploaded_file)

        parset_entry.restore(parset_instance)
        db.session.add(parset_entry)
        db.session.flush()

        # recalculate data (TODO: verify with Robyn if it's needed )
        project_instance = project_entry.hydrate()
        result = project_instance.runsim(parset_entry.name)
        current_app.logger.info("runsim result for project %s: %s" % (project_id, result))

        db.session.add(project_entry)  # todo: do we need to log that project was updated?
        db.session.flush()

        result_record = save_result_record(project_entry.id, result, parset_entry.name)
        db.session.add(result_record)

        db.session.commit()

        return [item.hydrate() for item in project_entry.parsets]
