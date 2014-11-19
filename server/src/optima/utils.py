import os
from sim.dataio import DATADIR, PROJECTDIR, loaddata, savedata, upload_dir_user
from flask import helpers, session

ALLOWED_EXTENSIONS=set(['txt','xlsx','xls'])

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

def project_exists(name, folder = PROJECTDIR):
  project_name = helpers.safe_join(upload_dir_user(folder), name+'.prj')
  print("project name: %s" % project_name)
  return os.path.exists(project_name)

"""
  loads the project with the given name from the given folder
  returns the model (D).
"""
def load_model(name, folder = PROJECTDIR):
  print("load_model %s %s" % (name, folder))
  project_file = name
  user_dir = upload_dir_user(folder)
  if not project_file.startswith(user_dir):
    project_file = helpers.safe_join(user_dir, name+'.prj')
  print("project file: %s" % project_file)
  data = loaddata(project_file)
  return data

def save_model(name, model, folder = PROJECTDIR):
  project_file = name
  user_dir = upload_dir_user(folder)
  if not project_file.startswith(user_dir):
    project_file = helpers.safe_join(user_dir, name+'.prj')
  return savedata(project_file, model)

def pick_params(params, data, args = {}):
  for param in params:
    the_value = data.get(param)
    if the_value:
        args[param] = the_value
  return args
