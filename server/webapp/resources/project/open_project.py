from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.dbmodels import ProjectDb
from server.webapp.exceptions import ProjectNotFound
from server.webapp.utils import project_exists


class OpenProject(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @marshal_with(ProjectDb.resource_fields)
    @login_required
    def get(self, project_id):
        """
        Opens the project with the given ID.
        If the project exists, notifies the user about success.
        expects project ID,
        todo: only if it can be found
        """
        proj_exists = project_exists(project_id)
        if not proj_exists:
            raise ProjectNotFound(id=project_id)
        else:
            return project_exists
