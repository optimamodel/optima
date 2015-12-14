from flask.ext.login import login_required
from flask_restful import Resource, fields, marshal_with
from flask_restful_swagger import swagger

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
    def get(self):
        """
        Gives back project parameters (modifiable)
        """
        from server.webapp.parameters import parameters
        project_parameters = [
            p for p in parameters() if 'modifiable' in p and p['modifiable']]
        return project_parameters
