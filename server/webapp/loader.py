import mpld3
import json
from pprint import pprint
import pprint
import math

from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import load_project_record, load_progset_record, report_exception, load_program_record
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist, ParsetDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser

from server.webapp.utils import update_or_create_program_record

from server.webapp.dbconn import db

from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ParsetsDb, ResultsDb

from server.webapp.serializers.project_progsets import (progset_parser, param_fields,
    effect_parser, progset_effects_fields)

from server.webapp.jsonhelper import normalize_obj

import uuid
from flask_restful import fields
from server.webapp.utils import RequestParser
from server.webapp.inputs import SubParser, Json as JsonInput
from server.webapp.fields import Json, Uuid



def load_project(project_id):
    project_record = load_project_record(project_id)
    if project_record is None:
        raise ProjectDoesNotExist(id=project_id)
    return project_record.hydrate()


def load_program(project_id, progset_id, program_id):
    program_entry = load_program_record(project_id, progset_id, program_id)
    if program_entry is None:
        raise ProgramDoesNotExist(id=program_id, project_id=project_id)
    return program_entry.hydrate()


def load_parset(project_id, parset_id):
    parset_entry = db.session.query(ParsetsDb).filter_by(
        id=parset_id, project_id=project_id).first()
    if parset_entry is None:
        raise ParsetDoesNotExist(id=parset_id, project_id=project_id)
    return parset_entry.hydrate()


def load_result(project_id, parset_id):
    result_entry = db.session.query(ResultsDb).filter_by(
        project_id=project_id, parset_id=parset_id,
        calculation_type=ResultsDb.CALIBRATION_TYPE).first()
    if result_entry is None:
        return None
    return result_entry.hydrate()
