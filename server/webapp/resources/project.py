"""
project.py
==========

The webhandlers for project related API calls. This should only take functions
from dataio.py which refers to project ids, filenames, project names, and
JSON compatible summaries of PyOptima objects.

There should be no direct references to PyOptima objects, underlying file
structure or the database.
"""
import os

from flask import current_app, helpers, request, Response
from flask.ext.login import current_user, login_required
from flask_restful import Resource
from flask_restful_swagger import swagger

from server.webapp.dataio import load_project_summary, \
    update_project_followed_by_template_data_spreadsheet, \
    load_project_parameters, load_project_program_summaries, \
    load_project_summaries, create_project_with_spreadsheet_download, \
    delete_projects, copy_project, create_project_from_prj, \
    download_project, update_project_from_prj, \
    load_data_spreadsheet_binary, load_template_data_spreadsheet, \
    update_project_from_data_spreadsheet, load_zip_of_prj_files, \
    update_project_from_econ_spreadsheet, load_project_name, delete_econ
from server.webapp.parse import get_default_populations
from server.webapp.resources.common import report_exception, verify_admin_request
from server.webapp.utils import get_post_data_json, get_upload_file


class ProjectsAll(Resource):
    method_decorators = [report_exception, verify_admin_request]

    @swagger.operation(summary="Returns list of project sumamaries (for admins)")
    def get(self):
        """
        GET /api/project/all
        """
        return {'projects': load_project_summaries()}


class Projects(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns list project summaries for current user")
    def get(self):
        """
        GET /api/project
        """
        return {'projects': load_project_summaries(current_user.id)}

    @swagger.operation(summary="Create new project")
    def post(self):
        """
        POST /api/project
        data-json: project_summary
        """
        project_summary = get_post_data_json()
        project_id, dirname, basename = create_project_with_spreadsheet_download(
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
        DELETE /api/project
        data-json: { projects: list of project_ids }
        """
        delete_projects(get_post_data_json()['projects'])
        return '', 204


class Project(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Returns a project summary')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>
        """
        return load_project_summary(project_id)

    @swagger.operation(summary='Update a project')
    def put(self, project_id):
        """
        PUT /api/project/<uuid:project_id>
        data-json: project_summary
        """
        project_summary = get_post_data_json()
        dirname, basename = update_project_followed_by_template_data_spreadsheet(
            project_id, project_summary)
        print("> Project template: %s" % basename)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary='Delete project')
    def delete(self, project_id):
        """
        DELETE /api/project/<uuid:project_id>
        """
        delete_projects([project_id])
        return '', 204


class ProjectData(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Download .prj file for project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/data
        """
        print("> Download .prj for project %s" % project_id)
        dirname, filename = download_project(project_id)
        return helpers.send_from_directory(dirname, filename)

    @swagger.operation(summary='Update existing project with .prj')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/data
        """
        uploaded_prj_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        update_project_from_prj(project_id, uploaded_prj_fname)
        reply = {
            'file': os.path.basename(uploaded_prj_fname),
            'result': 'Project %s is updated' % project_id,
        }
        return reply


class ProjectFromData(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Upload project with .prj')
    def post(self):
        """
        POST /api/project/data
        form: name: name of project
        file: upload
        """
        project_name = request.form.get('name')
        uploaded_prj_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        project_id = create_project_from_prj(
            uploaded_prj_fname, project_name, current_user.id)
        response = {
            'file': os.path.basename(uploaded_prj_fname),
            'name': project_name,
            'id': project_id
        }
        return response, 201


class ProjectCopy(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Copies project to a different name")
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/copy
        data-json:
            to: new project name
        """
        args = get_post_data_json()
        new_project_name = args['to']

        copy_project_id = copy_project(project_id, new_project_name)
        print("> Copied project %s -> %s" % (project_id, copy_project_id))

        payload = {
            'project': project_id,
            'copy_id': copy_project_id
        }
        return payload


class DefaultPrograms(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns default program summaries for program-set modal")
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/defaults
        """
        return {"programs": load_project_program_summaries(project_id)}


class DefaultParameters(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns default programs for program-set modal")
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parameters
        """
        return {'parameters': load_project_parameters(project_id)}


class DefaultPopulations(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Returns default populations for project management')
    def get(self):
        """
        GET /api/project/populations
        """
        return {'populations': get_default_populations()}


class Portfolio(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Download projects as .zip')
    def post(self):
        """
        POST /api/project/portfolio
        data-json:
            projects: list of project ids
        """
        project_ids = get_post_data_json()['projects']
        print("> Portfolio requested for projects {}".format(project_ids))
        dirname, filename = load_zip_of_prj_files(project_ids)
        return helpers.send_from_directory(dirname, filename)


class ProjectDataSpreadsheet(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Downloads template/uploaded data spreadsheet')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/spreadsheet
        """
        fname, binary = load_data_spreadsheet_binary(project_id)
        if binary is not None:
            print("> Download previously-uploaded xls as %s" % fname)
            return Response(
                binary,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + fname
                })
        else:
            dirname, basename = load_template_data_spreadsheet(project_id)
            print("> Template created: %s" % basename)
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload completed data spreadsheet')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/spreadsheet
        file-upload
        """
        spreadsheet_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        update_project_from_data_spreadsheet(project_id, spreadsheet_fname)
        reply = {
            'file': os.path.basename(spreadsheet_fname),
            'result': 'Project %s is updated' % project_id
        }
        return reply


class ProjectEcon(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Downloads template/uploaded econ spreadsheet')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/economics
        """
        fname, binary = load_econ_spreadsheet_binary(project_id)
        if binary is not None:
            print("> Download previously-uploaded xls as %s" % fname)
            return Response(
                binary,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + fname
                })
        else:
            dirname, basename = load_template_econ_spreadsheet(project_id)
            print("> Template created: %s" % basename)
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload the economics data spreadsheet')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/economics
        file-upload
        """
        econ_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        server_fname = update_project_from_econ_spreadsheet(project_id, econ_fname)
        reply = {
            'file': os.path.basename(server_fname),
            'success': 'Econ spreadsheet uploaded for project %s' % load_project_name(project_id),
        }
        return reply

    @swagger.operation(summary='Removes economics data from project')
    def delete(self, project_id):
        """
        DELETE /api/project/<uuid:project_id>/economics
        """
        delete_econ(project_id)


