import os
from sim.dataio import DATADIR, PROJECTDIR, TEMPLATEDIR, loaddata, savedata, upload_dir_user
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

def project_exists(name, folder = PROJECTDIR):
  return project_exists(name, folder)

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
def load_model(name, folder = PROJECTDIR):
  print("load_model %s %s" % (name, folder))
  project_file = project_path(name, folder)
  data = loaddata(project_file)
  return data

def save_model(name, model, folder = PROJECTDIR):
  project_file = project_path(name, folder)
  return savedata(project_file, model)

def pick_params(params, data, args = {}):
  for param in params:
    the_value = data.get(param)
    if the_value:
        args[param] = the_value
  return args
