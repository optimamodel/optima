import json
from flask import Blueprint, url_for, helpers, request, jsonify, redirect
from werkzeug.utils import secure_filename
import os
import traceback
from sim.dataio import upload_dir_user, DATADIR, TEMPLATEDIR, fullpath
from sim.updatedata import updatedata
from sim.makeproject import makeproject, makeworkbook
from utils import allowed_file, project_exists, delete_spreadsheet
from utils import check_project_name, load_model, save_model, report_exception
from flask.ext.login import login_required, current_user
from dbconn import db
from dbmodels import ProjectDb, WorkingProjectDb
from utils import BAD_REPLY
import time,datetime

""" route prefix: /api/project """
project = Blueprint('project',  __name__, static_folder = '../static')
project.config = {}

@project.record
def record_params(setup_state):
  app = setup_state.app
  project.config = dict([(key,value) for (key,value) in app.config.iteritems()])

"""
Gives back project params
"""
@project.route('/params')
@login_required
def get_project_params():
    from sim.parameters import parameters
    project_params = [p for p in parameters() if p['modifiable']]
    return json.dumps({"params":project_params})


"""
Creates the project with the given name and provided parameters.
Result: on the backend, new project is stored,
spreadsheet with specified name and parameters given back to the user.
"""
@project.route('/create/<project_name>', methods=['POST'])
@login_required
@report_exception()
# expects json with the following arguments (see example):
# {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}
def createProject(project_name):
    from sim.makeproject import default_datastart, default_dataend, default_econ_dataend, default_pops, default_progs

    #session.clear() # had to commit this line to check user session

    print("createProject %s" % project_name)
    data = request.form
    if data:
        data = json.loads(data['params'])
    print(data)

    makeproject_args = {"projectname":project_name, "savetofile":False}
    makeproject_args['datastart'] = data.get('datastart', default_datastart)
    makeproject_args['dataend'] = data.get('dataend', default_dataend)
    makeproject_args['econ_dataend'] = data.get('econ_dataend', default_econ_dataend)
    makeproject_args['progs'] = data.get('programs', default_progs)
    makeproject_args['pops'] = data.get('populations', default_pops)
    print("createProject(%s)" % makeproject_args)

    # get current user
    user_id = current_user.id
    proj = None
    # See if there is matching project
    proj = ProjectDb.query.filter_by(user_id=user_id, name=project_name).first()

    # update existing
    if proj is not None:
        proj.datastart = makeproject_args['datastart']
        proj.dataend = makeproject_args['dataend']
        proj.econ_dataend = makeproject_args['econ_dataend']
        proj.programs = makeproject_args['progs']
        proj.populations = makeproject_args['pops']
        print('Updating existing project %s' % proj.name)
    else:
        # create new project
        proj = ProjectDb(project_name, user_id, makeproject_args['datastart'], makeproject_args['dataend'], \
            makeproject_args['econ_dataend'], makeproject_args['progs'], makeproject_args['pops'])
        print('Creating new project: %s' % proj.name)

    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    proj.model = D.toDict()

    # Save to db
    db.session.add(proj)
    db.session.commit()
    new_project_template = D.G.workbookname

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

    proj_exists = False
    try: #first check DB
        proj_exists = project_exists(project_name)
        print("proj_exists: %s" % proj_exists)
    except:
        proj_exists = False
    if not proj_exists:
        return jsonify({'status':'NOK','reason':'No such project %s' % project_name})
    else:
        return redirect(url_for('site'))

"""
Generates workbook for the project with the given name.
"""
@project.route('/workbook/<project_name>')
@login_required
@report_exception()
#expects project name (project should already exist)
#if project exists, regenerates workbook for it
#if project does not exist, returns an error.
def giveWorkbook(project_name):
    reply = BAD_REPLY
    proj_exists = False
    cu = current_user
    print("giveWorkbook(%s %s)" % (cu.id, project_name))
    proj = ProjectDb.query.filter_by(user_id=cu.id, name=project_name).first()
    db.session.close()
    if proj is None:
        reply['reason']='Project %s does not exist.' % project_name
        return jsonify(reply)
    else:
        D = proj.model
        wb_name = D['G']['workbookname']
        makeworkbook(wb_name, proj.populations, proj.programs, proj.datastart, proj.dataend, proj.econ_dataend)
        print("project %s template: %s" % (proj.name, wb_name))
        (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
        return helpers.send_from_directory(dirname, basename)

@project.route('/info')
@login_required
@check_project_name
def getProjectInformation():
    """
    Returns information of the requested project.

    Returns:
        A jsonified project dictionary accessible to the current user.
        In case of an anonymous user an object with status "NOK" is returned.
    """

    # default response
    response_data = { "status": "NOK" }

    if current_user.is_anonymous() == False:

        # see if there is matching project
        project = ProjectDb.query.filter_by(user_id=current_user.id,
            name=request.project_name).first()

        # update response
        if project is not None:
            response_data = {
                'status': "OK",
                'name': project.name,
                'dataStart': project.datastart,
                'dataEnd': project.dataend,
                'projectionStartYear': project.datastart,
                'projectionEndYear': project.econ_dataend,
                'programs': project.programs,
                'populations': project.populations,
                'creation_time': project.creation_time, 
                'data_upload_time':project.data_upload_time
            }

    return jsonify(response_data)

@project.route('/list')
@login_required
def getProjectList():
    """
    Returns the list of existing projects from db.

    Returns:
        A jsonified list of project dictionaries if the user is logged in.
        In case of an anonymous user an empty list will be returned.

    """
    projects_data = []
    # Get current user
    if current_user.is_anonymous() == False:

        # Get projects for current user
        projects = ProjectDb.query.filter_by(user_id=current_user.id)
        for project in projects:
            project_data = {
                'status': "OK",
                'name': project.name,
                'dataStart': project.datastart,
                'dataEnd': project.dataend,
                'projectionStartYear': project.datastart,
                'projectionEndYear': project.econ_dataend,
                'programs': project.programs,
                'populations': project.populations,
                'creation_time': project.creation_time,
                'data_upload_time': project.data_upload_time
            }
            projects_data.append(project_data)
        db.session.close()

    return jsonify({"projects": projects_data})

"""
Deletes the given project (and eventually, corresponding excel files)
"""
@project.route('/delete/<project_name>', methods=['DELETE'])
@login_required
@report_exception()
def deleteProject(project_name):
    print("deleteProject %s" % project_name)
    delete_spreadsheet(project_name)
    print("spreadsheets for %s deleted" % project_name)
    # Get current user
    user_id = current_user.id
    # Get project row for current user with project name
    proj = db.session.query(ProjectDb).filter_by(user_id= user_id,name=project_name).first()

    if proj is not None:
        id = proj.id
        db.session.query(WorkingProjectDb).filter_by(id=id).delete()
        db.session.query(ProjectDb).filter_by(id=id).delete()

    db.session.commit()

    return jsonify({'status':'OK','reason':'Project %s deleted.' % project_name})


"""
saves data as Excel file 
"""
@project.route('/export', methods=['POST'])
@login_required
@report_exception()
def exportGraph():
    from sim.makeworkbook import OptimaGraphTable
    data = json.loads(request.data)
    print("/api/project/export %s" % data)
    name = data['name']
    filename = name+'.xlsx'
    columns = data['columns']
    path = fullpath(filename)
    table = OptimaGraphTable(name, columns)
    table.create(path)
    print("exported table: %s to %s" % (name, path))
    (dirname, basename) = os.path.split(path)
    return helpers.send_file(path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


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
@report_exception()
def uploadExcel():
    from datetime import datetime
    import dateutil.tz
    project_name = request.project_name
    user_id = current_user.id
    print("uploadExcel(project name: %s user:%s)" % (project_name, user_id))

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

    source_filename = secure_filename(file.filename)
    if not allowed_file(source_filename):
        reply['reason'] = 'File type of %s is not accepted!' % source_filename
        return json.dumps(reply)

    reply['file'] = source_filename

    filename = project_name + '.xlsx'
    server_filename = os.path.join(loaddir, filename)
    file.save(server_filename)

    D = load_model(project_name)
    D = updatedata(D, savetofile = False)

    save_model(project_name, D)

    # See if there is matching project
    proj = ProjectDb.query.filter_by(user_id=user_id, name=project_name).first()
        
    # save data upload timestamp
    if proj is not None:
        proj.data_upload_time = datetime.now(dateutil.tz.tzutc())    
        
        # Save to db
        db.session.add(proj)
        db.session.commit()
    else:
        db.session.close()
            
    reply['status'] = 'OK'
    reply['result'] = 'Project %s is updated' % project_name
    return json.dumps(reply)
