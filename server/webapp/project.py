import json
from flask import Blueprint, helpers, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
import os
from dataio import upload_dir_user, TEMPLATEDIR, fullpath
# TODO fix after v2
# from sim.updatedata import updatedata
# TODO fix after v2
# from sim.makeproject import makeproject, makeworkbook
from server.webapp.utils import allowed_file, project_exists, delete_spreadsheet, load_project
from server.webapp.utils import check_project_name, report_exception, model_as_bunch, model_as_dict
from server.webapp.utils import verify_admin_request
from server.webapp.utils import load_model, save_model
from flask.ext.login import login_required, current_user # pylint: disable=E0611,F0401
from server.webapp.dbconn import db
from server.webapp.dbmodels import (ProjectDb, WorkingProjectDb, ProjectDataDb,
    WorkLogDb, ResultsDb, ParsetsDb)
import datetime
import dateutil.tz
from datetime import datetime
from copy import deepcopy
from optima.project import Project


# route prefix: /api/project
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
    from parameters import parameters
    project_parameters = [p for p in parameters() if 'modifiable' in p and p['modifiable']]
    return jsonify({"parameters":project_parameters})

@project.route('/predefined')
@login_required
def get_predefined():
    """
    Gives back default populations and programs
    """
    from optima.populations import populations
    populations = populations()
    for p in populations: p['active']= False
    return jsonify({"populations": populations})


def getPopsAndProgsFromModel(project_entry, trustInputMetadata): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Initializes "meta data" about populations and programs from model.
    keep_old_parameters (for program parameters) will be True if we import from Excel.
    """
    from sim.programs import programs
    from sim.populations import populations
    programs = programs()
    populations = populations()
    model = project_entry.model
    if not 'data' in model: return

    dict_programs = dict([(item['short_name'], item) for item in programs])

    # Update project_entry.populations and project_entry.programs
    D_pops = model['data']['meta']['pops']
    D_progs = model['data']['meta']['progs']
    D_pops_names = model['data']['meta']['pops']['short']
    D_progs_names = model['data']['meta']['progs']['short']
    old_programs_dict = dict([(item.get('short_name') if item else '', item) for item in project_entry.programs])

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

    project_entry.populations = pops
    project_entry.programs = progs
    years = model['data']['epiyears']
    #this is the new truth
    model['G']['inputprograms'] = progs
    model['G']['inputpopulations'] = pops
    project_entry.model = model
    project_entry.datastart = int(years[0])
    project_entry.dataend = int(years[-1])


@project.route('/create/', methods=['POST'])
@login_required
@report_exception()
def create_project(): # pylint: disable=too-many-locals
    """
    Creates the project with the given name and provided parameters.
    Result: on the backend, new project is stored,
    spreadsheet with specified name and parameters given back to the user.
    expects json with the following arguments (see example):
    {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}

    """

    # TODO deprecate project name from URI
    from optima.makespreadsheet import default_datastart, default_dataend, makespreadsheet
    from dataio import tojson, templatepath
    from optima.project import version
    raw_data = json.loads(request.data)
    data = raw_data.get('params') if raw_data else None
    # get current user
    user_id = current_user.id

    project_name = data.get('name')
    if not project_name:
        return jsonify({'reason':'Project name is missing'}), 400
    project_name = secure_filename(project_name)
    current_app.logger.debug("createProject %s for user %s" % (project_name, current_user.email))

    current_app.logger.debug("createProject data: %s" % data)

    makeproject_args = {"projectname":project_name, "savetofile":False}
    makeproject_args['datastart'] = data.get('datastart', default_datastart)
    makeproject_args['dataend'] = data.get('dataend', default_dataend)
    makeproject_args['pops'] = data.get('populations')
    current_app.logger.debug("createProject(%s)" % makeproject_args)

    # create new project
    current_app.logger.debug("Creating new project %s by user %s:%s" % (project_name, user_id, current_user.email))
    project_entry = ProjectDb(project_name, user_id, makeproject_args['datastart'], \
        makeproject_args['dataend'], \
        makeproject_args['pops'],
        version=version)
    current_app.logger.debug('Creating new project: %s' % project_entry.name)

    # Save to db
    current_app.logger.debug("About to persist project %s for user %s" % (project_entry.name, project_entry.user_id))
    db.session.add(project_entry)
    db.session.commit()
    new_project_template = project_name

    path = templatepath(project_name)
    makespreadsheet(path, pops=makeproject_args['pops'], datastart=makeproject_args['datastart'], dataend=makeproject_args['dataend'])

    current_app.logger.debug("new_project_template: %s" % new_project_template)
    (dirname, basename) = (upload_dir_user(TEMPLATEDIR), new_project_template)
    response = helpers.send_from_directory(dirname, basename)
    response.headers['X-project-id'] = project_entry.id
    return response


@project.route('/update/<project_id>', methods=['PUT'])
@login_required
@report_exception()
def update_project(project_id): # pylint: disable=too-many-locals,too-many-statements
    """
    Updates the project with the given id.
    This happens after users edit the project.

    """

    # TODO replace this with app.config
    DATADIR = current_app.config['UPLOAD_FOLDER']

    from dataio import projectpath, tojson
    current_app.logger.debug("updateProject %s for user %s" % (project_id, current_user.email))
    raw_data = json.loads(request.data)

    current_app.logger.debug("project %s is in edit mode" % project_id)
    current_app.logger.debug(raw_data)

    can_update = None
    data = None
    if raw_data:
        can_update = raw_data.get('canUpdate')
        data = raw_data.get('params')
    current_app.logger.debug("updateProject data: %s" % data)


    # Check whether we are editing a project
    project_entry = load_project(project_id) if project_id else None
    if not project_entry:
        return jsonify({'reason':'No such project %s' % project_id}), 404

    project_name = project_entry.name

    makeproject_args = {"projectname": project_name, "savetofile":False}
    # editing datastart & dataend currently is not allowed
    makeproject_args['datastart'] = project_entry.datastart
    makeproject_args['dataend'] = project_entry.dataend
    makeproject_args['progs'] = data.get('programs', project_entry.programs)
    makeproject_args['pops'] = data.get('populations', project_entry.populations)
    current_app.logger.debug("createProject(%s)" % makeproject_args)

    current_app.logger.debug("Editing project %s by user %s:%s" % (project_name, current_user.id, current_user.email))
    project_entry.programs = makeproject_args['progs']
    project_entry.populations = makeproject_args['pops']
    current_app.logger.debug('Updating existing project %s' % project_entry.name)

    D = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    #D should have inputprograms and inputpopulations corresponding to the entered data now
    project_entry.model = tojson(D)
    db.session.query(WorkingProjectDb).filter_by(id=project_entry.id).delete()
    if can_update and project_entry.project_data is not None and project_entry.project_data.meta is not None:
        # try to reload the data
        loaddir =  upload_dir_user(DATADIR)
        if not loaddir:
            loaddir = DATADIR
        filename = project_name + '.xlsx'
        server_filename = os.path.join(loaddir, filename)
        filedata = open(server_filename, 'wb')
        filedata.write(project_entry.project_data.meta)
        filedata.close()
        D = model_as_bunch(project_entry.model)
        #resave relevant metadata
        D['G']['projectname'] = project_entry.name
        D['G']['projectfilename'] = projectpath(project_entry.name+'.prj')
        D['G']['workbookname'] = D['G']['projectname'] + '.xlsx'
        D['G']['inputprograms'] = deepcopy(project_entry.programs)
        D['G']['inputpopulations'] = deepcopy(project_entry.populations)
        # TODO fix after v2
        # D = updatedata(D, input_programs = project_entry.programs, savetofile = False)
        #and now, because workbook was uploaded, we have to correct the programs and populations
        model = model_as_dict(D)
        project_entry.model = model
        getPopsAndProgsFromModel(project_entry, trustInputMetadata = False)
    else:
        db.session.query(ProjectDataDb).filter_by(id=project_entry.id).delete()

    # Save to db
    current_app.logger.debug("About to persist project %s for user %s" % (project_entry.name, project_entry.user_id))
    db.session.add(project_entry)
    db.session.commit()
    new_project_template = D['G']['workbookname']

    current_app.logger.debug("new_project_template: %s" % new_project_template)
    (dirname, basename) = (upload_dir_user(TEMPLATEDIR), new_project_template)
    response = helpers.send_from_directory(dirname, basename)
    response.headers['X-project-id'] = project_entry.id
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
    except: # pylint: disable=bare-except
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

    cu = current_user
    current_app.logger.debug("giveWorkbook(%s %s)" % (cu.id, project_id))
    project_entry = load_project(project_id)
    if project_entry is None:
        reply = {'reason':'Project %s does not exist.' % project_id}
        return jsonify(reply), 500
    else:
        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project_entry.id)

        if projdata is not None and len(projdata.meta)>0:
            return Response(projdata.meta,
                mimetype= 'application/octet-stream',
                headers={'Content-Disposition':'attachment;filename='+ project_entry.name+'.xlsx'})
        else:
        # if no project data found
            D = project_entry.model
            wb_name = D['G']['workbookname']
            # TODO fix after v2
            # makeworkbook(wb_name, project_entry.populations, project_entry.programs, \
            #     project_entry.datastart, project_entry.dataend)
            current_app.logger.debug("project %s template created: %s" % (project_entry.name, wb_name))
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
    project_entry = load_project(request.project_id)
    # update response
    if project_entry is not None:
        reply = {
            'id': project_entry.id,
            'name': project_entry.name,
            'dataStart': project_entry.datastart,
            'dataEnd': project_entry.dataend,
            'populations': project_entry.populations,
            'creation_time': project_entry.created,
            'updated_time': project_entry.updated,
            'data_upload_time': project_entry.data_upload_time(),
            'has_data': project_entry.has_data()
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
        for project_entry in projects:
            project_data = {
                'id': project_entry.id,
                'name': project_entry.name,
                'dataStart': project_entry.datastart,
                'dataEnd': project_entry.dataend,
                'populations': project_entry.populations,
                'creation_time': project_entry.created,
                'updated_time': project_entry.updated,
                'data_upload_time': project_entry.data_upload_time(),
                'user_id': project_entry.user_id
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
        for project_entry in projects:
            project_data = {
                'id': project_entry.id,
                'name': project_entry.name,
                'dataStart': project_entry.datastart,
                'dataEnd': project_entry.dataend,
                'populations': project_entry.populations,
                'creation_time': project_entry.created,
                'updated_time': project_entry.updated,
                'data_upload_time': project_entry.data_upload_time()
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
    project_entry = load_project(project_id)
    project_name = None
    user_id = current_user.id

    if project_entry is not None:
        user_id = project_entry.user_id
        project_name = project_entry.name
        str_project_id = str(project_entry.id)
        #delete all relevant entries explicitly
        db.session.query(WorkLogDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProjectDataDb).filter_by(id=str_project_id).delete()
        db.session.query(WorkingProjectDb).filter_by(id=str_project_id).delete()
        db.session.query(ResultsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ParsetsDb).filter_by(project_id=str_project_id).delete()
        db.session.query(ProjectDb).filter_by(id=str_project_id).delete()
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
    from sqlalchemy.orm.session import make_transient
    from dataio import projectpath
    new_project_name = request.args.get('to')
    if not new_project_name:
        reply = {'reason': 'New project name is not given'}
        return jsonify(reply), 500
    # Get project row for current user with project name
    project_entry = load_project(project_id, all_data = True)
    if project_entry is None:
        reply = {'reason': 'Project %s does not exist.' % project_id}
        return jsonify(reply), 500
    project_user_id = project_entry.user_id

    # force load the existing data, parset and result
    project_data_exists = project_entry.project_data
    project_parset_exists = project_entry.parsets
    project_result_exists = project_entry.results

    db.session.expunge(project_entry)
    make_transient(project_entry)

    project_entry.id = None
    project_entry.name = new_project_name

    #change the creation and update time
    project_entry.created = datetime.now(dateutil.tz.tzutc())
    project_entry.updated = datetime.now(dateutil.tz.tzutc())
    # Question, why not use datetime.utcnow() instead of dateutil.tz.tzutc()?
    # it's the same, without the need to import more
    db.session.add(project_entry)
    db.session.flush()  # this updates the project ID to the new value
    new_project_id = project_entry.id

    if project_data_exists:
        # copy the project data
        db.session.expunge(project_entry.project_data)
        make_transient(project_entry.project_data)
        db.session.add(project_entry.project_data)

    if project_parset_exists:
        # copy each parset
        for parset in project_entry.parsets:
            db.session.expunge(parset)
            make_transient(parset)
            # set the id to None to ensure no duplicate ID
            parset.id = None
            db.session.add(parset)

    if project_result_exists:
        # copy each result
        for result in project_entry.results:
            db.session.expunge(result)
            make_transient(result)
            # set the id to None to ensure no duplicate ID
            result.id = None
            db.session.add(result)
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
def uploadExcel(): # pylint: disable=too-many-locals
    """
    Uploads Excel file, uses it to update the corresponding model.
    Precondition: model should exist.
    """

    # TODO replace this with app.config
    DATADIR = current_app.config['UPLOAD_FOLDER']

    from dataio import projectpath
    current_app.logger.debug("api/project/update")
    project_name = request.project_name
    project_id = request.project_id
    user_id = current_user.id
    current_app.logger.debug("uploadExcel(project id: %s user:%s)" % (project_id, user_id))

    uploaded_file = request.files['file']

    # getting current user path
    loaddir =  upload_dir_user(DATADIR)
    if not loaddir:
        loaddir = DATADIR
    if not uploaded_file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(uploaded_file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    filename = project_name + '.xlsx'
    server_filename = os.path.join(loaddir, filename)
    uploaded_file.save(server_filename)

    # See if there is matching project
    project_entry = load_project(project_id)
    current_app.logger.debug("project for user %s name %s: %s" % (current_user.id, project_name, project_entry))
    if project_entry is not None:
        from optima.utils import saves  # , loads
        # from optima.parameters import Parameterset
        from dbmodels import ParsetsDb, ResultsDb
        new_project = project_entry.hydrate()
        new_project.loadspreadsheet(server_filename)
        new_project.modified = datetime.now(dateutil.tz.tzutc())
        current_app.logger.info("after spreadsheet uploading: %s" % new_project)
        # TODO: figure out whether we still have to do anything like that
#        D['G']['inputpopulations'] = deepcopy(project_entry.populations)

        # Is this the first time? if so then we have to run simulations
#        should_re_run = 'S' not in D

        # TODO call new_project.runsim instead
        result = new_project.runsim()
        current_app.logger.info("runsim result for project %s: %s" % (project_id, result))

        # D = updatedata(D, input_programs = project_entry.programs, savetofile=False, rerun=should_re_run)
#       now, update relevant project_entry fields
        project_entry.settings = saves(new_project.settings)
        project_entry.data = saves(new_project.data)
        project_entry.created = new_project.created
        project_entry.updated = new_project.modified

        #update the programs and populations based on the data TODO: yes or no?
#        getPopsAndProgsFromModel(project_entry, trustInputMetadata = False)

        db.session.add(project_entry)

        # save data upload timestamp
        data_upload_time = datetime.now(dateutil.tz.tzutc())
        # get file data
        filedata = open(server_filename, 'rb').read()
        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project_entry.id)

        # update parsets
        result_parset_id = None
        parset_records_map = {record.id:record for record in project_entry.parsets} # may be SQLAlchemy can do stuff like this already?
        for (parset_name, parset_entry) in new_project.parsets.iteritems():
            parset_record = parset_records_map.get(parset_entry.uuid)
            if not parset_record: parset_record = ParsetsDb(project_id=project_entry.id, name = parset_name, id = parset_entry.uuid)
            if parset_record.name=="default": result_parset_id = parset_entry.uuid
            parset_record.pars = saves(parset_entry.pars)
            db.session.add(parset_record)

        # update results (after runsim is invoked)
        results_map = {(record.parset_id, record.calculation_type):record for record in project_entry.results}
        result_record = results_map.get((result_parset_id, "simulation"))
        if not result_record: result_record = ResultsDb(
            parset_id = result_parset_id,
            project_id = project_entry.id,
            calculation_type = "simulation",
            blob = saves(result)
            )
        db.session.add(result_record)

        # update existing
        if projdata is not None:
            projdata.meta = filedata
            projdata.upload_time = data_upload_time
        else:
            # create new project data
            projdata = ProjectDataDb(project_entry.id, filedata, data_upload_time)

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
    Download data for the project with the given name.
    expects project name (project should already exist)
    if project exists, returns data (aka D) for it
    if project does not exist, returns an error.

    """
    current_app.logger.debug("/api/project/data/%s" % project_id)
    project_entry = load_project(project_id)
    if project_entry is None:
        reply = {'reason': 'Project %s does not exist.' % project_id }
        return jsonify(reply), 500
    else:
        new_project = project_entry.hydrate()

        # return result as a file
        loaddir =  upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR
        filename = project_entry.name + '.prj'
        server_filename = os.path.join(loaddir, filename)

        from optima.utils import save
        save(server_filename, new_project)

        return helpers.send_from_directory(loaddir, filename)

@project.route('/data', methods=['POST'])
@login_required
@report_exception('Unable to copy uploaded data')
def createProjectAndSetData():
    """ Creates a project & uploads data file to update project model. """
    from optima.project import version
    user_id = current_user.id
    project_name = request.values.get('name')
    if not project_name:
        reply = {'reason': 'No project name provided'}
        return jsonify(reply), 500

    uploaded_file = request.files['file']

    if not uploaded_file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(uploaded_file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    from optima.utils import load
    new_project = load(uploaded_file)

    if new_project.data:
        datastart = int(new_project.data['years'][0])
        dataend = int(new_project.data['years'][-1])
        pops = []
        project_pops = new_project.data['pops']
        print "pops", project_pops
        for i in range(len(project_pops['short'])):
            print "i", i
            new_pop = {'name': project_pops['long'][i], 'short_name': project_pops['short'][i],
            'female': project_pops['female'][i], 'male':project_pops['male'][i],
            'age_from': int(project_pops['age'][i][0]), 'age_to': int(project_pops['age'][i][1])}
            pops.append(new_pop)
    else:
        from optima.makespreadsheet import default_datastart, default_dataend
        datastart = default_datastart
        dataend = default_dataend
        pops = {}

    project_entry = ProjectDb(project_name, user_id, datastart,
        dataend,
        pops,
        version=version)

    project_entry.restore(new_project)
    project_entry.name = project_name

    db.session.add(project_entry)
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
    uploaded_file = request.files['file']

    if not uploaded_file:
        reply = {'reason': 'No file is submitted!'}
        return jsonify(reply), 500

    source_filename = secure_filename(uploaded_file.filename)
    if not allowed_file(source_filename):
        reply = {'reason': 'File type of %s is not accepted!' % source_filename}
        return jsonify(reply), 500

    project_entry = load_project(project_id)
    if project_entry is None:
        reply = {'reason': 'Project %s does not exist.' % project_id}
        return jsonify(reply), 500

    from optima.utils import load
    new_project = load(uploaded_file)
    project_entry.restore(new_project)
    db.session.add(project_entry)

    db.session.commit()

    reply = {
        'file': source_filename,
        'result': 'Project %s is updated' % project_entry.name,
    }
    return jsonify(reply)


@project.route('/data/migrate', methods=['POST'])
@verify_admin_request
def migrateData():
    """
    Goes over all available projects and tries to run specified migration on them
    """
    import versioning
    from sim.makeproject import current_version
    for row in db.session.execute(
        "select distinct id from projects where (model->'G'->>'version')::text!=':val'", {'val':current_version}):
        print "row", row
        project_id = row[0]
        print "project_id", project_id
        model = load_model(project_id, from_json = False)
        model = versioning.run_migrations(model)
        if model is not None: save_model(project_id, model)
    return 'OK'
