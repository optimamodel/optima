import json
import pprint

from flask import helpers, request, make_response, current_app
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import copy_parset, create_parset, load_parset_summaries, \
    rename_parset, delete_parset, load_parset_graphs, load_result_csv, \
    load_parameters, save_parameters, load_result_mpld3_graphs
from server.webapp.resources.common import report_exception
from server.webapp.utils import get_post_data_json, get_upload_file


class Parsets(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Returns a list of parset summaries')
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parsets
        """
        print("> Load parsets")
        return {"parsets": load_parset_summaries(project_id)}

    @swagger.operation(description='Copy/create a parset, and returns a list of parset summaries')
    def post(self, project_id):
        """
        POST /api/project/<project_id>/parsets
        data-json:
            name: name of parset
            parset_id: id of parset (copy) or null (create
        """
        args = get_post_data_json()
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
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Delete parset with parset_id.')
    def delete(self, project_id, parset_id):
        """
        DELETE /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        """
        print("> Delete parset '%s'" % parset_id)
        delete_parset(project_id, parset_id)
        return '', 204

    @swagger.operation(description='Rename parset and returns a list of parset summaries')
    def put(self, project_id, parset_id):
        """
        PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        """
        name = get_post_data_json()['name']
        print("> Rename parset '%s'" % name)
        rename_parset(project_id, parset_id, name)
        return load_parset_summaries(project_id)


class ParsetCalibration(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(description='Returns parameter summaries and graphs for a project/parset')
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        url-query:
            autofit: boolean - true loads the results from the autofit parameters
        """
        autofit = request.args.get('autofit', False)
        # calculation_type = 'autofit' if autofit else "calibration"
        # print "> Get calibration graphs for %s" % (calculation_type)
        return load_parset_graphs(project_id, parset_id, "calibration")

    @swagger.operation(description='Updates a parset and returns the graphs for a parset_id')
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        data-json:
            parameters: parset_summary
            which: list of graphs to generate
            autofit: boolean indicates to fetch the autofit version of the results
        """
        args = get_post_data_json()
        autofit = args.get('autofit', False)
        # calculation_type = 'autofit' if autofit else "calibration"
        parameters = args.get('parameters')
        which = args.get('which')
        # print "> Update calibration graphs for %s" % (calculation_type)
        return load_parset_graphs(
            project_id, parset_id, "calibration", which, parameters)


class ParsetAutofit(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Starts autofit task and returns calc_status')
    def post(self, project_id, parset_id):
        """
        POST: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        data-json:
            maxtime: int - number of seconds to run
        """
        from server.webapp.tasks import run_autofit, start_or_report_calculation
        maxtime = get_post_data_json().get('maxtime')
        calc_status = start_or_report_calculation(project_id, 'autofit-' + str(parset_id))
        if calc_status['status'] != "blocked":
            print "> Starting autofit for %s s" % maxtime
            run_autofit.delay(project_id, parset_id, maxtime)
            calc_status['maxtime'] = maxtime
        return calc_status

    @swagger.operation(summary='Returns the calc status for the current job')
    def get(self, project_id, parset_id):
        """
        GET: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        """
        from server.webapp.tasks import check_calculation_status
        print "> Checking calc state"
        calc_state = check_calculation_status(project_id, 'autofit-' + str(parset_id))
        pprint.pprint(calc_state, indent=2)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state


class ParsetUploadDownload(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Return a JSON file of the parameters")
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        """
        print("> Download JSON file of parset %s" % parset_id)
        parameters = load_parameters(project_id, parset_id)
        response = make_response(json.dumps(parameters, indent=2))
        response.headers["Content-Disposition"] = "attachment; filename=parset.json"
        return response

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        file-upload
        """
        par_json = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload parset JSON file '%s'" % par_json)
        parameters = json.load(open(par_json))
        save_parameters(project_id, parset_id, parameters)
        return load_parset_summaries(project_id)


class ResultsExport(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns result as downloadable .csv file")
    def get(self, result_id):
        """
        GET /api/results/<results_id>
        """
        load_dir, filename = load_result_csv(result_id)
        response = helpers.send_from_directory(load_dir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        return response

    @swagger.operation(summary="Returns graphs of a result_id, using which selectors")
    def post(self, result_id):
        """
        POST /api/results/<results_id>
        data-json:
            result_id: uuid of results
        """
        args = get_post_data_json()
        return load_result_mpld3_graphs(result_id, args.get('which'))

