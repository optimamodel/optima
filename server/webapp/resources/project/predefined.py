from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.resources.project.fields import predefined_fields


class Predefined(Resource):
    @swagger.operation(
        responseClass=None,
        summary='Gives back default populations and programs'
    )
    @marshal_with(predefined_fields)
    @login_required
    def get(self):
        """
        Gives back default populations and programs
        """
        from programs import programs, program_categories
        from populations import populations
        programs = programs()
        populations = populations()
        program_categories = program_categories()
        for p in populations:
            p['active'] = False
        for p in programs:
            p['active'] = False
            new_parameters = [
                dict([
                        ('value', parameter),
                        ('active', True)]) for parameter in p['parameters']]
            if new_parameters:
                p['parameters'] = new_parameters
        payload = {
            "programs": programs,
            "populations": populations,
            "categories": program_categories
        }
        return payload
