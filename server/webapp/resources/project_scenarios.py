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
    load_project, load_progset, load_program, load_scenario, RequestParser, report_exception, modify_program)
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist, ScenarioDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser
from server.webapp.dbconn import db
from server.webapp.dbmodels import ScenariosDb

import optima as op

scenario_parser = RequestParser()
scenario_parser.add_arguments({
    'name': {'type': str, 'location': 'args', 'required': True},
    'parset_id': {'type': uuid.UUID, 'location': 'args', 'required': True},
    'scenario_type': {'type': str, 'location': 'args', 'required': True},
    'active': {'type': bool, 'location': 'args', 'required': True}
})

def check_pars(blob):
    """
    Check the pars attribute for scenarios.
    """
    if 'pars' not in blob.keys():
        raise ValueError("JSON body requires 'pars' parameter")

    if not isinstance(blob['pars'], list):
        raise ValueError("'pars' needs to be a list.")

    pars = []

    for i in blob['pars']:

        pars.append({
            'endval': int(i['endval']),
            'endyear': int(i['endyear']),
            'name': str(i['name']),
            'for': list(i['for']),
            'startval': int(i['startval']),
            'startyear': int(i['startyear'])
        })

    return pars

# /api/project/<project-id>/scenarios

class Scenarios(Resource):
    """
    Scenarios for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get the scenarios for the given project."
    )
    @marshal_with(ScenariosDb.resource_fields, envelope='scenarios')
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

        if args['scenario_type'] == "Parameter":
            blob = {'pars': check_pars(json.loads(request.data))}
        else:
            blob = {}

        scenario_entry = ScenariosDb(project_id, blob=blob, **args)

        db.session.add(scenario_entry)
        db.session.flush()
        db.session.commit()

        return scenario_entry, 201


# /api/project/<project-id>/scenarios/results
class ScenarioResults(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        operation="Run the scenarios for the given project."
    )
    def get(self, project_id):

        project_entry = load_project(project_id)
        project = project_entry.hydrate()
        project.runscenarios()

        graphs = op.plotting.makeplots(project.results[-1], figsize=(4, 3))

        jsons = []
        for graph in graphs:
            # Add necessary plugins here
            mpld3.plugins.connect(graphs[graph], mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
            # a hack to get rid of NaNs, javascript JSON parser doesn't like them
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph])).replace('NaN', 'null')
            jsons.append(json.loads(json_string))

        return jsons


# /api/project/<project-id>/scenarios/<scenarios-id>
class Scenario(Resource):
    """
    A given scenario.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get a single scenario."
    )
    @marshal_with(ScenariosDb.resource_fields)
    def get(self, project_id, scenario_id):
        """
        Get a single scenario.
        """
        return load_scenario(project_id, scenario_id)

    @swagger.operation(
        description="Update a single scenario."
    )
    @marshal_with(ScenariosDb.resource_fields)
    def put(self, project_id, scenario_id):
        """
        Update a single scenario.
        """
        args = scenario_parser.parse_args()

        if args['scenario_type'] == "Parameter":
            blob = {'pars': check_pars(json.loads(request.data))}
        else:
            blob = {}

        scenario_entry = load_scenario(project_id, scenario_id)

        scenario_entry.name = args['name']
        scenario_entry.scenario_type = args['scenario_type']
        scenario_entry.parset_id = args['parset_id']
        scenario_entry.progset_id = args.get('progset_id')
        scenario_entry.active = args['active']
        scenario_entry.blob = blob

        db.session.commit()

        return scenario_entry

    @swagger.operation(
        description="Delete a scenario."
    )
    def delete(self, project_id, scenario_id):

        scenario_entry = load_scenario(project_id, scenario_id)

        db.session.delete(scenario_entry)
        db.session.commit()

        return b'', 204
