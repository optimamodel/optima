import mpld3
import json
import uuid

from flask import current_app, request

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.inputs import SubParser
from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import (
    load_project, load_progset, load_program, RequestParser, report_exception, modify_program)
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser
from server.webapp.dbconn import db
from server.webapp.dbmodels import ScenariosDb

import optima as op


pars_parser = RequestParser()
pars_parser.add_arguments({
    'endval': {'type': int, 'location': 'json'},
    'endyear': {'type': int, 'location': 'json'},
    'name': {'type': str, 'location': 'json'},
    'for': {'type': int, 'location': 'json'},
    'startval': {'type': int, 'location': 'json'},
    'startyear': {'type': int, 'location': 'json'},
})


scenario_parser = RequestParser()
scenario_parser.add_arguments({
    'name': {'type': str, 'location': 'args', 'required': True},
    'parset_id': {'type': uuid.UUID, 'location': 'args', 'required': True},
    'scenario_type': {'type': str, 'location': 'args', 'required': True},
    'active': {'type': bool, 'location': 'args', 'required': True}
})

# /api/project/<project-id>/scenarios

class Scenarios(Resource):
    """
    Scenarios for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get the scenarios for the given project."
    )
    @marshal_with(ScenariosDb.resource_fields)
    def get(self, project_id):
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ScenariosDb).filter_by(project_id=project_entry.id).all()
        return reply

    @swagger.operation(
        operation="Create a new scenario for the given project.",
        parameters=scenario_parser.swagger_parameters()
    )
    @marshal_with(ScenariosDb.resource_fields)
    def post(self, project_id):

        args = scenario_parser.parse_args()

        if args.get('scenario_type') not in ["Parameter", "Program"]:
            raise ValueError("Type needs to be 'Parameter' or 'Program'.")

        try:
            blob = json.loads(request.data)
        except ValueError as e:
            print(e)
            blob = {}

        scenario_entry = ScenariosDb(project_id, blob=blob, **args)

        db.session.add(scenario_entry)
        db.session.flush()
        db.session.commit()

        return scenario_entry, 201
