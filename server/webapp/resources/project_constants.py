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


predefined_fields = {
    "programs": Json,
    "populations": Json,
    "categories": Json
}


class Predefined(Resource):

    @swagger.operation(
        summary='Gives back default populations and programs'
    )
    @marshal_with(predefined_fields)
    @login_required
    @report_exception
    def get(self):
        from server.webapp.programs import get_default_programs, program_categories
        from server.webapp.populations import populations

        programs = get_default_programs()
        populations = populations()
        program_categories = program_categories()
        for p in populations:
            p['active'] = False
        for p in programs:
            p['active'] = False
#            new_parameters = [
#                dict([
#                    ('value', parameter),
#                    ('active', True)]) for parameter in p['parameters']]
#            if new_parameters:
#                p['parameters'] = new_parameters
        payload = {
            "programs": programs,
            "populations": populations,
            "categories": program_categories
        }
        return payload
