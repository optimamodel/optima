import os
from sim.dataio import DATADIR, TEMPLATEDIR, upload_dir_user
from flask import helpers, current_app
from flask.ext.login import current_user
from functools import wraps
from flask import request, jsonify, abort
from dbconn import db
from dbmodels import ProjectDb, WorkingProjectDb, UserDb
import traceback

ALLOWED_EXTENSIONS = {'txt', 'xlsx', 'xls', 'json'}

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
        except Exception, err:
            exception = traceback.format_exc()
            current_app.logger.error("Exception during request %s: %s" % (request, exception))
            reply = {'reason': 'No project is open', 'exception': exception}
            return jsonify(reply), 500
    return _check_project_name

def report_exception(reason = None):
    def _report_exception(api_call):
        @wraps(api_call)
        def __report_exception(*args, **kwargs):
            try:
                return api_call(*args, **kwargs)
            except Exception, err:
                exception = traceback.format_exc()
                current_app.logger.error("Exception during request %s: %s" % (request, exception))
                reply = {'exception': exception}
                if reason:
                    reply['reason'] = reason
                return jsonify(reply), 500
        return __report_exception
    return _report_exception

#verification by secret (hashed pw) or by being a user with admin rights
def verify_admin_request(api_call):
    @wraps(api_call)
    def _verify_admin_request(*args, **kwargs):
        u = None
        if (not current_user.is_anonymous()) and current_user.is_authenticated() and current_user.is_admin:
            u = current_user
        else:
            secret = request.args.get('secret','')
            u = UserDb.query.filter_by(password = secret, is_admin=True).first()
        if u is None:
            abort(404)
        else:
            current_app.logger.debug("admin_user: %s %s %s" % (u.name, u.password, u.email))
            return api_call(*args, **kwargs)
    return _verify_admin_request


""" Finds out if this file is allowed to be uploaded """
def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def loaddir(app):
    loaddir = app.config['UPLOAD_FOLDER']
    if not loaddir:
        loaddir = DATADIR
    return loaddir

def send_as_json_file(data):
    import json
    from flask import Response
    loaddir =  upload_dir_user(TEMPLATEDIR)
    if not loaddir:
        loaddir = TEMPLATEDIR
    filename = 'data.json'
    server_filename = os.path.join(loaddir, filename)
    print "server_filename", server_filename
    with open(server_filename, 'wb') as filedata:
        json.dump(data, filedata)
    response = helpers.send_from_directory(loaddir, filename)
#    response.headers.add('content-length', str(os.path.getsize(server_filename)))
    return response


def project_exists(id):
    cu = current_user
    if current_user.is_admin:
        return ProjectDb.query.filter_by(id=id).count()>0
    else:
        return ProjectDb.query.filter_by(id=id, user_id=cu.id).count()>0

def load_project(id, all_data = False):
    from sqlalchemy.orm import undefer, defaultload
    cu = current_user
    current_app.logger.debug("getting project %s for user %s (admin:%s)" % (id, cu.id, cu.is_admin))
    if cu.is_admin:
        query = ProjectDb.query.filter_by(id=id)
    else:
        query = ProjectDb.query.filter_by(id=id, user_id=cu.id)
    if all_data:
        query = query.options( \
            undefer('model'), \
            defaultload(ProjectDb.working_project).undefer('model'), \
            defaultload(ProjectDb.project_data).undefer('meta'))
    project = query.first()
    if project is None:
        current_app.logger.warning("no such project found: %s for user %s %s" % (id, cu.id, cu.name))
    return project

def save_data_spreadsheet(name, folder=DATADIR):
    spreadsheet_file = name
    user_dir = upload_dir_user(folder)
    if not spreadsheet_file.startswith(user_dir):
        spreadsheet_file = helpers.safe_join(user_dir, name+ '.xlsx')

def delete_spreadsheet(name, user_id = None):
    spreadsheet_file = name
    for parent_dir in [TEMPLATEDIR, DATADIR]:
        user_dir = upload_dir_user(TEMPLATEDIR, user_id)
        if not spreadsheet_file.startswith(user_dir):
            spreadsheet_file = helpers.safe_join(user_dir, name+ '.xlsx')
        if os.path.exists(spreadsheet_file):
            os.remove(spreadsheet_file)

def model_as_dict(model):
    from sim.bunch import Bunch
    if isinstance(model, Bunch):
        model = model.toDict()
    return model

def model_as_bunch(model):
    from sim.bunch import Bunch
    return Bunch.fromDict(model)

"""
  loads the project with the given name
  returns the model (D).
"""
def load_model(id, as_bunch = True, working_model = False):
    current_app.logger.debug("load_model:%s" % id)
    model = None
    project = load_project(id)
    if project is not None:
        if  working_model == False or project.working_project is None:
            current_app.logger.debug("project %s loading main model" % id)
            model = project.model
        else:
            current_app.logger.debug("project %s loading working model" % id)
            model = project.working_project.model
        if model is None or len(model.keys())==0:
            current_app.logger.debug("model %s is None" % id)
        else:
            if as_bunch:
                model = model_as_bunch(model)
    return model

def save_working_model(id, model):

    model = model_as_dict(model)
    project = load_project(id)

    # If we do not have an instance for working project, make it now
    if project.working_project is None:
        working_project = WorkingProjectDb(project.id, model=model, is_calibrating=True)
    else:
        project.working_project.model = model
        working_project = project.working_project

    db.session.add(working_project)
    db.session.commit()

def save_working_model_as_default(id):
    current_app.logger.debug("save_working_model_as_default %s" % id)

    project = load_project(id)
    model = project.model

    # Make sure there is a working project
    if project.working_project is not None:
        project.model = project.working_project.model
        model = project.model
        db.session.add(project)
        db.session.commit()

    return model

def revert_working_model_to_default(id):
    current_app.logger.debug("revert_working_model_to_default %s" % id)

    project = load_project(id, all_data = True)
    model = project.model

    # Make sure there is a working project
    if project.working_project is not None:
        project.working_project.is_calibrating = False
        project.working_project.model = model
        db.session.add(project.working_project)
        db.session.commit()

    return model

def save_model(id, model):
    current_app.logger.debug("save_model %s" % id)

    model = model_as_dict(model)
    project = load_project(id)
    project.model = model #we want it to fail if there is no project...
    db.session.add(project)
    db.session.commit()

def pick_params(params, data, args = {}):
    for param in params:
        the_value = data.get(param)
        if the_value:
            args[param] = the_value
    return args

def for_fe(item): #only for json
    import numpy as np
    from sim.bunch import Bunch as struct

    if isinstance(item, list):
        return [for_fe(v) for v in item]
    if isinstance(item, np.ndarray):
        return [for_fe(v) for v in item.tolist()]
    elif isinstance(item, struct):
        return item.toDict()
    elif isinstance(item, dict):

        return dict( (k, for_fe(v)) for k,v in item.iteritems() )
    elif isinstance(item, float) and np.isnan(item):
        return None
    else:
        return item
