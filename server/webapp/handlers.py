"""
handlers.py
===========

The webhandlers for project related API calls. This should only take functions
from dataio.py which refers to project ids, filenames, project names, and
JSON compatible summaries of PyOptima objects.

There should be no direct references to PyOptima objects, underlying file
structure or the database.
"""

import json
import os

import flask.json
from flask import request, flash, url_for, redirect, Blueprint, make_response
from flask_login import login_required, current_user
from flask_restful import Resource
from flask_restful_swagger import swagger
from flask_restful import Api
from werkzeug.utils import secure_filename

from . import dataio
from .dataio import report_exception_decorator, verify_admin_request_decorator
from sciris import sanitizejson

# there's a circular import when celery is loaded so must use absolute import


api_blueprint = Blueprint('api', __name__, static_folder='static')
api = swagger.docs(Api(api_blueprint), apiVersion='2.0')

# add hooks to handle UID's and datetime strings
@api.representation('application/json')
def output_json(data, code, headers=None):
    inner = json.dumps(data, cls=flask.json.JSONEncoder)
    resp = make_response(inner, code)
    resp.headers.extend(headers or {})
    return resp


def get_post_data_json():
    return sanitizejson(json.loads(request.data))


def get_upload_file(dirname):
    """
    Returns the server filename for an uploaded file,
    handled by the current flask request

    Args:
        dirname: directory on server to store the file
    """
    file = request.files['file']
    filename = secure_filename(file.filename)
    if not (os.path.exists(dirname)):
        os.makedirs(dirname)
    full_filename = os.path.join(dirname, filename)
    print("> get_upload_file '%s'" % filename)
    file.save(full_filename)

    return full_filename



#############################################################################################
### USERS
#############################################################################################


class User(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='List users')
    @verify_admin_request_decorator
    def get(self):
        return {'users': dataio.get_user_summaries()}

    @swagger.operation(summary='Create a user')
    def post(self):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.create_user(args), 201

api.add_resource(User, '/api/user')


class UserDetail(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='Delete a user')
    @verify_admin_request_decorator
    def delete(self, user_id):
        dataio.delete_user(user_id)
        return '', 204

    @swagger.operation(summary='Update a user')
    def put(self, user_id):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.update_user(user_id, args)

api.add_resource(UserDetail, '/api/user/<uuid:user_id>')


class CurrentUser(Resource):
    method_decorators = [login_required, report_exception_decorator]

    @swagger.operation(summary='Return the current user')
    def get(self):
        return dataio.parse_user_record(current_user)

api.add_resource(CurrentUser, '/api/user/current')


class UserLogin(Resource):

    @swagger.operation(summary='Try to log a user in',)
    @report_exception_decorator
    def post(self):
        args = dataio.parse_user_args(get_post_data_json())
        return dataio.do_login_user(args)

api.add_resource(UserLogin, '/api/user/login')


class UserLogout(Resource):

    @swagger.operation(summary='Log the current user out')
    @report_exception_decorator
    def get(self):
        dataio.do_logout_current_user()
        flash(u'You have been signed out')
        return redirect(url_for("site"))

api.add_resource(UserLogout, '/api/user/logout')


