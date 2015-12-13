from flask.ext.login import login_required
from flask_restful import Resource
from flask import request
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.dbmodels import ProjectDb
from server.webapp.exceptions import ProjectNotFound
from server.webapp.utils import load_project
from server.webapp.resources.project.fields import project_data_fields


class ProjectInfo(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @marshal_with(project_data_fields)
    @login_required
    def get(self, project_id):
        """
        Returns information of the requested project.
        (Including status of the model)

        Returns:
            A jsonified project dictionary accessible to the current user.
            In case of an anonymous user an object an error response
            is returned.
        """
        # see if there is matching project
        project_entry = load_project(request.project_id)
        if project_entry is None:
            raise ProjectNotFound(id=request.project_id)
        payload = {
            'id': project_entry.id,
            'name': project_entry.name,
            'dataStart': project_entry.datastart,
            'dataEnd': project_entry.dataend,
            'populations': project_entry.populations,
            'creation_time': project_entry.created,
            'updated_time': project_entry.updated,
            'data_upload_time': project_entry.data_upload_time(),
            'has_data': project_entry.has_data()
        }
        return payload
