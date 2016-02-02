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
from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ParsetsDb, ResultsDb

import optima as op

# /api/project/<project-id>/scenarios

class Scenarios(Resource):
    """
    Scenarios for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get the scenarios for the given project."
    )
