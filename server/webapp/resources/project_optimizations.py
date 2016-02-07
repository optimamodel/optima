import os
from datetime import datetime
import dateutil
import uuid


from flask import current_app, helpers, request, Response
from werkzeug.exceptions import Unauthorized
from werkzeug.utils import secure_filename

from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger

import optima as op

from server.webapp.dataio import TEMPLATEDIR, templatepath, upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ProjectDataDb, ProjectDb, ResultsDb, ProjectEconDb, OptimizationsDb

from server.webapp.inputs import secure_filename_input, AllowedSafeFilenameStorage
from server.webapp.exceptions import ProjectDoesNotExist
from server.webapp.fields import Uuid, Json

from server.webapp.resources.common import file_resource, file_upload_form_parser
from server.webapp.utils import (load_project, verify_admin_request, report_exception,
                                 save_result, delete_spreadsheet, RequestParser)


optimization_parser = RequestParser()
optimization_parser.add_arguments({
    'name': {'type': str, 'required': True},
    'parset_id': {'type': uuid.UUID, 'required': True},
    'progset_id': {'type': uuid.UUID, 'required': True},
    'optimization_type': {'type': str, 'required': True},
})


class Optimizations(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(responseClass=OptimizationsDb.__name__)
    @marshal_with(OptimizationsDb.resource_fields, envelope='optimizations')
    def get(self, project_id):
        """
        Get the optimizations for the given project.
        """
        project_entry = load_project(project_id, raise_exception=True)

        reply = db.session.query(OptimizationsDb).filter_by(project_id=project_entry.id).all()

        r = []

        for i in reply:
            i._ensure_current()
            r.append(i)

        return r

    @swagger.operation(responseClass=OptimizationsDb.__name__,
                       parameters=optimization_parser.swagger_parameters())
    @marshal_with(OptimizationsDb.resource_fields)
    def post(self, project_id):

        project_entry = load_project(project_id, raise_exception=True)

        args = optimization_parser.parse_args()

        optimization_entry = OptimizationsDb(project_id=project_id, **args)

        db.session.add(optimization_entry)
        db.session.flush()
        db.session.commit()

        return optimization_entry
