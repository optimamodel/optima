from flask.ext.login import login_required
from flask_restful import Resource, fields, marshal_with
from flask_restful_swagger import swagger

from server.webapp.fields import Json
from server.webapp.utils import report_exception


result_fields = {
    'fittable': fields.String,
    'name': fields.String,
    'auto': fields.String,
    'partype': fields.String,
    'proginteract': fields.String,
    'short': fields.String,
    'coverage': fields.Boolean,
    'by': fields.String,
    'pships': fields.Raw,
}


class Parameters(Resource):
    @swagger.operation(
        summary="List default parameters"
    )
    @report_exception
    @marshal_with(result_fields, envelope='parameters')
    @login_required
    def get(self, project_id):
        """Gives back project parameters (modifiable)"""

        from server.webapp.utils import load_project
        from optima.parameters import partable, loadpartable, Par

        default_pars = [par['short'] for par in loadpartable(partable)]

        project = load_project(project_id, raise_exception=True)
        be_parsets = [parset.hydrate() for parset in project.parsets]
        parameters = []
        added_parameters = set()
        for parset in be_parsets:
            print(parset.pars)
            for parameter in parset.pars:
                for key in default_pars:
                    if key not in added_parameters and \
                            key in parameter and \
                            isinstance(parameter[key], Par) and \
                            parameter[key].visible == 1 and \
                            parameter[key].y.keys():
                        param = parameter[key].__dict__
                        if parameter[key].by == 'pship':
                            pships = parameter[key].y.keys()
                        else:
                            pships = []
                        param['pships'] = pships

                        parameters.append(param)
                        added_parameters.add(key)

        return parameters


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
    @report_exception
    @marshal_with(populations_fields, envelope='populations')
    @login_required
    def get(self):
        from server.webapp.populations import populations

        populations = populations()
        for p in populations:
            p['active'] = False
        return populations
