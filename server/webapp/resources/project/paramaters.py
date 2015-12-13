from flask import jsonify
from flask.ext.login import login_required
from flask_restful import Resource


class Parameters(Resource):

    # @swagger.operation(
    #     responseClass=ProjectDb.__name__,
    #     summary='Create a new Project'
    # )
    @login_required
    def get(self):
        """
        Gives back project parameters (modifiable)
        """
        from optima import parameters
        project_parameters = [p for p in parameters()
                              if 'modifiable' in p and p['modifiable']]
        return jsonify({"parameters": project_parameters})
