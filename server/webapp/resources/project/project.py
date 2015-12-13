from datetime import datetime
from flask import current_app
from flask import helpers
from flask import json
from flask import request
from flask.ext.login import current_user
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import fields
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from optima.makespreadsheet import default_dataend
from optima.makespreadsheet import default_datastart
from optima.makespreadsheet import makespreadsheet
from optima.project import version
from server.webapp.dataio import TEMPLATEDIR
from server.webapp.dataio import templatepath
from server.webapp.dataio import upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb
from server.webapp.dbmodels import ProjectDataDb
from server.webapp.dbmodels import ProjectDb
from server.webapp.dbmodels import ResultsDb
from server.webapp.dbmodels import WorkLogDb
from server.webapp.dbmodels import WorkingProjectDb
from server.webapp.exceptions import ParamsMissing
from server.webapp.resources.project.fields import project_data_list_fields
from server.webapp.utils import load_project
from werkzeug.utils import secure_filename
from server.webapp.utils import delete_spreadsheet

result_fields = {
    fields.List(fields.Nested(project_data_list_fields))
}


class Project(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open all user;s project Project'
    )
    @marshal_with(result_fields)
    @login_required
    def get(self):
        """
        Returns the list of existing projects from db.

        Returns:
            A jsonified list of project dictionaries if the user is logged in.
            In case of an anonymous user an empty list will be returned.

        """
        projects_data = []
        # Get current user
        if not current_user.is_anonymous():

            # Get projects for all users, if the user is admin
            projects = ProjectDb.query.all()
            for project_entry in projects:
                project_data = {
                    'id': project_entry.id,
                    'name': project_entry.name,
                    'dataStart': project_entry.datastart,
                    'dataEnd': project_entry.dataend,
                    'populations': project_entry.populations,
                    'creation_time': project_entry.created,
                    'updated_time': project_entry.updated,
                    'data_upload_time': project_entry.data_upload_time()
                }
                projects_data.append(project_data)
        return projects_data

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Create a new Project'
    )
    @login_required
    def post(self):
        """
        Creates the project with the given name and provided parameters.
        Result: on the backend, new project is stored,
        spreadsheet with specified name and parameters given back to the user.
        expects json with the following arguments (see example):
        {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}

        """
        current_app.logger.info(
            "create request: {} {}".format(request, request.data))
        payload = json.loads(request.data)
        data = payload.get('params')
        if not data:
            raise ParamsMissing('params')

        project_name = data.get('name')
        if not project_name:
            raise ParamsMissing('name')

        user_id = current_user.id

        project_name = secure_filename(data.get('name'))
        current_app.logger.debug(
            "createProject %s for user %s" % (
                project_name, current_user.email))
        current_app.logger.debug("createProject data: %s" % data)

        makeproject_args = {"projectname": project_name, "savetofile": False}
        makeproject_args['datastart'] = data.get(
            'datastart', default_datastart)
        makeproject_args['dataend'] = data.get('dataend', default_dataend)
        makeproject_args['pops'] = data.get('populations')

        current_app.logger.debug("createProject(%s)" % makeproject_args)

        # create new project
        current_app.logger.debug("Creating new project %s by user %s:%s" % (
            project_name, user_id, current_user.email))
        project_entry = ProjectDb(
            project_name,
            user_id,
            makeproject_args['datastart'],
            makeproject_args['dataend'],
            makeproject_args['pops'],
            version=version,
            created=datetime.utcnow())
        current_app.logger.debug(
            'Creating new project: %s' % project_entry.name)

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project_entry.name, project_entry.user_id))
        db.session.add(project_entry)
        db.session.commit()
        new_project_template = project_name

        path = templatepath(project_name)
        makespreadsheet(
            path,
            pops=makeproject_args['pops'],
            datastart=makeproject_args['datastart'],
            dataend=makeproject_args['dataend'])

        current_app.logger.debug(
            "new_project_template: %s" % new_project_template)
        (dirname, basename) = (
            upload_dir_user(TEMPLATEDIR), new_project_template)
        response = helpers.send_from_directory(dirname, basename)
        response.headers['X-project-id'] = project_entry.id
        return response

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Create a new Project'
    )
    @login_required
    def delete(self, project_id):
        """
        Deletes the given project (and eventually, corresponding excel files)
        """
        current_app.logger.debug("deleteProject %s" % project_id)
        # only loads the project if current user is either owner or admin
        project_entry = load_project(project_id)
        project_name = None
        user_id = current_user.id

        if project_entry is not None:
            user_id = project_entry.user_id
            project_name = project_entry.name
            str_project_id = str(project_entry.id)
            # delete all relevant entries explicitly
            db.session.query(WorkLogDb).filter_by(
                project_id=str_project_id).delete()
            db.session.query(ProjectDataDb).filter_by(
                id=str_project_id).delete()
            db.session.query(WorkingProjectDb).filter_by(
                id=str_project_id).delete()
            db.session.query(ResultsDb).filter_by(
                project_id=str_project_id).delete()
            db.session.query(ParsetsDb).filter_by(
                project_id=str_project_id).delete()
            db.session.query(ProjectDb).filter_by(id=str_project_id).delete()
        db.session.commit()
        current_app.logger.debug(
            "project %s is deleted by user %s" % (project_id, current_user.id))
        delete_spreadsheet(project_name)
        if (user_id != current_user.id):
            delete_spreadsheet(project_name, user_id)
        current_app.logger.debug("spreadsheets for %s deleted" % project_name)

        return '', 200
