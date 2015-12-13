import os

from copy import deepcopy
from flask import current_app
from flask import helpers
from flask import json
from flask import request
from flask.ext.login import current_user
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.dataio import TEMPLATEDIR
from server.webapp.dataio import projectpath
from server.webapp.dataio import upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDataDb
from server.webapp.dbmodels import ProjectDb
from server.webapp.dbmodels import WorkingProjectDb
from server.webapp.exceptions import ProjectNotFound
from server.webapp.utils import load_project
from server.webapp.utils import model_as_bunch
from server.webapp.utils import model_as_dict
from server.webapp.utils import project_exists


def getPopsAndProgsFromModel(project_entry, trustInputMetadata):
    """
    Initializes "meta data" about populations and programs from model.
    keep_old_parameters (for program parameters)
    will be True if we import from Excel.
    """
    from sim.programs import programs
    from sim.populations import populations
    programs = programs()
    populations = populations()
    model = project_entry.model
    if 'data' not in model:
        return

    dict_programs = dict([(item['short_name'], item) for item in programs])

    # Update project_entry.populations and project_entry.programs
    D_pops = model['data']['meta']['pops']
    D_progs = model['data']['meta']['progs']
    D_pops_names = model['data']['meta']['pops']['short']
    D_progs_names = model['data']['meta']['progs']['short']
    old_programs_dict = dict(
        [(item.get('short_name') if item else '', item) for item in project_entry.programs])

    # get and generate populations from D.data.meta
    pops = []
    if trustInputMetadata and model['G'].get('inputpopulations'):
        pops = deepcopy(model['G']['inputpopulations'])
    else:
        for index, short_name in enumerate(D_pops_names):
            new_item = {}
            new_item['name'] = D_pops['long'][index]
            new_item['short_name'] = short_name
            for prop in ['sexworker', 'injects', 'sexmen', 'client', 'female', 'male', 'sexwomen']:
                new_item[prop] = bool(D_pops[prop][index])
            pops.append(new_item)

    # get and generate programs from D.data.meta
    progs = []
    if trustInputMetadata and model['G'].get('inputprograms'):
        # if there are already parameters
        progs = deepcopy(model['G']['inputprograms'])
    else:
        # we should try to rebuild the inputprograms
        for index, short_name in enumerate(D_progs_names):
            new_item = {}
            new_item['name'] = D_progs['long'][index]
            new_item['short_name'] = short_name
            new_item['parameters'] = []
            new_item['category'] = 'Other'
            old_program = old_programs_dict.get(short_name)
            # if the program was given in create_project, keep the parameters
            if old_program:
                new_item['category'] = old_program['category']
                new_item['parameters'] = deepcopy(old_program['parameters'])
            else:
                standard_program = dict_programs.get(short_name)
                if standard_program:
                    new_item['category'] = standard_program['category']
                    new_parameters = [{'value': parameter}
                                      for parameter in standard_program['parameters']]
                    for parameter in new_parameters:
                        if parameter['value']['pops'] == ['']:
                            parameter['value']['pops'] = list(D_pops_names)
                    if new_parameters:
                        new_item['parameters'] = deepcopy(new_parameters)

            progs.append(new_item)

    project_entry.populations = pops
    project_entry.programs = progs
    years = model['data']['epiyears']
    # this is the new truth
    model['G']['inputprograms'] = progs
    model['G']['inputpopulations'] = pops
    project_entry.model = model
    project_entry.datastart = int(years[0])
    project_entry.dataend = int(years[-1])


class ProjectItem(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @marshal_with(ProjectDb.resource_fields)
    @login_required
    def get(self, project_id):
        """
        Opens the project with the given ID.
        If the project exists, notifies the user about success.
        expects project ID,
        todo: only if it can be found
        """
        proj_exists = project_exists(project_id)
        if not proj_exists:
            raise ProjectNotFound(id=project_id)
        else:
            return project_exists

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Update a Project'
    )
    @login_required
    def put(self, project_id):
        """
        Updates the project with the given id.
        This happens after users edit the project.

        """
        # TODO replace this with app.config
        DATADIR = current_app.config['UPLOAD_FOLDER']

        current_app.logger.debug(
            "updateProject %s for user %s" % (project_id, current_user.email))
        raw_data = json.loads(request.data)

        current_app.logger.debug(
            "project %s is in edit mode" % project_id)
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
            raise ProjectNotFound(id=project_id)

        project_name = project_entry.name

        makeproject_args = {"projectname": project_name, "savetofile": False}
        # editing datastart & dataend currently is not allowed
        makeproject_args['datastart'] = project_entry.datastart
        makeproject_args['dataend'] = project_entry.dataend
        makeproject_args['progs'] = data.get(
            'programs', project_entry.programs)
        makeproject_args['pops'] = data.get(
            'populations', project_entry.populations)
        current_app.logger.debug(
            "createProject(%s)" % makeproject_args)

        current_app.logger.debug(
            "Editing project %s by user %s:%s" % (
                project_name, current_user.id, current_user.email))
        project_entry.programs = makeproject_args['progs']
        project_entry.populations = makeproject_args['pops']
        current_app.logger.debug(
            'Updating existing project %s' % project_entry.name)

        # makeproject is supposed to return the name of the existing file...
        # D = makeproject(**makeproject_args)
        # D should have inputprograms and inputpopulations corresponding to the
        # entered data now
        # project_entry.model = tojson(D)
        WorkingProjectDb.query.filter_by(id=project_entry.id).delete()
        if can_update and project_entry.project_data is not None and project_entry.project_data.meta is not None:
            # try to reload the data
            loaddir = upload_dir_user(DATADIR)
            if not loaddir:
                loaddir = DATADIR
            filename = project_name + '.xlsx'
            server_filename = os.path.join(loaddir, filename)
            filedata = open(server_filename, 'wb')
            filedata.write(project_entry.project_data.meta)
            filedata.close()
            D = model_as_bunch(project_entry.model)
            # resave relevant metadata
            D['G']['projectname'] = project_entry.name
            D['G']['projectfilename'] = projectpath(project_entry.name+'.prj')
            D['G']['workbookname'] = D['G']['projectname'] + '.xlsx'
            D['G']['inputprograms'] = deepcopy(project_entry.programs)
            D['G']['inputpopulations'] = deepcopy(project_entry.populations)
            # TODO fix after v2
            # D = updatedata(
            # D, input_programs = project_entry.programs, savetofile = False)
            # and now, because workbook was uploaded, we have to correct the
            # programs and populations
            model = model_as_dict(D)
            project_entry.model = model
            getPopsAndProgsFromModel(project_entry, trustInputMetadata=False)
        else:
            ProjectDataDb.query.filter_by(
                id=project_entry.id).delete()

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project_entry.name, project_entry.user_id))
        db.session.add(project_entry)
        db.session.commit()
        new_project_template = D['G']['workbookname']

        current_app.logger.debug(
            "new_project_template: %s" % new_project_template)
        (dirname, basename) = (
            upload_dir_user(TEMPLATEDIR), new_project_template)
        response = helpers.send_from_directory(dirname, basename)
        response.headers['X-project-id'] = project_entry.id
        return response

