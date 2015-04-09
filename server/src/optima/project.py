import json
from flask import Blueprint, url_for, helpers, request, jsonify, redirect, current_app, Response, flash
from werkzeug.utils import secure_filename
import os
import traceback
from sim.dataio import upload_dir_user, DATADIR, TEMPLATEDIR, fullpath
from sim.updatedata import updatedata
from sim.makeproject import makeproject, makeworkbook
from utils import allowed_file, project_exists, delete_spreadsheet, load_project
from utils import check_project_name, load_model, save_model, report_exception, model_as_bunch, model_as_dict
from utils import verify_admin_request
from flask.ext.login import login_required, current_user
from dbconn import db
from dbmodels import ProjectDb, WorkingProjectDb, ProjectDataDb, WorkLogDb
from utils import load_model, save_model
import time,datetime
import dateutil.tz
from datetime import datetime
from copy import deepcopy

""" route prefix: /api/project """
project = Blueprint('project',  __name__, static_folder = '../static')
project.config = {}

@project.record
def record_params(setup_state):
  app = setup_state.app
  project.config = dict([(key,value) for (key,value) in app.config.iteritems()])

@project.route('/parameters')
@login_required
def get_project_parameters():
    """
    Gives back project parameters (modifiable)
    """
    from sim.parameters import parameters
    project_parameters = [p for p in parameters() if 'modifiable' in p and p['modifiable']]
    return jsonify({"parameters":project_parameters})

@project.route('/predefined')
@login_required
def get_predefined():
    """
    Gives back default populations and programs
    """
    from sim.programs import programs, program_categories
    from sim.populations import populations
    programs = programs()
    populations = populations()
    program_categories = program_categories()
    for p in populations: p['active']= False
    for p in programs:
        p['active'] = False
        new_parameters = [dict([('value', parameter),('active',True)]) for parameter in p['parameters']]
        if new_parameters: p['parameters'] = new_parameters
    return jsonify({"programs":programs, "populations": populations, "categories":program_categories})


def getPopsAndProgsFromModel(project, trustInputMetadata):
    """
    Initializes "meta data" about populations and programs from model.
    keep_old_parameters (for program parameters) will be True if we import from Excel.
    """
    from sim.programs import programs
    from sim.populations import populations
    programs = programs()
    populations = populations()
    model = project.model
    if not 'data' in model: return

    dict_programs = dict([(item['short_name'], item) for item in programs])
    dict_populations = dict([(item['short_name'], item) for item in populations])

    # Update project.populations and project.programs
    D_pops = model['data']['meta']['pops']
    D_progs = model['data']['meta']['progs']
    D_pops_names = model['data']['meta']['pops']['short']
    D_progs_names = model['data']['meta']['progs']['short']
    old_populations_dict = dict([(item.get('short_name') if item else '', item) for item in project.populations])
    old_programs_dict = dict([(item.get('short_name') if item else '', item) for item in project.programs])
    D_progs_with_effects = model['programs']

    # get and generate populations from D.data.meta
    pops = []
    if trustInputMetadata and model['G'].get('inputpopulations'):
        pops = deepcopy(model['G']['inputpopulations'])
    else:
        for index, short_name in enumerate(D_pops_names):
            new_item = {}
            new_item['name'] = D_pops['long'][index]
            new_item['short_name'] = short_name
            for prop in ['sexworker','injects','sexmen','client','female','male','sexwomen']:
                new_item[prop] = bool(D_pops[prop][index])
            pops.append(new_item)

    # get and generate programs from D.data.meta
    progs = []
    if trustInputMetadata and model['G'].get('inputprograms'):
        progs = deepcopy(model['G']['inputprograms']) #if there are already parameters
    else:
        # we should try to rebuild the inputprograms
        for index, short_name in enumerate(D_progs_names):
            new_item = {}
            new_item['name'] = D_progs['long'][index]
            new_item['short_name'] = short_name
            new_item['parameters'] = []
            new_item['category'] = 'Other'
            old_program = old_programs_dict.get(short_name)
            if old_program: #if the program was given in create_project, keep the parameters
                new_item['category'] = old_program['category']
                new_item['parameters'] = deepcopy(old_program['parameters'])
            else:
                standard_program = dict_programs.get(short_name)
                if standard_program:
                    new_item['category'] = standard_program['category']
                    new_parameters = [{'value': parameter} for parameter in standard_program['parameters']]
                    for parameter in new_parameters:
                        if parameter['value']['pops']==['']: parameter['value']['pops']=list(D_pops_names)
                    if new_parameters: new_item['parameters'] = deepcopy(new_parameters)

            progs.append(new_item)

    project.populations = pops
    project.programs = progs
    years = model['data']['epiyears']
    #this is the new truth
    model['G']['inputprograms'] = progs
    model['G']['inputpopulations'] = pops
    project.model = model
    project.datastart = int(years[0])
    project.dataend = int(years[-1])


@project.route('/create/<project_name>', methods=['POST'])
@login_required
@report_exception()
def create_project(project_name):
    """
    Creates the project with the given name and provided parameters.
    Result: on the backend, new project is stored,
    spreadsheet with specified name and parameters given back to the user.
    expects json with the following arguments (see example):
    {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}

    """
    from sim.makeproject import default_datastart, default_dataend, default_pops, default_progs
    from sim.runsimulation import runsimulation
    from sim.dataio import tojson
    current_app.logger.debug("createProject %s for user %s" % (project_name, current_user.email))
    raw_data = json.loads(request.data)
    # get current user
    user_id = current_user.id

    data = raw_data.get('params') if raw_data else None
    current_app.logger.debug("createProject data: %s" % data)

    makeproject_args = {"projectname":project_name, "savetofile":False}
    makeproject_args['datastart'] = data.get('datastart', default_datastart)
    makeproject_args['dataend'] = data.get('dataend', default_dataend)
    makeproject_args['progs'] = data.get('programs', default_progs)
    makeproject_args['pops'] = data.get('populations', default_pops)
    current_app.logger.debug("createProject(%s)" % makeproject_args)

    # create new project
    current_app.logger.debug("Creating new project %s by user %s:%s" % (project_name, user_id, current_user.email))
    project = ProjectDb(project_name, user_id, makeproject_args['datastart'], \
        makeproject_args['dataend'], \
        makeproject_args['progs'], makeproject_args['pops'])
    current_app.logger.debug('Creating new project: %s' % project.name)

    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    project.model = tojson(D)

    # Save to db
    current_app.logger.debug("About to persist project %s for user %s" % (project.name, project.user_id))
    db.session.add(project)
    db.session.commit()
    new_project_template = D['G']['workbookname']

    current_app.logger.debug("new_project_template: %s" % new_project_template)
    (dirname, basename) = (upload_dir_user(TEMPLATEDIR), new_project_template)
    response = helpers.send_from_directory(dirname, basename)
    response.headers['X-project-id'] = project.id
    return response


@project.route('/update/<project_id>', methods=['PUT'])
@login_required
@report_exception()
def update_project(project_id):
    """
    Updates the project with the given id.
    This happens after users edit the project.

    """

    from sim.makeproject import default_datastart, default_dataend, default_pops, default_progs
    from sim.runsimulation import runsimulation
    from sim.dataio import projectpath, tojson
    current_app.logger.debug("updateProject %s for user %s" % (project_id, current_user.email))
    raw_data = json.loads(request.data)
    # get current user
    user_id = current_user.id

    current_app.logger.debug("project %s is in edit mode" % project_id)
    current_app.logger.debug(raw_data)

    can_update = None
    data = None
    if raw_data:
        can_update = raw_data.get('canUpdate')
        data = raw_data.get('params')
    current_app.logger.debug("updateProject data: %s" % data)


    # Check whether we are editing a project
    project = load_project(project_id) if project_id else None
    if not project:
        return jsonify({'reason':'No such project %s' % project_id}), 404

    project_name = project.name

    makeproject_args = {"projectname": project_name, "savetofile":False}
    # editing datastart & dataend currently is not allowed
    makeproject_args['datastart'] = project.datastart
    makeproject_args['dataend'] = project.dataend
    makeproject_args['progs'] = data.get('programs', project.programs)
    makeproject_args['pops'] = data.get('populations', project.populations)
    current_app.logger.debug("createProject(%s)" % makeproject_args)

    current_app.logger.debug("Editing project %s by user %s:%s" % (project_name, current_user.id, current_user.email))
    project.programs = makeproject_args['progs']
    project.populations = makeproject_args['pops']
    current_app.logger.debug('Updating existing project %s' % project.name)
    # to make sure we keep the existing user id when an admin is editing
    user_id = project.user_id

    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    #D should have inputprograms and inputpopulations corresponding to the entered data now
    project.model = tojson(D)
    db.session.query(WorkingProjectDb).filter_by(id=project.id).delete()
    if can_update and project.project_data is not None and project.project_data.meta is not None:
        # try to reload the data
        loaddir =  upload_dir_user(DATADIR)
        if not loaddir:
            loaddir = DATADIR
        filename = project_name + '.xlsx'
        server_filename = os.path.join(loaddir, filename)
        filedata = open(server_filename, 'wb')
        filedata.write(project.project_data.meta)
        filedata.close()
        D = model_as_bunch(project.model)
        #resave relevant metadata
        D['G']['projectname'] = project.name
        D['G']['projectfilename'] = projectpath(project.name+'.prj')
        D['G']['workbookname'] = D['G']['projectname'] + '.xlsx'
        D['G']['inputprograms'] = deepcopy(project.programs)
        D['G']['inputpopulations'] = deepcopy(project.populations)
        D = updatedata(D, input_programs = project.programs, savetofile = False)
        #and now, because workbook was uploaded, we have to correct the programs and populations
        model = model_as_dict(D)
        project.model = model
        getPopsAndProgsFromModel(project, trustInputMetadata = False)
    else:
        db.session.query(ProjectDataDb).filter_by(id=project.id).delete()

    # Save to db
    current_app.logger.debug("About to persist project %s for user %s" % (project.name, project.user_id))
    db.session.add(project)
    db.session.commit()
    new_project_template = D['G']['workbookname']

    current_app.logger.debug("new_project_template: %s" % new_project_template)
    (dirname, basename) = (upload_dir_user(TEMPLATEDIR), new_project_template)
    response = helpers.send_from_directory(dirname, basename)
    response.headers['X-project-id'] = project.id
    return response

@project.route('/open/<project_id>')
@login_required
def openProject(project_id):
    """
    Opens the project with the given ID.
    If the project exists, notifies the user about success.
    expects project ID,
    todo: only if it can be found
    """
    proj_exists = False
    try: #first check DB
        proj_exists = project_exists(project_id)
        current_app.logger.debug("proj_exists: %s" % proj_exists)
    except:
        proj_exists = False
    if not proj_exists:

        return jsonify({'reason':'No such project %s' % project_id}), 500
    else:
        return jsonify({})

@project.route('/workbook/<project_id>')
@login_required
@report_exception()
def giveWorkbook(project_id):
    """
    Generates workbook for the project with the given name.
    expects project name (project should already exist)
    if project exists, regenerates workbook for it
    if project does not exist, returns an error.
    """

    proj_exists = False
    cu = current_user
    current_app.logger.debug("giveWorkbook(%s %s)" % (cu.id, project_id))
    project = load_project(project_id)
    if project is None:
        reply = {'reason':'Project %s does not exist.' % project_id}
        return jsonify(reply), 500
    else:
        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project.id)

        if projdata is not None and len(projdata.meta)>0:
            return Response(projdata.meta,
                mimetype= 'application/octet-stream',
                headers={'Content-Disposition':'attachment;filename='+ project.name+'.xlsx'})
        else:
        # if no project data found
            D = project.model
            wb_name = D['G']['workbookname']
            makeworkbook(wb_name, project.populations, project.programs, \
                project.datastart, project.dataend)
            current_app.logger.debug("project %s template created: %s" % (project.name, wb_name))
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
            #deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename)

@project.route('/info')
@login_required
@check_project_name
def getProjectInformation():
    """
    Returns information of the requested project. (Including status of the model)

    Returns:
        A jsonified project dictionary accessible to the current user.
        In case of an anonymous user an object an error response is returned.
    """

    # see if there is matching project
    project = load_project(request.project_id)
    # update response
    if project is not None:
        reply = {
            'id': project.id,
            'name': project.name,
            'dataStart': project.datastart,
            'dataEnd': project.dataend,
            'programs': project.programs,
            'populations': project.populations,
            'creation_time': project.creation_time,
            'updated_time': project.updated_time,
            'data_upload_time': project.data_upload_time(),
            'has_data': project.has_data(),
        }
        return jsonify(reply)
    else:
        reply = {'reason': 'Project %s does not exist' % request.project_id}
        return jsonify(reply), 500

@project.route('/list/all')
@login_required
@verify_admin_request
def getProjectListAll():
    """
    Returns the list of existing projects from db.

    Returns:
        A jsonified list of project dictionaries if the user is logged in.
        In case of an anonymous user an empty list will be returned.

    """
    projects_data = []
    # Get current user
    if current_user.is_anonymous() == False:

        # Get projects for all users, if the user is admin
        projects = ProjectDb.query.all()
        for project in projects:
            project_data = {
                'id': project.id,
                'name': project.name,
                'dataStart': project.datastart,
                'dataEnd': project.dataend,
                'programs': project.programs,
                'populations': project.populations,
                'creation_time': project.creation_time,
                'updated_time': project.updated_time,
                'data_upload_time': project.data_upload_time(),
                'user_id': project.user_id
            }
            projects_data.append(project_data)

    return jsonify({"projects": projects_data})


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
                'id': project.id,
                'name': project.name,
                'dataStart': project.datastart,
                'dataEnd': project.dataend,
                'programs': project.programs,
                'populations': project.populations,
                'creation_time': project.creation_time,
                'updated_time': project.updated_time,
                'data_upload_time': project.data_upload_time()
            }
            projects_data.append(project_data)

    return jsonify({"projects": projects_data})

@project.route('/delete/<project_id>', methods=['DELETE'])
@login_required
@report_exception()
def deleteProject(project_id):
    """
    Deletes the given project (and eventually, corresponding excel files)
    """
    current_app.logger.debug("deleteProject %s" % project_id)
    # only loads the project if current user is either owner or admin
    project = load_project(project_id)
    project_name = None
    user_id = current_user.id

    if project is not None:
        id = project.id
        user_id = project.user_id
        project_name = project.name
        #delete all relevant entries explicitly
        db.session.query(WorkLogDb).filter_by(project_id=id).delete()
        db.session.query(ProjectDataDb).filter_by(id=id).delete()
        db.session.query(WorkingProjectDb).filter_by(id=id).delete()
        db.session.query(ProjectDb).filter_by(id=id).delete()
    db.session.commit()
    current_app.logger.debug("project %s is deleted by user %s" % (project_id, current_user.id))
    delete_spreadsheet(project_name)
    if (user_id!=current_user.id):delete_spreadsheet(project_name, user_id)
    current_app.logger.debug("spreadsheets for %s deleted" % project_name)

    return jsonify({'result':'Project %s deleted.' % project_name})

@project.route('/copy/<project_id>', methods=['POST'])
@login_required
@report_exception()
def copyProject(project_id):
    """
    Copies the given project to a different name
    usage: /api/project/copy/<project_id>?to=<new_project_name>
    """
    from sqlalchemy.orm.session import make_transient, make_transient_to_detached
    from sim.dataio import projectpath
    new_project_name = request.args.get('to')
    if not new_project_name:
        reply = {'reason': 'New project name is not given'}
        return jsonify(reply), 500
    # Get project row for current user with project name
    project = load_project(project_id, all_data = True)
    if project is None:
        reply = {'reason': 'Project %s does not exist.' % project_id}
        return jsonify(reply), 500
    project_user_id = project.user_id
    project_data_exists = project.project_data #force loading it
    db.session.expunge(project)
    make_transient(project)
    project.id = None
    project.name = new_project_name
    #also change all the relevant metadata
    project.model['G']['projectname'] = project.name
    project.model['G']['projectfilename'] = projectpath(project.name+'.prj')
    project.model['G']['workbookname'] = project.name + '.xlsx'
    db.session.add(project)
    db.session.flush() #this updates the project ID to the new value
    new_project_id = project.id
    if project_data_exists:
        db.session.expunge(project.project_data) # it should have worked without that black magic. but it didn't.
        make_transient(project.project_data)
        db.session.add(project.project_data)
    db.session.commit()
    # let's not copy working project, it should be either saved or discarded
    return jsonify({'project':project_id, 'user':project_user_id, 'copy_id':new_project_id})

@project.route('/export', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def exportGraph():
    """
    saves data as Excel file
    """
    from sim.makeworkbook import OptimaGraphTable
    data = json.loads(request.data)

    sheet = [{
        "name": data['name'],
        "columns":data['columns']
    }]
    path = fullpath(data['name'] + '.xlsx' )
    table = OptimaGraphTable(sheet)
    table.create(path)
    (dirname, basename) = os.path.split(path)
    return helpers.send_file(path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@project.route('/exportall', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def exportAllGraphs():
    """
    saves All data as Excel files
    """
    from sim.makeworkbook import OptimaGraphTable

    data = json.loads(request.data)
    project_name = request.project_name
    name = project_name
    filename = name+'.xlsx'
    path = fullpath(filename)
    table = OptimaGraphTable(data) # data => sheets
    table.create(path)
    (dirname, basename) = os.path.split(path)
    return helpers.send_file(path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@project.route('/download/<downloadName>', methods=['GET'])
@login_required
def downloadExcel(downloadName):
    """
    Download example Excel file.
    """
    example_excel_file_name = 'example.xlsx'

    file_path = helpers.safe_join(project.static_folder, example_excel_file_name)
    options = {
        'cache_timeout': project.get_send_file_max_age(example_excel_file_name),
        'conditional': True,
        'attachment_filename': downloadName
    }
    return helpers.send_file(file_path, **options)

@project.route('/update', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def uploadExcel():
    """
    Uploads Excel file, uses it to update the corresponding model.
    Precondition: model should exist.
    """
    from sim.runsimulation import runsimulation
    from sim.dataio import projectpath
    current_app.logger.debug("api/project/update")
    project_name = request.project_name
    project_id = request.project_id
    user_id = current_user.id
    current_app.logger.debug("uploadExcel(project id: %s user:%s)" % (project_id, user_id))

    file = request.files['file']

    # getting current user path
    loaddir =  upload_dir_user(DATADIR)
    if not loaddir:
        loaddir = DATADIR
    if not file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    filename = project_name + '.xlsx'
    server_filename = os.path.join(loaddir, filename)
    file.save(server_filename)

    # See if there is matching project
    project = load_project(project_id)
    current_app.logger.debug("project for user %s name %s: %s" % (current_user.id, project_name, project))
    if project is not None:
        # update and save model
        D = model_as_bunch(project.model)
        #make sure we get project name and relevant fields up-to-date
        D['G']['projectname'] = project.name
        D['G']['projectfilename'] = projectpath(project.name+'.prj')
        D['G']['workbookname'] = D['G']['projectname'] + '.xlsx'
        D['G']['inputprograms'] = deepcopy(project.programs)
        D['G']['inputpopulations'] = deepcopy(project.populations)

        # Is this the first time? if so then we have to run simulations
        should_re_run = 'S' not in D

        D = updatedata(D, input_programs = project.programs, savetofile = False, rerun = should_re_run)
        model = model_as_dict(D)
        project.model = model
        #update the programs and populations based on the data
        getPopsAndProgsFromModel(project, trustInputMetadata = False)

        db.session.add(project)

        # save data upload timestamp
        data_upload_time = datetime.now(dateutil.tz.tzutc())
        # get file data
        filedata = open(server_filename, 'rb').read()
        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project.id)

        # update existing
        if projdata is not None:
            projdata.meta = filedata
            projdata.upload_time = data_upload_time
        else:
            # create new project data
            projdata = ProjectDataDb(project.id, filedata, data_upload_time)

        # Save to db
        db.session.add(projdata)
        db.session.commit()

    reply = {'file': source_filename, 'result': 'Project %s is updated' % project_name}
    return jsonify(reply)

@project.route('/data/<project_id>')
@login_required
@report_exception()
def getData(project_id):
    """
    download data for the project with the given name.
    expects project name (project should already exist)
    if project exists, returns data (aka D) for it
    if project does not exist, returns an error.
    """
    proj_exists = False
    current_app.logger.debug("/api/project/data/%s" % project_id)
    project = load_project(project_id)
    if project is None:
        reply = {'reason': 'Project %s does not exist.' % project_id }
        return jsonify(reply), 500
    else:
        data = project.model
        #make sure this exists
        data['G']['inputprograms'] = project.programs
        data['G']['inputpopulations'] = project.populations
        # return result as a file
        loaddir =  upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR
        filename = project.name + '.json'
        server_filename = os.path.join(loaddir, filename)
        with open(server_filename, 'wb') as filedata:
            json.dump(data, filedata)
        return helpers.send_from_directory(loaddir, filename)

@project.route('/data', methods=['POST'])
@login_required
@report_exception('Unable to copy uploaded data')
def createProjectAndSetData():
    """
    Creates a project & uploads data file to update project model.
    """
    user_id = current_user.id
    project_name = request.values.get('name')
    if not project_name:
        reply = {'reason': 'No project name provided'}
        return jsonify(reply), 500

    file = request.files['file']

    if not file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    data = json.load(file)

    project = ProjectDb(project_name, user_id, data['G']['datastart'], \
        data['G']['dataend'], \
        data['G']['inputprograms'], data['G']['inputpopulations'])
    project.model = data
    getPopsAndProgsFromModel(project, trustInputMetadata = True)

    db.session.add(project)
    db.session.commit()

    reply = {'file': source_filename, 'result': 'Project %s is updated' % project_name}
    return jsonify(reply)


@project.route('/data/<project_id>', methods=['POST'])
@login_required
@report_exception('Unable to copy uploaded data')
def setData(project_id):
    """
    Uploads Data file, uses it to update the project model.
    Precondition: model should exist.
    """
    user_id = current_user.id
    current_app.logger.debug("uploadProject(project id: %s user:%s)" % (project_id, user_id))
    file = request.files['file']

    if not file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    project = load_project(project_id)
    if project is None:
        reply = {'reason': 'Project %s does not exist.' % project_id}
        return jsonify(reply), 500

    data = json.load(file)
    data['G']['projectfilename'] = project.model['G']['projectfilename']
    data['G']['workbookname'] = project.model['G']['workbookname']
    data['G']['projectname'] = project.model['G']['projectname']
    project.model = data
    project_name = project.name
    getPopsAndProgsFromModel(project, trustInputMetadata = True)

    db.session.add(project)
    db.session.commit()

    reply = {'file': source_filename, 'result': 'Project %s is updated' % project_name}
    return jsonify(reply)

@project.route('/data/migrate', methods=['POST'])
@verify_admin_request
def migrateData():
    """
    Goes over all available projects and tries to run specified migration on them
    """
    import versioning
    for project_id in db.session.query(ProjectDb.id).distinct():
        print "project_id", project_id
        model = load_model(project_id, from_json = False)
        model = versioning.run_migrations(model)
        if model is not None: save_model(project_id, model)
    return 'OK'
