from flask.ext.login import login_required
from flask_restful import Resource, fields, marshal_with
from flask_restful_swagger import swagger

from server.webapp.fields import Json
from server.webapp.utils import report_exception


result_fields = {
    "calibration": fields.Boolean,
    "dim": fields.Integer,
    "input_keys": fields.Raw,
    "keys": fields.Raw,
    "modifiable": fields.Boolean,
    "name": fields.String,
    "page": fields.String,
}


class Parameters(Resource):
    @swagger.operation(
        summary="List default parameters"
    )
    @marshal_with(result_fields, envelope='parameters')
    @login_required
    @report_exception
    def get(self):
        """
        Gives back project parameters (modifiable)
        """
        from server.webapp.parameters import parameters
        project_parameters = [
            p for p in parameters() if 'modifiable' in p and p['modifiable']]
        return project_parameters


populations_fields = {
    "active": fields.Boolean,
    "age_from": fields.Integer,
    "age_to": fields.Integer,
    "female": fields.Boolean,
    "male": fields.Boolean,
    "name": fields.String,
    "short_name": fields.String,
}


class Populations(Resource):

    @swagger.operation(
        summary='Gives back default populations'
    )
    @marshal_with(populations_fields, envelope='populations')
    @login_required
    @report_exception
    def get(self, project_id):
        from server.webapp.populations import populations

        populations = populations()
        for p in populations:
            p['active'] = False
        return populations
