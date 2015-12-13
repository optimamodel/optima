from datetime import datetime
from flask import current_app
from flask import helpers
from flask import json
from flask import request
from flask.ext.login import current_user
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful_swagger import swagger
from optima.makespreadsheet import default_dataend
from optima.makespreadsheet import default_datastart
from optima.makespreadsheet import makespreadsheet
from optima.project import version
from server.webapp.dataio import TEMPLATEDIR
from server.webapp.dataio import templatepath
from server.webapp.dataio import upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb
from server.webapp.exceptions import ParamsMissing
from werkzeug.utils import secure_filename


class CreateProject(Resource):

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
