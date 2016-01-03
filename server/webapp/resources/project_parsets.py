from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger

from server.webapp.inputs import SubParser
from server.webapp.utils import load_project, RequestParser
from server.webapp.exceptions import RecordDoesNotExist, ProjectDoesNotExist

from server.webapp.dbconn import db

from server.webapp.dbmodels import ParsetsDb


class Parsets(Resource):
    """
    Parsets for a given project.
    """
    class_decorators = [login_required]

    @swagger.operation(
        description='Download parsets for the project with the given id.',
        notes="""
            if project exists, returns parsets for it
            if project does not exist, returns an error.
        """,
        responseClass=ParsetsDb.__name__
    )
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/parsets" % str(project_id))
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id).all()
        return [item.hydrate() for item in reply]
