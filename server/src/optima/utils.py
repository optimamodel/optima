import os
from sim.dataio import DATADIR, PROJECTDIR, TEMPLATEDIR, loaddata, savedata, upload_dir_user
from flask import helpers, session
from flask.ext.login import current_user
from functools import wraps
from flask import request, jsonify

ALLOWED_EXTENSIONS=set(['txt','xlsx','xls'])

def check_project_name(api_call):
  @wraps(api_call)
  def _check_project_name(*args, **kwargs):
    reply = {"status":"NOK"}
    print(request.headers)
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


""" Finds out if this file is allowed to be uploaded """
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def loaddir(app):
  loaddir = ''
  loaddir = app.config['UPLOAD_FOLDER']
  print("loaddir = %s" % loaddir)
  if not loaddir:
    loaddir = DATADIR
  return loaddir

def project_path(name, folder = PROJECTDIR):
  print("project_path %s" % name)
  project_file = name
  user_dir = upload_dir_user(folder)
  print("user_dir:%s" % user_dir)
  if not project_file.startswith(user_dir):
    project_file = helpers.safe_join(user_dir, name+'.prj')
  print("project name: %s -> %s" % (name, project_file))
  return project_file

def project_file_exists(name, folder = PROJECTDIR):
  project_file = project_path(name, folder)
  return os.path.exists(project_file)

def project_exists_db(name):
  from api import db
  from dbmodels import ProjectDb
  cu = current_user
  return ProjectDb.query.filter_by(user_id=cu.id, name=name).count()

def project_exists(name, folder = PROJECTDIR):
  return project_exists_db(name)

def delete_project_file(name, folder = PROJECTDIR):
  print("delete_project_file %s" % name)
  try:
    the_project_path = project_path(name, folder)
    print("the_project_path(%s) = %s" % (name, the_project_path))
    if os.path.exists(the_project_path):
      os.remove(the_project_path)
    return True
  except:
    return False

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
  loads the project with the given name from the given folder
  returns the model (D).
"""
def load_model_file(name, folder = PROJECTDIR):
  print("load_model %s %s" % (name, folder))
  project_file = project_path(name, folder)
  data = loaddata(project_file)
  return data

def load_model(name):
  print("load_model:%s" % name)
  model = None
  try:
    from api import db
    from dbmodels import ProjectDb
    cu = current_user
    print("cu: %s" % cu)
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
    print("proj: %s" % proj)
    model = proj.model
  except:
    pass
  if model is None or len(model.keys())==0:
    return load_model_file(name)
  else:
    from sim.bunch import Bunch
    return Bunch.fromDict(model)

def save_model_file(name, model, folder = PROJECTDIR):
  project_file = project_path(name, folder)
  return savedata(project_file, model)

def save_model_db(name, model):
  from api import db
  from dbmodels import ProjectDb
  cu = current_user
  proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
  proj.model = model.toDict()
  db.session.add(proj)
  db.session.commit()

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
