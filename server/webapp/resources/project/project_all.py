from flask.ext.login import current_user
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import fields
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.resources.project.fields import project_data_list_all_fields
from server.webapp.utils import verify_admin_request
from server.webapp.dbmodels import ProjectDb

result_fields = {
    fields.List(fields.Nested(project_data_list_all_fields))
}


class ProjectAll(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='List All Project as an Admin'
    )
    @marshal_with(result_fields)
    @login_required
    @verify_admin_request
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
                    'data_upload_time': project_entry.data_upload_time(),
                    'user_id': project_entry.user_id
                }
                projects_data.append(project_data)
        return projects_data
