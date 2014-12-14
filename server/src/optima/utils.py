import os
from sim.dataio import DATADIR, PROJECTDIR, TEMPLATEDIR, loaddata, savedata, upload_dir_user
from flask import helpers
from flask.ext.login import current_user
from functools import wraps
from flask import request, jsonify
from dbconn import db
from dbmodels import ProjectDb, WorkingProjectDb
import traceback

ALLOWED_EXTENSIONS = {'txt', 'xlsx', 'xls'}

BAD_REPLY = {"status":"NOK"}

def check_project_name(api_call):
    @wraps(api_call)
    def _check_project_name(*args, **kwargs):
        reply = BAD_REPLY
        # print(request.headers)
        try:
            project_name = request.headers['project']
        except:
            project_name = ''

        if project_name == '':
            reply['reason'] = 'No project is open'
            return jsonify(reply)
        else:
            request.project_name = project_name
            return api_call(*args, **kwargs)
    return _check_project_name

def report_exception(reason = None):
    def _report_exception(api_call):
        @wraps(api_call)
        def __report_exception(*args, **kwargs):
            try:
                return api_call(*args, **kwargs)
            except Exception, err:
                var = traceback.format_exc()
                reply = BAD_REPLY
                reply['exception'] = var
                if reason:
                    reply['reason'] = reason
                return jsonify(reply)
        return __report_exception
    return _report_exception


""" Finds out if this file is allowed to be uploaded """
def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def loaddir(app):
    loaddir = app.config['UPLOAD_FOLDER']
    print("loaddir = %s" % loaddir)
    if not loaddir:
        loaddir = DATADIR
    return loaddir

def project_exists(name):
    cu = current_user
    return ProjectDb.query.filter_by(user_id=cu.id, name=name).count()>0

def save_data_spreadsheet(name, folder=DATADIR):
    spreadsheet_file = name
    user_dir = upload_dir_user(folder)
    if not spreadsheet_file.startswith(user_dir):
        spreadsheet_file = helpers.safe_join(user_dir, name+ '.xlsx')

def delete_spreadsheet(name):
    spreadsheet_file = name
    for parent_dir in [TEMPLATEDIR, DATADIR]:
        user_dir = upload_dir_user(TEMPLATEDIR)
        if not spreadsheet_file.startswith(user_dir):
            spreadsheet_file = helpers.safe_join(user_dir, name+ '.xlsx')
        if os.path.exists(spreadsheet_file):
            os.remove(spreadsheet_file)

"""
  loads the project with the given name
  returns the model (D).
"""
def load_model(name, as_bunch = True, working_model = False):
    print("load_model:%s" % name)
    model = None
    cu = current_user
    print("getting project %s for user %s" % (name, cu.id))
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
    if proj is not None:
        if proj.working_project is None or working_model == False:
            print("project %s does not have working model" % name)
            model = proj.model
        else:
            print("project %s has working model" % name)
            model = proj.working_project.model
        if model is None or len(model.keys())==0:
            print("model %s is None" % name)
        else:
            if as_bunch:
                from sim.bunch import Bunch
                print("convert model %s to Bunch" % name)
                model = Bunch.fromDict(model)
    else:
        print("no such project found: %s for user %s %s" % (name, cu.id, cu.name))
    db.session.close() #very important!
    return model

def save_model_db(name, model):
    print("save_model_db %s" % name)

    from sim.bunch import Bunch
    cu = current_user
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
    if isinstance(model, Bunch):
        model = model.toDict()
    proj.model = model
    db.session.add(proj)
    db.session.commit()

def save_working_model(name, model):

    from sim.bunch import Bunch
    cu = current_user
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
    if isinstance(model, Bunch):
        model = model.toDict()

    # If we do not have an instance for working project, make it now
    if proj.working_project is None:
        working_project = WorkingProjectDb(proj.id, model=model, is_calibrating=True)
    else:
        proj.working_project.model = model
        working_project = proj.working_project

    db.session.add(working_project)
    db.session.commit()

def save_working_model_as_default(name):
    print("save_working_model_as_default %s" % name)

    from sim.bunch import Bunch
    cu = current_user
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()

    # Default value for model
    model = {}

    # Make sure there is a working project
    if proj.working_project is not None:
        proj.model = proj.working_project.model
        model = proj.model
        db.session.add(proj)
        db.session.commit()
    else:
        db.session.close()

    return model

def revert_working_model_to_default(name):
    print("revert_working_model_to_default %s" % name)

    from sim.bunch import Bunch
    cu = current_user
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
    model = proj.model

    # Make sure there is a working project
    if proj.working_project is not None:
        proj.working_project.is_calibrating = False
        db.session.add(proj.working_project)
        db.session.commit()

    return model

def save_model(name, model):
  try:
    save_model_db(name, model)
  except:
    save_model_file(name, model)

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
