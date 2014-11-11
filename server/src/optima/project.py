import json
import fnmatch
from flask import Flask, Blueprint, url_for, helpers, request, jsonify, session, redirect
import shutil
from werkzeug import secure_filename
import os
import sys
import traceback
from sim.dataio import loaddata, savedata, DATADIR, PROJECTDIR, TEMPLATEDIR
from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.optimize import optimize
from optima.data import data
from utils import *
from flask.ext.login import login_required

""" route prefix: /api/project """
project = Blueprint('project',  __name__, static_folder = '../static')
project.config = {}

@project.record
def record_params(setup_state):
  app = setup_state.app
  project.config = dict([(key,value) for (key,value) in app.config.iteritems()])

"""
Creates the project with the given name and provided parameters.
Result: on the backend, new project is stored, 
spreadsheet with specified name and parameters given back to the user.
"""
@project.route('/create/<project_name>', methods=['POST'])
@login_required
# expects json with the following arguments (see example):
# {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}
def createProject(project_name):
    session.clear()
    print("createProject %s" % project_name)
    data = request.form
    if data:
        data = json.loads(data['params'])
#    data = json.loads(request.args.get('params'))
#    data = dict([(x,int(y)) for (x,y) in data.items()])
    print(data)
    makeproject_args = {"projectname":project_name}
    if data.get('datastart'):
        makeproject_args['datastart'] = int(data['datastart'])
    if data.get('dataend'):
        makeproject_args['dataend'] = int(data['dataend'])
    if data.get('econ_datastart'):
        makeproject_args['econ_datastart'] = int(data['econ_datastart'])
    if data.get('econ_dataend'):
        makeproject_args['econ_dataend'] = int(data['econ_dataend'])
    if data.get('programs'):
        makeproject_args['progs'] = data['programs']
    if data.get('populations'):
        makeproject_args['pops'] = data['populations']
#    makeproject_args = dict(makeproject_args.items() + data.items())
    print(makeproject_args)
    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    new_project_template = D.spreadsheetname
    print("new_project_template: %s" % new_project_template)
    (dirname, basename) = (TEMPLATEDIR, new_project_template)
#    xlsname = project_name + '.xlsx'
#    srcfile = helpers.safe_join(project.static_folder,'example.xlsx')
#    dstfile =  helpers.safe_join(dirname, xlsname)
#    shutil.copy(srcfile, dstfile)
    session['project_name'] = project_name 
    return helpers.send_from_directory(dirname, basename)

"""
Opens the project with the given name.
If the project exists, should put it in session and return to the user.
"""
@project.route('/open/<project_name>')
# expects project name, will put it into session
# todo: only if it can be found
def openProject(project_name):
    if not project_exists(project_name):
      return jsonify({'status':'NOK','reason':'No such project %s' % project_name})
    else:
      session['project_name'] = project_name 
      return redirect(url_for('site'))

"""
Returns the current project name.
"""
@project.route('/name')
def getProjectInfo():
    return jsonify({"project":session.get('project_name','')})

"""
Returns the list of existing projects.
"""
@project.route('/list')
def getProjectList():
    projects = []
    for file in os.listdir(PROJECTDIR):
        if fnmatch.fnmatch(file, '*.prj'):
            projects.append(file)
    return jsonify({"projects":projects})

"""
Download example Excel file.
"""
@project.route('/download/<downloadName>', methods=['GET'])
def downloadExcel(downloadName):
    example_excel_file_name = 'example.xlsx'

    file_path = helpers.safe_join(project.static_folder, example_excel_file_name)
    options = {
        'cache_timeout': project.get_send_file_max_age(example_excel_file_name),
        'conditional': True,
        'attachment_filename': downloadName
    }
    return helpers.send_file(file_path, **options)

"""
Uploads Excel file, uses it to update the corresponding model.
Precondition: model should exist.
"""
@project.route('/update', methods=['POST'])
def uploadExcel():
    reply = {'status':'NOK'}
    file = request.files['file']
    loaddir = project.config['UPLOAD_FOLDER']
    print("loaddir = %s" % loaddir)
    if not loaddir:
        loaddir = DATADIR
    print("loaddir = DATADIR")
    if not file:
        reply['reason'] = 'No file is submitted!'
        return json.dumps(reply)

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        reply['reason'] = 'File type of %s is not accepted!' % filename
        return json.dumps(reply)

    reply['file'] = filename
    if allowed_file(filename):
        server_filename = os.path.join(loaddir, filename)
        file.save(server_filename)

    file_basename, file_extension = os.path.splitext(filename)
    project_name = helpers.safe_join(PROJECTDIR, file_basename+'.prj')
    print("project name: %s" % project_name)
    if not os.path.exists(project_name):
        reply['reason'] = 'Project %s does not exist' % file_basename
        return json.dumps(reply)

    try:
        data = loaddata(project_name)
        D = updatedata(data, loaddir)
    except Exception, err:
        var = traceback.format_exc()
        reply['exception'] = var
        return json.dumps(reply)      

    session['project_name'] = project_name 
    reply['status'] = 'OK'
    reply['result'] = 'Project %s is updated' % file_basename
    return json.dumps(reply)
