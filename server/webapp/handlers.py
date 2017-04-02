"""
handlers.py
===========

The webhandlers for project related API calls. This should only take functions
from dataio.py which refers to project ids, filenames, project names, and
JSON compatible summaries of PyOptima objects.

There should be no direct references to PyOptima objects, underlying file
structure or the database.
"""

import json
import os
import pprint

import yaml

import flask.json
from flask import helpers, current_app, request, flash, url_for, redirect, Blueprint, make_response
from flask_login import login_required, current_user
from flask_restful import Resource
from flask_restful_swagger import swagger
from flask_restful import Api
from werkzeug.utils import secure_filename

from . import parse, dataio
from .dataio import report_exception_decorator, verify_admin_request_decorator
from .parse import normalize_obj

# there's a circular import when celery is loaded so must use absolute import
import server.webapp.tasks


api_blueprint = Blueprint('api', __name__, static_folder='static')
api = swagger.docs(Api(api_blueprint), apiVersion='2.0')

# add hooks to handle UID's and datetime strings
@api.representation('application/json')
def output_json(data, code, headers=None):
    inner = json.dumps(data, cls=flask.json.JSONEncoder)
    resp = make_response(inner, code)
    resp.headers.extend(headers or {})
    return resp


def get_post_data_json():
    return normalize_obj(json.loads(request.data))


def get_upload_file(dirname):
    """
    Returns the server filename for an uploaded file,
    handled by the current flask request

    Args:
        dirname: directory on server to store the file
    """
    file = request.files['file']
    filename = secure_filename(file.filename)
    if not (os.path.exists(dirname)):
        os.makedirs(dirname)
    full_filename = os.path.join(dirname, filename)
    print("> Upload file '%s'" % filename)
    file.save(full_filename)

    return full_filename


def log_yaml(summary, title=None):
    if title:
        print(">> " + title)
    print(yaml.dump(summary))
    return summary



#############################################################################################
### PROJECTS
#############################################################################################

class ProjectsAll(Resource):
    method_decorators = [report_exception_decorator, verify_admin_request_decorator]

    @swagger.operation(summary="Returns list of project sumamaries (for admins)")
    def get(self):
        """
        Returns a list of:
            - creationTime: 2016-11-24 02:59:49.778765+00:00
              dataEnd: 2020.0
              dataStart: 2000.0
              dataUploadTime: 2016-11-24 13:59:48.899000
              hasEcon: false
              hasParset: true
              id: !!python/object:uuid.UUID {int: 21882366148703344914572624594908261043}
              isOptimizable: false
              name: !!python/unicode 'concentrated'
              populations:
                  - {age_from: 15, age_to: 49, female: true, male: false, name: Female sex workers,
                     short: FSW}
                  - ...
              updatedTime: 2016-11-24 02:59:49.778779+00:00
              userId: !!python/object:uuid.UUID {int: 296644019381267506816166667285382118442}
              version: 2.1.7
        """
        return {'projects': dataio.load_project_summaries()}

api.add_resource(ProjectsAll, '/api/project/all')


class Projects(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns list project summaries for current user")
    def get(self):
        return log_yaml({'projects': dataio.load_project_summaries(current_user.id)})

    @swagger.operation(summary="Create new project")
    def post(self):
        """
        data-json: project_summary
        """
        project_summary = get_post_data_json()
        project_id, dirname, basename = dataio.create_project_with_spreadsheet_download(
            current_user.id, project_summary)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.status_code = 201
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary="Bulk delete projects")
    def delete(self):
        """
        data-json: { projects: list of project_ids }
        """
        dataio.delete_projects(get_post_data_json()['projects'])
        return '', 204

api.add_resource(Projects, '/api/project')


class Project(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns a project summary')
    def get(self, project_id):
        return dataio.load_project_summary(project_id)

    @swagger.operation(summary='Update a project & download spreadsheet')
    def put(self, project_id):
        """
        data-json: project_summary
        """
        args = get_post_data_json()
        project_summary = args['project']
        is_spreadsheet = args['isSpreadsheet']
        is_delete_data = args['isDeleteData']
        print("> project" % project_summary)
        if is_spreadsheet:
            dirname, basename = dataio.update_project_followed_by_template_data_spreadsheet(
                project_id, project_summary, is_delete_data)
            print("> Project template: %s" % basename)
            response = helpers.send_from_directory(
                dirname,
                basename,
                as_attachment=True,
                attachment_filename=basename)
            response.headers['X-project-id'] = project_id
            return response
        else:
            dataio.update_project_from_summary(project_id, project_summary, is_delete_data)
            return '', 202

    @swagger.operation(summary='Delete project')
    def delete(self, project_id):
        dataio.delete_projects([project_id])
        return '', 204

api.add_resource(Project, '/api/project/<uuid:project_id>')


class ProjectData(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download .prj file for project')
    def get(self, project_id):
        dirname, filename = dataio.download_project(project_id)
        return helpers.send_from_directory(dirname, filename)

    @swagger.operation(summary='Update existing project with .prj')
    def post(self, project_id):
        """
        post-body: upload-file
        """
        uploaded_prj_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        dataio.update_project_from_prj(project_id, uploaded_prj_fname)
        reply = {
            'file': os.path.basename(uploaded_prj_fname),
            'result': 'Project %s is updated' % project_id,
        }
        return reply

api.add_resource(ProjectData, '/api/project/<uuid:project_id>/data')


class ProjectFromData(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Upload project with .prj/.xls')
    def post(self):
        """
        file-upload
        request-form:
            name: name of project
            xls: true
        """
        project_name = request.form.get('name')
        is_xls = request.form.get('xls', False)
        uploaded_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        if is_xls:
            project_id = dataio.create_project_from_spreadsheet(
                uploaded_fname, project_name, current_user.id)
        else:
            project_id = dataio.create_project_from_prj(
                uploaded_fname, project_name, current_user.id)
        response = {
            'file': os.path.basename(uploaded_fname),
            'name': project_name,
            'id': project_id
        }
        return response, 201

api.add_resource(ProjectFromData, '/api/project/data')


class ProjectCopy(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Copies project to a different name")
    def post(self, project_id):
        """
        data-json: to: new project name
        """
        args = get_post_data_json()
        new_project_name = args['to']

        copy_project_id = dataio.copy_project(project_id, new_project_name)
        print("> Copied project %s -> %s" % (project_id, copy_project_id))

        payload = {
            'project': project_id,
            'copy_id': copy_project_id
        }
        return payload

api.add_resource(ProjectCopy, '/api/project/<uuid:project_id>/copy')


class DefaultPrograms(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns default program summaries for program-set modal")
    def get(self, project_id):
        return {"programs": dataio.load_project_program_summaries(project_id)}

api.add_resource(DefaultPrograms, '/api/project/<uuid:project_id>/defaults')


class DefaultParameters(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns default programs for program-set modal")
    def get(self, project_id):
        return {'parameters': dataio.load_project_parameters(project_id)}

api.add_resource(DefaultParameters, '/api/project/<project_id>/parameters')


class DefaultPopulations(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns default populations for project management')
    def get(self):
        return {'populations': parse.get_default_populations()}

api.add_resource(DefaultPopulations, '/api/project/populations')


class Portfolio(Resource): # WARNING, should maybe be called something different since actually a project method
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download projects as .zip')
    def post(self):
        """
        data-json:
          projects: list of project ids
        """
        project_ids = get_post_data_json()['projects']
        print("> Portfolio requested for projects {}".format(project_ids))
        dirname, filename = dataio.load_zip_of_prj_files(project_ids)
        return helpers.send_from_directory(dirname, filename)

api.add_resource(Portfolio, '/api/project/portfolio')


class ProjectDataSpreadsheet(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Downloads template/uploaded data spreadsheet')
    def get(self, project_id):
        dirname, basename = dataio.load_data_spreadsheet(project_id, True)
        print("> Template created: %s" % basename)
        return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload completed data spreadsheet')
    def post(self, project_id):
        """
        file-upload
        """
        spreadsheet_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        dataio.update_project_from_data_spreadsheet(project_id, spreadsheet_fname)
        project_name = dataio.load_project_name(project_id)
        basename = os.path.basename(spreadsheet_fname)
        return '"%s" was successfully uploaded to project "%s"' % (basename, project_name)

api.add_resource(ProjectDataSpreadsheet, '/api/project/<uuid:project_id>/spreadsheet')

class SpreadsheetDownload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download spreadsheet data')
    def get(self, project_id):
        dirname, basename = dataio.load_data_spreadsheet(project_id, False)
        print("> Data xls created: %s" % basename)
        return helpers.send_from_directory(dirname, basename, as_attachment=True)

api.add_resource(SpreadsheetDownload, '/api/project/<uuid:project_id>/downloaddata')



#############################################################################################
### PORTFOLIOS
#############################################################################################

class ManagePortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns portfolio information")
    def get(self):
        return dataio.load_portfolio_summaries()

    @swagger.operation(summary="Create portfolio")
    def post(self):
        name = get_post_data_json()["name"]
        return dataio.create_portfolio(name)

api.add_resource(ManagePortfolio, '/api/portfolio')


class SavePortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Update portfolio")
    def post(self, portfolio_id):
        portfolio_summary = get_post_data_json()
        return dataio.save_portfolio_by_summary(portfolio_id, portfolio_summary)

    @swagger.operation(summary="Delete portfolio")
    def delete(self, portfolio_id):
        return dataio.delete_portfolio(portfolio_id)

api.add_resource(SavePortfolio, '/api/portfolio/<uuid:portfolio_id>')



class PortfolioData(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download .prt file for portfolio')
    def get(self, portfolio_id):
        dirname, filename = dataio.download_portfolio(portfolio_id)
        return helpers.send_from_directory(dirname, filename)

api.add_resource(PortfolioData, '/api/portfolio/<uuid:portfolio_id>/data')


class UploadPortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Upload portfolio')
    def post(self):
        """
        post-body: upload-file
        """
        uploaded_prt_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        portfolio = dataio.update_portfolio_from_prt(uploaded_prt_fname)
        reply = {
            'file': os.path.basename(uploaded_prt_fname),
            'portfolio': portfolio
        }
        return reply

api.add_resource(UploadPortfolio, '/api/portfolio/upload')




# WARNING, at the moment the upload is halfway in between upload new portfolio and update existing portfolio
#class PortfolioFromData(Resource):
#    method_decorators = [report_exception_decorator, login_required]
#
#    @swagger.operation(summary='Upload project with .prj/.xls')
#    def post(self):
#        """
#        file-upload
#        request-form:
#            name: name of project
#            xls: true
#        """
#        project_name = request.form.get('name')
#        is_xls = request.form.get('xls', False)
#        uploaded_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
#        if is_xls:
#            project_id = dataio.create_project_from_spreadsheet(
#                uploaded_fname, project_name, current_user.id)
#        else:
#            project_id = dataio.create_project_from_prj(
#                uploaded_fname, project_name, current_user.id)
#        response = {
#            'file': os.path.basename(uploaded_fname),
#            'name': project_name,
#            'id': project_id
#        }
#        return response, 201
#
#api.add_resource(PortfolioFromData, '/api/portfolio/data')



class DeletePortfolioProject(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Delete project in a portfolio")
    def delete(self, portfolio_id, project_id):
        return dataio.delete_portfolio_project(portfolio_id, project_id)

api.add_resource(DeletePortfolioProject, '/api/portfolio/<portfolio_id>/project/<project_id>')


class CalculatePortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns portfolio information")
    def post(self, portfolio_id):
        maxtime = int(get_post_data_json().get('maxtime'))
        print("> Run BOC %s" % (portfolio_id))
        return server.webapp.tasks.launch_boc(portfolio_id, maxtime)

api.add_resource(CalculatePortfolio, '/api/portfolio/<uuid:portfolio_id>/calculate')


class MinimizePortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Starts portfolio minimization")
    def post(self, portfolio_id):
        maxtime = int(get_post_data_json().get('maxtime'))
        return server.webapp.tasks.launch_miminize_portfolio(portfolio_id, maxtime)

api.add_resource(MinimizePortfolio, '/api/portfolio/<uuid:portfolio_id>/minimize')


class ExportPortfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download .xlsx file of portfolio results')
    def get(self, portfolio_id):
        dirname, filename = dataio.export_portfolio(portfolio_id)
        return helpers.send_from_directory(dirname, filename)

api.add_resource(ExportPortfolio, '/api/portfolio/<uuid:portfolio_id>/export')


class RegionTemplate(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Make portfolio region template")
    def post(self):
        args = get_post_data_json()
        project_id = args['projectId']
        n_region = int(args['nRegion'])
        year = int(args['year'])
        dirname, basename = dataio.make_region_template_spreadsheet(project_id, n_region, year)
        print("> Got spreadsheet now download")
        return helpers.send_from_directory(dirname, basename)

api.add_resource(RegionTemplate, '/api/region')


class SpawnRegion(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Spawn projects with region spreadsheet")
    def post(self):
        """
        file-upload
        """
        project_id = request.form.get('projectId')
        spreadsheet_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        project_summaries = dataio.load_project_summaries(current_user.id)
        project_names = [p['name'] for p in project_summaries]
        prj_names = dataio.make_region_projects(project_id, spreadsheet_fname, project_names)
        return prj_names

api.add_resource(SpawnRegion, '/api/spawnregion')


class TaskChecker(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Poll task')
    def get(self, pyobject_id, work_type):
        return server.webapp.tasks.check_task(pyobject_id, work_type)

    @swagger.operation(summary="Deletes a task")
    def delete(self, pyobject_id, work_type):
        return server.webapp.tasks.delete_task(pyobject_id, work_type)

api.add_resource(TaskChecker, '/api/task/<uuid:pyobject_id>/type/<work_type>')


class ResultsReady(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download .xlsx file of portfolio results')
    def get(self, portfolio_id):
        resultready = dataio.portfolio_results_ready(portfolio_id)
        return not(resultready) # WARNING, not!

api.add_resource(ResultsReady, '/api/portfolio/<uuid:portfolio_id>/ready')





#############################################################################################
### PARSETS
#############################################################################################

class Parsets(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns a list of parset summaries')
    def get(self, project_id):
        print("> Load parsets")
        return {"parsets": dataio.load_parset_summaries(project_id)}

    @swagger.operation(summary='Copy/create a parset, and returns a list of parset summaries')
    def post(self, project_id):
        """
        data-json:
            name: name of parset
            parset_id: id of parset (copy) or null (create
        """
        args = get_post_data_json()
        new_parset_name = args['name']
        parset_id = args.get('parset_id')

        if not parset_id:
            print("> Create parset " + new_parset_name)
            dataio.create_parset(project_id, new_parset_name)
        else:
            print("> Copy parset " + new_parset_name)
            dataio.copy_parset(project_id, parset_id, new_parset_name)

        return dataio.load_parset_summaries(project_id)

api.add_resource(Parsets, '/api/project/<uuid:project_id>/parsets')


class ParsetRenameDelete(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Delete parset with parset_id.')
    def delete(self, project_id, parset_id):
        print("> Delete parset '%s'" % parset_id)
        dataio.delete_parset(project_id, parset_id)
        return '', 204

    @swagger.operation(summary='Rename parset and returns a list of parset summaries')
    def put(self, project_id, parset_id):
        name = get_post_data_json()['name']
        print("> Rename parset '%s'" % name)
        dataio.rename_parset(project_id, parset_id, name)
        return dataio.load_parset_summaries(project_id)

api.add_resource(ParsetRenameDelete, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>')


class ParsetRefresh(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Refresh parset')
    def post(self, project_id, parset_id):
        dataio.refresh_parset(project_id, parset_id)
        return dataio.load_parset_graphs(project_id, parset_id, "calibration")

api.add_resource(ParsetRefresh, '/api/project/<uuid:project_id>/refreshparset/<uuid:parset_id>')


class ParsetCalibration(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns parameter summaries and graphs for a project/parset')
    def get(self, project_id, parset_id):
        return dataio.load_parset_graphs(project_id, parset_id, "calibration")

    @swagger.operation(summary='Updates a parset and returns the graphs for a parset_id')
    def post(self, project_id, parset_id):
        """
        data-json:
            parameters: parset_summary
            which: list of graphs to generate
            autofit: boolean indicates to fetch the autofit version of the results
        """
        args = get_post_data_json()
        parameters = args.get('parameters', None)
        which = args.get('which')
        startYear = args.get('startYear', None)
        if startYear is not None:
            startYear = int(startYear)
        endYear = args.get('endYear', None)
        if endYear is not None:
            endYear = int(endYear)
        return dataio.load_parset_graphs(
            project_id, parset_id, "calibration", which, parameters,
            startYear=startYear, endYear=endYear)

api.add_resource(ParsetCalibration, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration')


class ParsetAutofit(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Starts autofit task and returns calc_status')
    def post(self, project_id, parset_id):
        """
        data-json:
            maxtime: int - number of seconds to run
        """
        maxtime = get_post_data_json().get('maxtime')
        return server.webapp.tasks.launch_autofit(project_id, parset_id, maxtime)

    @swagger.operation(summary='Returns the calc status for the current job')
    def get(self, project_id, parset_id):
        print "> Checking calc state"
        calc_state = server.webapp.tasks.check_calculation_status(
            project_id, 'autofit-' + str(parset_id))
        pprint.pprint(calc_state, indent=2)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state

api.add_resource(ParsetAutofit, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration')


class ParsetUploadDownload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Return a JSON file of the parameters")
    def get(self, project_id, parset_id):
        print("> Download JSON file of parset %s" % parset_id)
        parameters = dataio.load_parameters(project_id, parset_id)
        response = make_response(json.dumps(parameters, indent=2))
        response.headers["Content-Disposition"] = "attachment; filename=parset.json"
        return response

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, parset_id):
        """
        file-upload
        """
        par_json = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload parset JSON file '%s'" % par_json)
        parameters = json.load(open(par_json))
        dataio.save_parameters(project_id, parset_id, parameters)
        return dataio.load_parset_summaries(project_id)

api.add_resource(ParsetUploadDownload, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data')




#############################################################################################
### RESULTS
#############################################################################################

class ResultsExport(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns result as downloadable .csv file")
    def get(self, result_id):
        load_dir, filename = dataio.load_result_csv(result_id)
        response = helpers.send_from_directory(load_dir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        return response

    @swagger.operation(summary="Returns graphs of a result_id, using which selectors")
    def post(self, result_id):
        """
        data-json:
            result_id: uuid of results
        """
        args = get_post_data_json()
        return dataio.load_result_mpld3_graphs(result_id, args.get('which'), args.get('zoom'))

api.add_resource(ResultsExport, '/api/results/<uuid:result_id>')



#############################################################################################
### PROGSETS
#############################################################################################

class Progsets(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Return progset summaries')
    def get(self, project_id):
        return dataio.load_progset_summaries(project_id)

    @swagger.operation(summary='Create a new progset')
    def post(self, project_id):
        """
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return dataio.create_progset(project_id, progset_summary)

api.add_resource(Progsets, '/api/project/<uuid:project_id>/progsets')


class Progset(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Update progset with the given id.')
    def put(self, project_id, progset_id):
        """
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return dataio.save_progset(project_id, progset_id, progset_summary)

    @swagger.operation(summary='Delete progset with the given id.')
    def delete(self, project_id, progset_id):
        dataio.delete_progset(project_id, progset_id)
        return '', 204

    @swagger.operation(summary='Copy progset with the given id.')
    def post(self, project_id, progset_id):
        """
        data-json: name:
        """
        new_name = get_post_data_json()['name']
        return dataio.copy_progset(project_id, progset_id, new_name)

api.add_resource(Progset, '/api/project/<uuid:project_id>/progset/<uuid:progset_id>')


class ProgsetRename(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Update progset with the given id.')
    def put(self, project_id, progset_id):
        """
        data-json: progset_summary
        """
        new_name = get_post_data_json()['newName']
        return dataio.rename_progset(project_id, progset_id, new_name)

api.add_resource(ProgsetRename, '/api/project/<uuid:project_id>/progset/<uuid:progset_id>/rename')


class ProgsetUploadDownload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, progset_id):
        """
        file-upload
        """
        json_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload progset JSON file '%s'" % json_fname)
        progset_summary = json.load(open(json_fname))
        return dataio.upload_progset(project_id, progset_id, progset_summary)

api.add_resource(ProgsetUploadDownload, '/api/project/<uuid:project_id>/progset/<uuid:progset_id>/data')


class ProgsetParameters(Resource):

    @swagger.operation(summary='Return parameters for progset outcome page')
    def get(self, project_id, progset_id, parset_id):
        return dataio.load_parameters_from_progset_parset(project_id, progset_id, parset_id)

api.add_resource(ProgsetParameters,
     '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/parameters/<uuid:parset_id>')


class ProgsetOutcomes(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns list of outcomes for a progset')
    def get(self, project_id, progset_id):
        return dataio.load_progset_outcome_summaries(project_id, progset_id)

    @swagger.operation(summary='Saves the outcomes of a given progset, used in outcome page')
    def put(self, project_id, progset_id):
        outcome_summaries = get_post_data_json()
        return dataio.save_outcome_summaries(project_id, progset_id, outcome_summaries)

api.add_resource(ProgsetOutcomes, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects')


class Program(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Saves a program summary to project')
    def post(self, project_id, progset_id):
        """
        data-json: programs: program_summary
        """
        program_summary = get_post_data_json()['program']
        dataio.save_program(project_id, progset_id, program_summary)
        return 204

api.add_resource(Program, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program')


class ProgramPopSizes(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Return estimated popsize for a given program and parset')
    def get(self, project_id, progset_id, program_id, parset_id):
        payload = dataio.load_target_popsizes(project_id, parset_id, progset_id, program_id)
        return payload, 201

api.add_resource(ProgramPopSizes,
    '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program/<uuid:program_id>/parset/<uuid:parset_id>/popsizes')


class ProgramCostcovGraph(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns an mpld3 dict that can be displayed with the mpld3 plugin')
    def get(self, project_id, progset_id, program_id):
        """
        url-args:
            t: comma-separated list of years (>= startyear in data)
            parset_id: parset ID of project (not related to program targetpars)
            caption: string to display in graph
            xupperlim: maximum dollar shown
            perperson: cost per person shown as data point
        """
        args = request.args

        parset_id = args['parset_id']

        try:
            t = map(int, args['t'].split(','))
        except ValueError:
            t = None
        if t is None:
            return {}

        print '>>>> Generating plot...'
        return dataio.load_costcov_graph(
            project_id, progset_id, program_id, parset_id, t)

api.add_resource(ProgramCostcovGraph,
    '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage/graph')




#############################################################################################
### SCENARIOS
#############################################################################################


class Scenarios(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='get scenarios for a project')
    def get(self, project_id):
        return dataio.load_scenario_summaries(project_id)

    @swagger.operation(summary='update scenarios; returns scenarios so client-side can check')
    def put(self, project_id):
        """
        data-josn: scenarios: scenario_summaries
        """
        data = get_post_data_json()
        scenario_summaries = data['scenarios']
        return dataio.save_scenario_summaries(project_id, scenario_summaries)

api.add_resource(Scenarios, '/api/project/<uuid:project_id>/scenarios')


class ScenarioSimulationGraphs(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Run scenarios and returns the graphs')
    def post(self, project_id):
        """
        post-json:
            isRun: True or False
            start: int -or- None
            end: int -or- None
        """
        args = get_post_data_json()
        return dataio.make_scenarios_graphs(
            project_id,
            which=args.get('which', None),
            is_run=args.get('isRun', False),
            zoom=args.get('zoom', None), # BOSCO MODIFY
            startYear=args.get('start', None),
            endYear=args.get('end', None))

api.add_resource(ScenarioSimulationGraphs, '/api/project/<uuid:project_id>/scenarios/results')


class DefaultParStartVal(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Get default value for parameter')
    def post(self):
        """
        post-json:
          projectId: project.id,
          parsetId: $scope.scenario.parset_id,
          parShort: newScenPar.name,
          pop: newScenPar.for,
          year: newScenPar.startYear
        """
        args = get_post_data_json()
        return dataio.load_startval_for_parameter(
            args['projectId'],
            args['parsetId'],
            args['parShort'],
            args['pop'],
            args['year'])

api.add_resource(DefaultParStartVal, '/api/startval')



#############################################################################################
### OPTIMIZATIONS
#############################################################################################

class Optimizations(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns list of optimization summaries")
    def get(self, project_id):
        return dataio.load_optimization_summaries(project_id)

    @swagger.operation(summary="Uploads project with optimization summaries, and returns summaries")
    def post(self, project_id):
        """
        data-json: optimization_summaries
        """
        optimization_summaries = get_post_data_json()
        return dataio.save_optimization_summaries(project_id, optimization_summaries)

api.add_resource(Optimizations, '/api/project/<uuid:project_id>/optimizations')


class OptimizationUpload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Uploads json of optimization summary")
    def post(self, project_id, optimization_id):
        """
        data-json: optimization_summary
        """
        optim_json = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        optim_summary = json.load(open(optim_json))
        return dataio.upload_optimization_summary(project_id, optimization_id, optim_summary)

api.add_resource(OptimizationUpload, '/api/project/<uuid:project_id>/optimization/<uuid:optimization_id>/upload')


class OptimizationCalculation(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Launch optimization calculation')
    def post(self, project_id, optimization_id):
        """
        data-json: maxtime: time to run in int
        """
        args = get_post_data_json()
        maxtime = args.get('maxtime')
        return server.webapp.tasks.launch_optimization(project_id, optimization_id, int(maxtime)), 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        return server.webapp.tasks.check_optimization(project_id, optimization_id)

api.add_resource(OptimizationCalculation, '/api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results')


class OptimizationGraph(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Provides optimization graph for the given project')
    def post(self, project_id, optimization_id):
        """
        post-json: which: list of graphs to display
        """
        which = get_post_data_json().get('which')
        return dataio.load_optimization_graphs(project_id, optimization_id, which)

api.add_resource(OptimizationGraph, '/api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph')


class AnyOptimizable(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Gets whether the project contains at least one optimizable progset')
    def get(self, project_id):
        return dataio.any_optimizable(project_id)

api.add_resource(AnyOptimizable, '/api/project/<uuid:project_id>/optimizable')


#############################################################################################
### USERS
#############################################################################################


class User(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='List users')
    @verify_admin_request_decorator
    def get(self):
        return {'users': dataio.get_user_summaries()}

    @swagger.operation(summary='Create a user')
    def post(self):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.create_user(args), 201

api.add_resource(User, '/api/user')


class UserDetail(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='Delete a user')
    @verify_admin_request_decorator
    def delete(self, user_id):
        dataio.delete_user(user_id)
        return '', 204

    @swagger.operation(summary='Update a user')
    def put(self, user_id):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.update_user(user_id, args)

api.add_resource(UserDetail, '/api/user/<uuid:user_id>')


class CurrentUser(Resource):
    method_decorators = [login_required, report_exception_decorator]

    @swagger.operation(summary='Return the current user')
    def get(self):
        return dataio.parse_user_record(current_user)

api.add_resource(CurrentUser, '/api/user/current')


class UserLogin(Resource):

    @swagger.operation(summary='Try to log a user in',)
    @report_exception_decorator
    def post(self):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.do_login_user(args)

api.add_resource(UserLogin, '/api/user/login')


class UserLogout(Resource):

    @swagger.operation(summary='Log the current user out')
    @report_exception_decorator
    def get(self):
        dataio.do_logout_current_user()
        flash(u'You have been signed out')
        return redirect(url_for("site"))

api.add_resource(UserLogout, '/api/user/logout')


