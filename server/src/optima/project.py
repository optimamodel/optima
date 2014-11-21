import json
import fnmatch
from flask import Flask, Blueprint, url_for, helpers, request, jsonify, session, redirect
import shutil
from werkzeug import secure_filename
import os
import sys
import traceback
from sim.dataio import loaddata, savedata,upload_dir_user, DATADIR, PROJECTDIR, TEMPLATEDIR
from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.optimize import optimize
from optima.data import data
from utils import allowed_file, project_file_exists, delete_project_file, delete_spreadsheet
from utils import check_project_name, load_model, save_model
from flask.ext.login import login_required, current_user

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

    #session.clear() # had to commit this line to check user session

    print("createProject %s" % project_name)
    data = request.form
    if data:
        data = json.loads(data['params'])
#    data = json.loads(request.args.get('params'))
#    data = dict([(x,int(y)) for (x,y) in data.items()])
    print(data)
    makeproject_args = {"projectname":project_name, "savetofile":False}
    name = project_name
    if data.get('datastart'):
        datastart  = makeproject_args['datastart'] = int(data['datastart'])
    else:
        datastart = ''

    if data.get('dataend'):
        dataend = makeproject_args['dataend'] = int(data['dataend'])
    else:
        dataend = ''

    if data.get('econ_datastart'):
        econ_datastart = makeproject_args['econ_datastart'] = int(data['econ_datastart'])
    else:
        econ_datastart = ''

    if data.get('econ_dataend'):
        econ_dataend = makeproject_args['econ_dataend'] = int(data['econ_dataend'])
    else:
       econ_dataend  = ''

    if data.get('programs'):
        programs = makeproject_args['progs'] = data['programs']
    else:
        programs = {}

    if data.get('populations'):
        populations = makeproject_args['pops'] = data['populations']
    else:
        populations = {}
    
    from api import db
    from dbmodels import ProjectDb
    
    print("User based processing")
    
    # get current user 
    cu = current_user
    if cu.is_anonymous() == False:
        
        # See if there is matching project
        try:
            proj = ProjectDb.query.filter_by(user_id=cu.id, name=name).first()
        except:
            proj = None
        
        # update existing 
        if proj is not None:
            proj.datastart = datastart
            proj.dataend = dataend
            proj.econ_datastart = econ_datastart
            proj.econ_dataend = econ_dataend    
            proj.programs = programs 
            proj.populations = populations  
        else:
            # create new project
            proj = ProjectDb(name, cu.id, datastart, dataend, econ_datastart, econ_dataend, programs, populations)
        
        # Save to db

    #    makeproject_args = dict(makeproject_args.items() + data.items())
    print(makeproject_args)

    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    proj.model = D.toDict()
    db.session.add(proj)
    db.session.commit()
    new_project_template = D.spreadsheetname

    print("new_project_template: %s" % new_project_template)
    (dirname, basename) = (upload_dir_user(TEMPLATEDIR), new_project_template)
    return helpers.send_from_directory(dirname, basename)

"""
Opens the project with the given name.
If the project exists, should put it in session and return to the user.
"""
@project.route('/open/<project_name>')
@login_required
# expects project name, 
# todo: only if it can be found
def openProject(project_name):
    
    cu = current_user
    proj_exists = False
    if cu.is_anonymous() == False:    
        try:
            proj_exists = ProjectDb.query.filter_by(user_id=cu.id, name=project_name).count() > 0
        except:
            proj_exists = False
        if not proj_exists: # try reading this from file and resaving
            proj_exists = project_file_exists(project_name)
    if not proj_exists:
        return jsonify({'status':'NOK','reason':'No such project %s' % project_name})
    else:
        return redirect(url_for('site'))

"""
Returns the current project name.
"""
@project.route('/name')
@login_required
@check_project_name
def getProjectInfo():
    return jsonify({"project": request.project_name})

"""
Returns the list of existing projects from db.
"""
@project.route('/list')
@login_required
def getProjectList():
    projects = []
    
    # Get current user 
    cu = current_user
    if cu.is_anonymous() == False:
        from api import db
        from dbmodels import ProjectDb
        
        # Get projects for current user
        projList = ProjectDb.query.filter_by(user_id=cu.id)
        for project in projList:
             projects.append(project.name)
   
    return jsonify({"projects":projects})

"""
Deletes the given project (and eventually, corresponding excel files)
"""
@project.route('/delete/<project_name>', methods=['POST'])
@login_required
def deleteProject(project_name):
    print("deleteProject %s" % project_name)
    try: 
        delete_project_file(project_name)
        print("project file %s deleted" % project_name)
        delete_spreadsheet(project_name)
        print("spreadsheets for %s deleted" % project_name)
        # Get current user 
        cu = current_user
        if cu.is_anonymous() == False:
        
            from api import db
            from dbmodels import ProjectDb

            # Get project row for current user with project name
            db.session.query(ProjectDb).filter_by(user_id= cu.id,name=project_name).delete()

            # delete project row
#            db.session.delete(project)
            db.session.commit()

        return jsonify({'status':'OK','reason':'Project %s deleted.' % project_name})
    except Exception, err:
        var = traceback.format_exc()
        reply = {'status':'NOK', 'reason':'Project %s did not exist.' % project_name}
        reply['exception'] = var
        return jsonify(reply)

"""
Download example Excel file.
"""
@project.route('/download/<downloadName>', methods=['GET'])
@login_required
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
@login_required
@check_project_name
def uploadExcel():
    reply = {'status':'NOK'}
    file = request.files['file']
  
    # getting current user path
    loaddir =  upload_dir_user(DATADIR)
    print("loaddir = %s" % loaddir)
    if not loaddir:
        loaddir = DATADIR
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
#    project_name = helpers.safe_join(upload_dir_user(PROJECTDIR), file_basename+'.prj')
    project_name = request.project_name
    print("project name: %s" % project_name)
#    if not os.path.exists(project_name):
#        reply['reason'] = 'Project %s does not exist' % file_basename
#        return json.dumps(reply)

    try:
        D = load_model(project_name)
        D = updatedata(D, savetofile = False)

        save_model(project_name, D)
    except Exception, err:
        var = traceback.format_exc()
        reply['exception'] = var
        return json.dumps(reply)      

    reply['status'] = 'OK'
    reply['result'] = 'Project %s is updated' % file_basename
    return json.dumps(reply)
