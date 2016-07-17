import json
import pprint

from flask import helpers, request, make_response
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import (
    load_result_by_id, copy_parset, create_parset, load_parset_summaries,
    rename_parset, delete_parset, generate_parset_graphs, load_result_dir_filename,
    load_parameters, save_parameters)
from server.webapp.plot import make_mpld3_graph_dict
from server.webapp.resources.common import report_exception
from server.webapp.utils import AllowedSafeFilenameStorage, RequestParser, normalize_obj


class Parsets(Resource):
    """
    /api/project/<project_id>/parsets
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Get parset summaries for project')
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parsets
        Returns a list of parset summaries
        """
        print("> Load parsets")
        return {"parsets": load_parset_summaries(project_id)}

    @swagger.operation(description='Create parset or copy existing parset')
    def post(self, project_id):
        """
        POST /api/project/<project_id>/parsets
        Copy/create a parset, and returns a list of parset summaries

        Post-body:
            name: name of parset
            parset_id: id of parset (copy) or null (create
        """
        args = normalize_obj(request.get_json())
        new_parset_name = args['name']
        parset_id = args.get('parset_id')

        if not parset_id:
            print("> Create parset " + new_parset_name)
            create_parset(project_id, new_parset_name)
        else:
            print("> Copy parset " + new_parset_name)
            copy_parset(project_id, parset_id, new_parset_name)

        return load_parset_summaries(project_id)


class ParsetRenameDelete(Resource):
    """
    /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Delete parset with parset_id.')
    def delete(self, project_id, parset_id):
        """
        DELETE /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        """
        print("> Delete parset '%s'" % parset_id)
        delete_parset(project_id, parset_id)
        return '', 204

    @swagger.operation(description='Rename parset with parset_id')
    def put(self, project_id, parset_id):
        """
        PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        Renames the given parset and returns a list of parset summaries
        """
        name = normalize_obj(request.get_json())['name']
        print("> Rename parset '%s'" % name)
        rename_parset(project_id, parset_id, name)
        return load_parset_summaries(project_id)


class ParsetCalibration(Resource):
    """
    /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Returns parameter summaries and graphs for a project/parset')
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        Returns the graphs for parset_id

        Url-query:
            autofit: boolean - true loads the results from the autofit parameters
        """
        autofit = request.args.get('autofit', False)
        calculation_type = 'autofit' if autofit else "calibration"
        print "> Get calibration graphs for %s" % (calculation_type)
        return generate_parset_graphs(project_id, parset_id, calculation_type)

    @swagger.operation(description='Updates parameters and returns graphs')
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        Updates a parset and returns the graphs for a parset_id

        Post-body:
            parameters: parset_summary
            which: list of graphs to generate
            autofit: boolean indicates to fetch the autofit version of the results
        """
        args = normalize_obj(json.loads(request.data))
        autofit = args.get('autofit', False)
        calculation_type = 'autofit' if autofit else "calibration"
        parameters = args.get('parameters')
        which = args.get('which')
        print "> Update calibration graphs for %s" % (calculation_type)
        return generate_parset_graphs(
            project_id, parset_id, calculation_type, which, parameters)


class ParsetAutofit(Resource):
    """
    /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration

    Calc_status:
    {
        'status': "blocked", "started" tc.
        'error_text': string,
        'start_time': datetime_string,
        'stop_time': datetime_string,
        'result_id': uuid_string
    }
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Launch auto calibration')
    def post(self, project_id, parset_id):
        """
        POST: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        Starts autofit task and returns calc_status

        Post-query:
            maxtime: int - number of seconds to run
        """
        from server.webapp.tasks import run_autofit, start_or_report_calculation
        maxtime = json.loads(request.data).get('maxtime')
        calc_status = start_or_report_calculation(project_id, parset_id, 'autofit')
        if calc_status['status'] != "blocked":
            print "> Starting autofit for %s s" % maxtime
            run_autofit.delay(project_id, parset_id, maxtime)
            calc_status['maxtime'] = maxtime
        return calc_status

    @swagger.operation(summary='Poll autofit status')
    def get(self, project_id, parset_id):
        """
        GET: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        Returns the calc status for the current job
        """
        from server.webapp.tasks import check_calculation_status
        print "> Checking calc state"
        calc_state = check_calculation_status(project_id, parset_id, 'autofit')
        pprint.pprint(calc_state, indent=2)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state


file_upload_form_parser = RequestParser()
file_upload_form_parser.add_argument('file', type=AllowedSafeFilenameStorage, location='files', required=True)


class ParsetUploadDownload(Resource):
    """
    /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
    Export and import of the existing parset in / from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Download JSON of parameters")
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        Return a JSON file of the parameters
        """
        print("> Download JSON file of parset %s" % parset_id)
        parameters = load_parameters(project_id, parset_id)
        response = make_response(json.dumps(parameters, indent=2))
        response.headers["Content-Disposition"] = "attachment; filename=parset.json"
        return response

    @swagger.operation(summary="Upload JSON of parameters")
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        Update from JSON file of the parameters
        """
        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']
        print("> Upload parset JSON file '%s'" % uploaded_file)
        parameters = json.load(uploaded_file)
        save_parameters(project_id, parset_id, parameters)
        return load_parset_summaries(project_id)


class ResultsExport(Resource):
    """
    /api/results/<results_id>
    """
    method_decorators = [report_exception, login_required]

    def get(self, result_id):
        """
        GET /api/results/<results_id>
        Returns result as downloadable .csv file
        """
        load_dir, filename = load_result_dir_filename(result_id)
        response = helpers.send_from_directory(load_dir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        return response

    def post(self, result_id):
        """
        POST /api/results/<results_id>
        Returns graphs of a result_id, using which selectors

        post-body:
            result_id: uuid of results
        """
        args = normalize_obj(request.get_json())
        result = load_result_by_id(result_id)
        return make_mpld3_graph_dict(result, args.get('which'))

