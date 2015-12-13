from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import marshal_with
from server.webapp.fields import Json

result_fields = {
    'parameters': Json
}


class Parameters(Resource):
    @marshal_with(result_fields)
    @login_required
    def get(self):
        """
        Gives back project parameters (modifiable)
        """
        from parameters import parameters
        project_parameters = [
            p for p in parameters() if 'modifiable' in p and p['modifiable']]
        payload = {
            'parameters': project_parameters
        }
        return payload
