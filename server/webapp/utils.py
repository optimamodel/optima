import os
from functools import wraps
import traceback

from dataio import TEMPLATEDIR, upload_dir_user, fromjson, tojson

from flask import helpers, current_app, abort
from flask import request, jsonify, Response, make_response
from werkzeug.datastructures import FileStorage

from flask.ext.login import current_user
from flask_restful.reqparse import RequestParser as OrigReqParser

from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, UserDb

# json should probably removed from here since we are now using prj for up/download
ALLOWED_EXTENSIONS = {'txt', 'xlsx', 'xls', 'json', 'prj'}


def check_project_name(api_call):
    @wraps(api_call)
    def _check_project_name(*args, **kwargs):
        project_name = None
        project_id = None
        try:
            project_name = request.headers['project']
            project_id = request.headers['project-id']
            request.project_name = project_name
            request.project_id = project_id
            return api_call(*args, **kwargs)
        except Exception:
            exception = traceback.format_exc()
            current_app.logger.error("Exception during request %s: %s" % (request, exception))
            reply = {'reason': 'No project is open', 'exception': exception}
            return jsonify(reply), 400
    return _check_project_name


#this should be run after check_project_name
def check_project_exists(api_call):
    @wraps(api_call)
    def _check_project_exists(*args, **kwargs):
        project_id = request.headers['project-id']
        project_name = request.headers['project']
        if not project_exists(project_id):
            error_msg = 'Project %s(%s) does not exist' % (project_id, project_name)
            current_app.logger.error(error_msg)
            reply = {'reason': error_msg}
            return jsonify(reply), 404
        else:
            return api_call(*args, **kwargs)
    return _check_project_exists


def report_exception(api_call):
    @wraps(api_call)
    def _report_exception(*args, **kwargs):
        from werkzeug.exceptions import HTTPException
        try:
            return api_call(*args, **kwargs)
        except Exception, e:
            exception = traceback.format_exc()
            # limiting the exception information to 10000 characters maximum
            # (to prevent monstrous sqlalchemy outputs)
            current_app.logger.error("Exception during request %s: %.10000s" % (request, exception))
            if isinstance(e, HTTPException):
                raise
            code = 500
            reply = {'exception': exception}
            return make_response(jsonify(reply), code)
    return _report_exception


def verify_admin_request(api_call):
    """
    verification by secret (hashed pw) or by being a user with admin rights
    """
    @wraps(api_call)
    def _verify_admin_request(*args, **kwargs):
        u = None
        if (not current_user.is_anonymous()) and current_user.is_authenticated() and current_user.is_admin:
            u = current_user
        else:
            secret = request.args.get('secret', '')
            u = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if u is None:
            abort(403)
        else:
            current_app.logger.debug("admin_user: %s %s %s" % (u.name, u.password, u.email))
            return api_call(*args, **kwargs)
    return _verify_admin_request


def allowed_file(filename):
    """
    Finds out if this file is allowed to be uploaded
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def loaddir(app):
    the_loaddir = app.config['UPLOAD_FOLDER']
    return the_loaddir


def send_as_json_file(data):
    import json
    the_loaddir = upload_dir_user(TEMPLATEDIR)
    if not the_loaddir:
        the_loaddir = TEMPLATEDIR
    filename = 'data.json'
    server_filename = os.path.join(the_loaddir, filename)
    print "server_filename", server_filename
    with open(server_filename, 'wb') as filedata:
        json.dump(data, filedata)
    response = helpers.send_from_directory(loaddir, filename)
#    response.headers.add('content-length', str(os.path.getsize(server_filename)))
    return response


def project_exists(project_id, raise_exception=False):
    from server.webapp.exceptions import ProjectDoesNotExist
    cu = current_user
    query_args = {'id': project_id}
    if not current_user.is_admin:
        query_args['user_id'] = cu.id
    count = ProjectDb.query(**query_args)

    if raise_exception and count == 0:
        raise ProjectDoesNotExist(id=project_id)

    return count > 0


def load_project(project_id, all_data=False, raise_exception=False):
    from sqlalchemy.orm import undefer, defaultload
    from server.webapp.exceptions import ProjectDoesNotExist
    cu = current_user
    current_app.logger.debug("getting project %s for user %s (admin:%s)" % (project_id, cu.id, cu.is_admin))
    if cu.is_admin:
        query = ProjectDb.query.filter_by(id=project_id)
    else:
        query = ProjectDb.query.filter_by(id=project_id, user_id=cu.id)
    if all_data:
        query = query.options(
            # undefer('model'),
            # defaultload(ProjectDb.working_project).undefer('model'),
            defaultload(ProjectDb.project_data).undefer('meta'))
    project = query.first()
    if project is None:
        current_app.logger.warning("no such project found: %s for user %s %s" % (project_id, cu.id, cu.name))
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)
    return project


def save_data_spreadsheet(name, folder=None):
    if folder is None:
        folder = current_app.config['UPLOAD_FOLDER']
    spreadsheet_file = name
    user_dir = upload_dir_user(folder)
    if not spreadsheet_file.startswith(user_dir):
        spreadsheet_file = helpers.safe_join(user_dir, name + '.xlsx')


def delete_spreadsheet(name, user_id=None):
    spreadsheet_file = name
    for parent_dir in [TEMPLATEDIR, current_app.config['UPLOAD_FOLDER']]:
        user_dir = upload_dir_user(parent_dir, user_id)
        if not spreadsheet_file.startswith(user_dir):
            spreadsheet_file = helpers.safe_join(user_dir, name + '.xlsx')
        if os.path.exists(spreadsheet_file):
            os.remove(spreadsheet_file)


# TODO get rid of this
def model_as_dict(model):
    return tojson(model)


# TODO get rid of this
def model_as_bunch(model):
    return fromjson(model)


def load_model(project_id, from_json=True, working_model=False):  # todo rename
    """
      loads the project with the given name
      returns the hydrated project instance (Can't think of another name than "model" yet...).
    """
    # TODO we won't have to do this for working_model, because this concept won't make sense in Optima 2.0
    current_app.logger.debug("load_model:%s" % project_id)
    model = None
    project = load_project(project_id)
    if project is not None:
        if not working_model or project.working_project is None:
            current_app.logger.debug("project %s loading main model" % project_id)
            model = project.hydrate()
        else:  # this branch won't be needed
            current_app.logger.debug("project %s loading working model" % project_id)
            model = project.working_project.hydrate()
        if model is None:
            current_app.logger.debug("model %s is None" % project_id)
#        else: todo remove from_json
#            if from_json: model = model_as_bunch(model)
    return model


def save_working_model_as_default(project_id):  # TODO will be about results, not about the model
    current_app.logger.debug("save_working_model_as_default %s" % project_id)

    project = load_project(project_id)
    model = project.model

    # Make sure there is a working project
    if project.working_project is not None:
        project.model = project.working_project.model
        model = project.model
        db.session.add(project)
        db.session.commit()

    return model


def revert_working_model_to_default(project_id):  # TODO will be about results, not about the model
    current_app.logger.debug("revert_working_model_to_default %s" % project_id)

    project = load_project(project_id, all_data=True)
    model = project.model

    # Make sure there is a working project
    if project.working_project is not None:
        project.working_project.is_calibrating = False
        project.working_project.model = model
        db.session.add(project.working_project)
        db.session.commit()

    return model


def save_model(project_id, model, to_json=False):
    # model is given as json by default, no need to convert
    current_app.logger.debug("save_model %s" % project_id)

    if to_json:
        model = model_as_dict(model)
    project = load_project(project_id)
    project.model = model  # we want it to fail if there is no project...
    db.session.add(project)
    db.session.commit()


def pick_params(params, data, args=None):
    if args is None:
        args = {}
    for param in params:
        the_value = data.get(param)
        if the_value:
            args[param] = the_value
    return args


def for_fe(item):  # only for json
    import numpy as np

    if isinstance(item, list):
        return [for_fe(v) for v in item]
    if isinstance(item, np.ndarray):
        return [for_fe(v) for v in item.tolist()]
    elif isinstance(item, dict):
        return dict((k, for_fe(v)) for k, v in item.iteritems())
    elif isinstance(item, float) and np.isnan(item):
        return None
    else:
        return item


def update_or_create_parset(project_id, name, parset):

    from datetime import datetime
    import dateutil
    from server.webapp.dbmodels import ParsetsDb
    from optima.utils import saves

    parset_record = ParsetsDb.query \
        .filter_by(id=parset.uid, project_id=project_id) \
        .first()

    if parset_record is None:
        parset_record = ParsetsDb(
            project_id=project_id,
            name=name,
            created=parset.created or datetime.now(dateutil.tz.tzutc()),
            updated=datetime.now(dateutil.tz.tzutc()),
            pars=saves(parset.pars)
        )

        db.session.add(parset_record)
    else:
        parset_record.updated = datetime.now(dateutil.tz.tzutc())
        parset_record.pars = saves(parset.pars)


def update_or_create_progset(project_id, name, progset):

    from datetime import datetime
    import dateutil
    from server.webapp.dbmodels import ProgsetsDb

    progset_record = ProgsetsDb.query \
        .filter_by(name=progset.name, project_id=project_id) \
        .first()

    if progset_record is None:
        progset_record = ProgsetsDb(
            project_id=project_id,
            name=name,
            created=progset.created or datetime.now(dateutil.tz.tzutc()),
            updated=datetime.now(dateutil.tz.tzutc())
        )

        db.session.add(progset_record)
        db.session.flush()
    else:
        progset_record.updated = datetime.now(dateutil.tz.tzutc())

    return progset_record


def update_or_create_program(project_id, progset_id, name, program, active=False):

    from datetime import datetime
    import dateutil
    from server.webapp.dbmodels import ProgramsDb

    program_record = ProgramsDb.query \
        .filter_by(name=name, project_id=project_id, progset_id=progset_id) \
        .first()

    if program_record is None:
        program_record = ProgramsDb(
            project_id=project_id,
            progset_id=progset_id,
            name=name,
            short_name=program.get('short_name', ''),
            category=program.get('category', ''),
            created=datetime.now(dateutil.tz.tzutc()),
            updated=datetime.now(dateutil.tz.tzutc()),
            pars=ProgramsDb.program_pars_to_pars(program.get('targetpars', [])),
            targetpops=program.get('targetpops', []),
            active=active,
            criteria=program.get('criteria', None)
        )

        db.session.add(program_record)
    else:
        program_record.updated = datetime.now(dateutil.tz.tzutc())
        program_record.pars = ProgramsDb.program_pars_to_pars(program.get('targetpars', []))
        program_record.targetpops = program.get('targetpops', [])
        program_record.short_name = program.get('short_name', '')
        program_record.category = program.get('category', '')
        program_record.active = active
        program_record.criteria = program.get('criteria', None)

    if program.get('short_name') == 'PWID programs':
        raise Exception(program_record.__dict__)

def init_login_manager(login_manager):

    @login_manager.user_loader
    def load_user(userid):
        from server.webapp.dbmodels import UserDb
        try:
            user = UserDb.query.filter_by(id=userid).first()
        except Exception:
            user = None
        return user

    @login_manager.request_loader
    def load_user_from_request(request):  # pylint: disable=redefined-outer-name

        # try to login using the secret url arg
        secret = request.args.get('secret')
        if secret:
            from server.webapp.dbmodels import UserDb
            user = UserDb.query.filter_by(password=secret, is_admin=True).first()
            if user:
                return user

        # finally, return None if both methods did not login the user
        return None

    @login_manager.unauthorized_handler
    def unauthorized_handler():
        abort(401)


class RequestParser(OrigReqParser):

    def __init__(self, *args, **kwargs):
        super(RequestParser, self).__init__(*args, **kwargs)
        self.abort_on_error = True

    def get_swagger_type(self, arg):
        try:
            if issubclass(arg.type, FileStorage):
                return 'file'
        except TypeError:
            ## this arg.type was not a class
            pass

        if callable(arg.type):
            return arg.type.__name__
        return arg.type

    def swagger_parameters(self):
        return [
            {
                'name': arg.name,
                'dataType': self.get_swagger_type(arg),
                'required': arg.required,
                'description': arg.help,
                'paramType': 'form',
            }
            for arg in self.args
        ]

    def add_arguments(self, arguments_dict):
        for argument_name, kwargs in arguments_dict.iteritems():
            self.add_argument(argument_name, **kwargs)

    def parse_args(self, req=None, strict=False):
        from werkzeug.exceptions import HTTPException

        try:
            return super(RequestParser, self).parse_args(req, strict)
        except HTTPException as e:
            if self.abort_on_error:
                raise e
            else:
                raise ValueError(e.data['message'])
