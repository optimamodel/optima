from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, abort
from flask_restful_swagger import swagger

from server.webapp.inputs import SubParser
from server.webapp.utils import load_project, RequestParser
from server.webapp.exceptions import ParsetDoesNotExist

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
        project_entry = load_project(project_id, raise_exception=True)

        reply = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id).all()
        return [item.hydrate() for item in reply]


class ParsetsDetail(Resource):
    """
    Single Parset.
    """
    class_decorators = [login_required]

    @swagger.operation(
        description='Delete parset with the given id.',
        notes="""
            if parset exists, delete it
            if parset does not exist, returns an error.
        """
    )
    def delete(self, project_id, parset_id):

        current_app.logger.debug("/api/project/{}/parsets/{}".format(project_id, parset_id))
        project_entry = load_project(project_id, raise_exception=True)

        parset = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id, id=parset_id).first()
        if parset is None:
            raise ParsetDoesNotExist(id=parset_id)

        # Is this how we should check for default parset?
        if parset.name == 'Default':
            abort(403)

        db.session.query(ParsetsDb).filter_by(id=parset_id).delete()
        db.session.commit()

        return '', 204
