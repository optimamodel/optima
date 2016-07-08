import uuid
import os
from datetime import datetime
from pprint import pprint

import dateutil
from flask import current_app, helpers, request
from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger

import optima as op
from server.webapp.dataio import (
    load_project_record, TEMPLATEDIR, upload_dir_user, save_result, load_result,
    load_project, load_parset, load_parset_list, get_parset_from_project)
from server.webapp.dbconn import db
from server.webapp.dbmodels import ResultsDb
from server.webapp.exceptions import ParsetDoesNotExist, ParsetAlreadyExists
from server.webapp.parse import get_parset_parameters, put_parameters_in_parset
from server.webapp.resources.common import report_exception
from server.webapp.utils import AllowedSafeFilenameStorage, RequestParser, normalize_obj
from server.webapp.plot import make_mpld3_graph_dict



copy_parser = RequestParser()
copy_parser.add_arguments({
    'name': {'required': True},
    'parset_id': {'type': uuid.UUID}
})


class Parsets(Resource):
    """
    GET /api/project/<project_id>/parsets

    Returns all parsets of a project for display in dropdown menu in calibration

    POST /api/project/<project_id>/parsets

    Copy or make new parset that is passed in  body as parset_id
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Download all parsets for project')
    def get(self, project_id):
        current_app.logger.debug("/api/project/%s/parsets" % str(project_id))
        project_entry = load_project_record(project_id)
        project = project_entry.load()

        return {"parsets": load_parset_list(project)}

    @swagger.operation(description='Create parset or copy existing parset')
    def post(self, project_id):
        current_app.logger.debug("POST /api/project/{}/parsets".format(project_id))
        args = copy_parser.parse_args()
        print "args", args
        name = args['name']
        parset_id = args.get('parset_id')

        project_entry = load_project_record(project_id)
        project = project_entry.load()

        if name in project.parsets:
            raise ParsetAlreadyExists(project_id, name)

        if not parset_id:
            # CREATE parset with default settings
            project.makeparset(name, overwrite=False)
            new_result = project.runsim(name)
            project_entry.save_obj(project)
            db.session.add(project_entry)

            result_record = save_result(project, new_result, name)
            db.session.add(result_record)
        else:
            original_parset = get_parset_from_project(project, parset_id)
            parset_name = original_parset.name
            project.copyparset(orig=parset_name, new=name)
            project_entry.save_obj(project)
            db.session.add(project_entry)

        db.session.commit()

        return load_parset_list(project)


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
        project = project_entry.load()

        parset = load_parset(project, parset_id)
        project.parsets.pop(parset.name)
        project_entry.save_obj(project)

        return '', 204

    @swagger.operation(description='Rename parset with parset_id')
    @report_exception
    def put(self, project_id, parset_id):
        """
        For consistency, let's always return the updated parsets for operations on parsets
        (so that FE doesn't need to perform another GET call)
        """
        current_app.logger.debug("PUT /api/project/{}/parsets/{}".format(project_id, parset_id))
        args = rename_parser.parse_args()
        name = args['name']

        project_record = load_project_record(project_id, raise_exception=True)
        project = project_record.load()

        parset = load_parset(project, parset_id)
        project.parsets.rename(parset.name, name)
        parset.name = name

        project_record.save_obj(project)

        return load_parset_list(project)



calibration_parser = RequestParser()
calibration_parser.add_argument('which', default=None, action='append')
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

    Returns parameter summaries and graphs for a project/parset, called on page init
    so doesn't really require a which

    PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration

    Saves the parameters and gets graphs

    POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration

    Save parameters without fetching graphs
    """

    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Returns parameter summaries and graphs for a project/parset')
    def get(self, project_id, parset_id):
        current_app.logger.debug("/api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        args = calibration_parser.parse_args()
        which = args.get('which')
        if which is not None:
            which = map(str, which)
        autofit = args.get('autofit', False)
        calculation_type = 'autofit' if autofit else ResultsDb.CALIBRATION_TYPE
        print "> Calculation type: %s, autofit: %s, which: %s" % (calculation_type, autofit, which)

        project = load_project(project_id)
        parset = load_parset(project, parset_id)
        result = load_result(project.uid, parset.uid, calculation_type)

        if result is None:
            print "> Runsim for new calibration results and store"
            project = load_project(project_id, autofit)
            simparslist = parset.interp()
            result = project.runsim(simpars=simparslist)
            result_record = save_result(project, result, parset.name, calculation_type)
            db.session.add(result_record)
            db.session.flush()
            db.session.commit()
        else:
            print "> Fetch result(%s) '%s' for parset '%s'" % (calculation_type, result.name, parset.name)

        print "> Generating graphs"
        graphs = make_mpld3_graph_dict(result, which)['graphs']

        return {
            "calibration": {
                "parset_id": parset_id,
                "parameters": get_parset_parameters(parset),
                "graphs": graphs,
                "resultId": result.uid,
            }
        }

    @report_exception
    def put(self, project_id, parset_id):
        current_app.logger.debug("PUT /api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        args = calibration_update_parser.parse_args()
        parameters = args.get('parameters', [])
        which = args.get('which')
        if which is not None:
            which = map(str, which)
        doSave = args.get('doSave')
        autofit = args.get('autofit', False)
        calculation_type = 'autofit' if autofit else ResultsDb.CALIBRATION_TYPE
        print "> Calculation type: %s, autofit: %s, which: %s" % (calculation_type, autofit, which)


        project_record = load_project_record(project_id)
        project = project_record.load()

        # update parset with uploaded parameters
        parset = get_parset_from_project(project, parset_id)
        put_parameters_in_parset(parameters, parset)

        # recalculate result for parset
        simparslist = parset.interp()
        result = project.runsim(simpars=simparslist)

        if doSave:  # save the updated results
            print "> Saving results", result.uid
            result_record = save_result(project, result, parset.name, calculation_type)
            db.session.add(result_record)
            db.session.commit()
        elif autofit:
            result = load_result(project_id, parset_id, calculation_type)
            print "> Loading autofit results", result.uid
            if 'improvement' not in which:
                which.insert(0, 'improvement')
        else:
            print "> Saving temporary calibration graphs", result.uid
            result_record = save_result(project, result, parset.name, "temp-" + calculation_type)

            db.session.add(result_record)
            db.session.commit()

        project.parsets[parset.name] = parset

        project_record.save_obj(project)

        print "> Generating graphs"
        graphs = make_mpld3_graph_dict(result, which)['graphs']

        return {
            'calibration': {
                "parset_id": parset_id,
                "parameters": get_parset_parameters(parset),
                "graphs": graphs,
                "resultId": str(result.uid),
            }
        }

    @report_exception
    def post(self, project_id, parset_id):
        current_app.logger.debug("POST /api/project/{}/parsets/{}/calibration".format(project_id, parset_id))
        data = normalize_obj(request.get_json(force=True))

        parset_record = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset_record is None or parset_record.project_id != project_id:
            raise ParsetDoesNotExist(id=parset_id)
        parset = parset_record.hydrate()
        put_parameters_in_parset(data['parameters'], parset)

        parset_record.pars = op.saves(parset.pars)
        parset_record.updated = datetime.now(dateutil.tz.tzutc())
        db.session.add(parset_record)

        ResultsDb.query \
            .filter_by(
                parset_id=parset_id, project_id=project_id, calculation_type="calibration") \
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

        project = load_project(project_id)
        parset = load_parset(project, parset_id)

        calc_status = start_or_report_calculation(project_id, parset_id, 'autofit')
        if not calc_status['can_start']:
            calc_status['status'] = 'running'
            return calc_status, 208
        else:
            run_autofit.delay(project_id, parset.name, args['maxtime'])
            calc_status['status'] = 'started'
            calc_status['maxtime'] = args['maxtime']
            return calc_status, 201

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

        project_record = load_project_record(project_id)
        project = project_record.load()

        parset = load_parset(project, parset_id)
        parset.project = None

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = project.uid.hex + "-" + parset.uid.hex + ".prst"
        op.saveobj(os.path.join(loaddir, filename), parset)

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
    def post(self, project_id, parset_id):
        # TODO replace this with app.config
        current_app.logger.debug("POST /api/project/{0}/parset/{1}/data".format(project_id, parset_id))

        print request.files, request.args
        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        project_entry = load_project_record(project_id, raise_exception=True)
        project = project_entry.load()

        parset = op.loadobj(uploaded_file)
        parset.project = project
        project.parsets[parset.name] = parset


        # recalculate data (TODO: verify with Robyn if it's needed )]
        result = project.runsim(parset.name)
        current_app.logger.info("runsim result for project %s: %s" % (project_id, result))

        project_entry.save_obj(project)

        result_record = save_result(project, result, parset.name)
        db.session.add(result_record)

        db.session.commit()

        return load_parset_list(project)



class ExportResultsDataAsCsv(Resource):
    """
    Export of data from an Optima Results object as a downloadable .csv file

    /api/results/<results_id>

    - GET: returns a .csv file as blob
    """

    method_decorators = [report_exception, login_required]

    def get(self, result_id):
        current_app.logger.debug("GET /api/results/{0}".format(result_id))
        result_record = db.session.query(ResultsDb).get(result_id)
        if result_record is None:
            raise Exception("Results '%s' does not exist" % result_id)
        load_dir = upload_dir_user(TEMPLATEDIR)
        if not load_dir:
            load_dir = TEMPLATEDIR
        filestem = 'results'
        filename = filestem + '.csv'
        result = result_record.hydrate()
        result.export(filestem=os.path.join(load_dir, filestem))

        response = helpers.send_from_directory(load_dir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)

        return response
