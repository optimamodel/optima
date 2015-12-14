import os
from datetime import datetime
import dateutil
from copy import deepcopy

from flask import current_app, helpers, request, Response, abort
from werkzeug.exceptions import Unauthorized
from werkzeug.utils import secure_filename

from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger

from optima.makespreadsheet import default_dataend, default_datastart, makespreadsheet
from optima.project import version

from server.webapp.dataio import TEMPLATEDIR, templatepath, upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import (ParsetsDb, ProjectDataDb, ProjectDb,
    ResultsDb, WorkingProjectDb, ProgsetsDb, ProgramsDb)

from server.webapp.inputs import secure_filename_input, SubParser
from server.webapp.exceptions import RecordDoesNotExist, NoFileSubmitted, InvalidFileType, NoProjectNameProvided

from server.webapp.utils import (load_project, verify_admin_request,
    delete_spreadsheet, RequestParser, model_as_bunch, model_as_dict, allowed_file)
from server.webapp.resources.project.utils import getPopsAndProgsFromModel


class ProjectBase(Resource):
    method_decoractors = [login_required]

    def get_query(self):
        return ProjectDb.query

    @marshal_with(ProjectDb.resource_fields, envelope='projects')
    def get(self):
        projects = self.get_query().all()
        return projects


class ProjectDoesNotExist(RecordDoesNotExist):

    _model = 'project'


population_parser = RequestParser()
population_parser.add_arguments({
    'short_name': {'required': True, 'location': 'json'},
    'name':       {'required': True, 'location': 'json'},
    'female':     {'type': bool, 'required': True, 'location': 'json'},
    'male':       {'type': bool, 'required': True, 'location': 'json'},
    'age_from':   {'location': 'json'},
    'age_to':     {'location': 'json'},
})


project_parser = RequestParser()
project_parser.add_arguments({
    'name': {'required': True, 'type': secure_filename_input},
    'datastart': {'type': int, 'default': default_datastart},
    'dataend': {'type': int, 'default': default_dataend},
    # FIXME: programs should be a "SubParser" with its own Parser
    # 'populations': {'type': (population_parser), 'required': True},
    'populations': {'type': dict, 'required': True, 'action': 'append'},
})


# editing datastart & dataend currently is not allowed
project_update_parser = RequestParser()
project_update_parser.add_arguments({
    'name': {'required': True, 'type': secure_filename_input},
    # FIXME: programs should be a "SubParser" with its own Parser
    #'populations': {'type': SubParser(population_parser)},
    'populations': {'type': dict, 'action': 'append'},
    'canUpdate': {'type': bool, 'default': False},
    # FIXME: programs should be a "SubParser" with its own Parser
    'programs': {'type': dict, 'action': 'append'}
})


class ProjectAll(ProjectBase):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='List All Projects',
        note='Requires admin priviledges'
    )
    @verify_admin_request
    def get(self):
        return super(ProjectAll, self).get()


class Project(ProjectBase):

    def get_query(self):
        return super(Project, self).get_query().filter_by(user_id=current_user.id)

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary="List all project for current user"
    )
    def get(self):
        return super(Project, self).get()

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Create a new Project with the given name and provided parameters.',
        notes="""Creates the project with the given name and provided parameters.
            Result: on the backend, new project is stored,
            spreadsheet with specified name and parameters given back to the user.""",
        parameters=project_parser.swagger_parameters()
    )
    @login_required
    def post(self):
        current_app.logger.info(
            "create request: {} {}".format(request, request.data))

        args = project_parser.parse_args()
        user_id = current_user.id

        current_app.logger.debug(
            "createProject %s for user %s" % (
                args['name'], current_user.email))
        current_app.logger.debug("createProject data: %s" % args)

        current_app.logger.debug("createProject(%s)" % args)

        # create new project
        current_app.logger.debug("Creating new project %s by user %s:%s" % (
            args['name'], user_id, current_user.email))
        project_entry = ProjectDb(
            user_id=user_id,
            version=version,
            created=datetime.utcnow(),
            **args
        )

        current_app.logger.debug(
            'Creating new project: %s' % project_entry.name)

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project_entry.name, project_entry.user_id))
        db.session.add(project_entry)
        db.session.commit()
        new_project_template = args['name']

        path = templatepath(args['name'])
        makespreadsheet(
            path,
            pops=args['populations'],
            datastart=args['datastart'],
            dataend=args['dataend'])

        current_app.logger.debug(
            "new_project_template: %s" % new_project_template)
        (dirname, basename) = (
            upload_dir_user(TEMPLATEDIR), new_project_template)
        response = helpers.send_from_directory(dirname, basename)
        response.headers['X-project-id'] = project_entry.id
        response.status_code = 201
        return response


class ProjectItem(Resource):
    method_decoractors = [login_required]

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @marshal_with(ProjectDb.resource_fields)
    def get(self, project_id):
        query = ProjectDb.query
        project_entry = query.get(project_id)

        if project_entry is None:
            abort(410)
            # FIXME
            # raise ProjectDoesNotExist()
        if not current_user.is_admin and \
                str(project_entry.user_id) != str(current_user.id):
            raise Unauthorized

        return project_entry

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Update a Project'
    )
    def put(self, project_id):
        """
        Updates the project with the given id.
        This happens after users edit the project.

        """
        # TODO replace this with app.config
        DATADIR = current_app.config['UPLOAD_FOLDER']

        current_app.logger.debug(
            "updateProject %s for user %s" % (
                project_id, current_user.email))

        args = project_parser.parse_args()

        current_app.logger.debug(
            "project %s is in edit mode" % project_id)
        current_app.logger.debug(args)

        can_update = args.pop('canUpdate', False)
        current_app.logger.debug("updateProject data: %s" % args)

        # Check whether we are editing a project
        project_entry = load_project(project_id) if project_id else None
        if not project_entry:
            raise ProjectDoesNotExist(id=project_id)

        for name, value in args.iteritems():
            if value is not None:
                setattr(project_entry, name, value)

        current_app.logger.debug(
            "Editing project %s by user %s:%s" % (
                args['name'], current_user.id, current_user.email))

        # makeproject is supposed to return the name of the existing file...
        # D = makeproject(**makeproject_args)
        # D should have inputprograms and inputpopulations corresponding to the
        # entered data now
        # project_entry.model = tojson(D)
        WorkingProjectDb.query.filter_by(id=project_entry.id).delete()
        if can_update and project_entry.project_data is not None and project_entry.project_data.meta is not None:
            from dataio import projectpath

            # try to reload the data
            loaddir = upload_dir_user(DATADIR)
            if not loaddir:
                loaddir = DATADIR
            filename = args['name'] + '.xlsx'
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

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Deletes the given project (and eventually, corresponding excel files)'
    )
    def delete(self, project_id):
        current_app.logger.debug("deleteProject %s" % project_id)
        # only loads the project if current user is either owner or admin
        project_entry = load_project(project_id)
        user_id = current_user.id

        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        user_id = project_entry.user_id
        project_name = project_entry.name

        project_entry.recursive_delete()

        db.session.commit()
        current_app.logger.debug(
            "project %s is deleted by user %s" % (project_id, current_user.id))
        delete_spreadsheet(project_name)
        if (user_id != current_user.id):
            delete_spreadsheet(project_name, user_id)
        current_app.logger.debug("spreadsheets for %s deleted" % project_name)

        return '', 204


file_resource = {
    'file': fields.String,
    'result': fields.String,
}


class ProjectSpreadsheet(Resource):
    class_decorators = [login_required]

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Generates workbook for the project with the given id.',
        notes="""
        if project exists, regenerates workbook for it
        if project does not exist, returns an error.
        """
    )
    def get(self, project_id):
        cu = current_user
        current_app.logger.debug("giveWorkbook(%s %s)" % (cu.id, project_id))
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project_entry.id)

        wb_name = '{}.xlsx'.format(project_entry.name)

        if projdata is not None and len(projdata.meta) > 0:
            return Response(
                projdata.meta,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + wb_name
                })
        else:
            # if no project data found
            # TODO fix after v2
            # makeworkbook(wb_name, project_entry.populations, project_entry.programs, \
            #     project_entry.datastart, project_entry.dataend)
            current_app.logger.debug(
                "project %s template created: %s" % (project_entry.name, wb_name)
            )
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
            # deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename)

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Upload the project workbook',
        parameters=[
            {
                'name': 'file',
                'dataType': 'file',
                'required': True,
                'description': 'Excel file',
                'paramType': 'form',
            }
        ]
    )
    @marshal_with(file_resource)
    def post(self, project_id):

        # TODO replace this with app.config
        DATADIR = current_app.config['UPLOAD_FOLDER']

        current_app.logger.debug("api/project/update")

        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        project_name = project_entry.name
        user_id = current_user.id
        current_app.logger.debug("uploadExcel(project id: %s user:%s)" % (project_id, user_id))

        uploaded_file = request.files['file']

        # getting current user path
        loaddir = upload_dir_user(DATADIR)
        if not loaddir:
            loaddir = DATADIR
        if not uploaded_file:
            raise NoFileSubmitted()

        source_filename = secure_filename(uploaded_file.filename)
        if not allowed_file(source_filename):
            raise InvalidFileType(source_filename)

        filename = project_name + '.xlsx'
        server_filename = os.path.join(loaddir, filename)
        uploaded_file.save(server_filename)

        # See if there is matching project
        current_app.logger.debug("project for user %s name %s: %s" % (current_user.id, project_name, project_entry))
        if project_entry is not None:
            from optima.utils import saves  # , loads
            # from optima.parameters import Parameterset
            new_project = project_entry.hydrate()
            new_project.loadspreadsheet(server_filename)
            new_project.modified = datetime.now(dateutil.tz.tzutc())
            current_app.logger.info("after spreadsheet uploading: %s" % new_project)
            # TODO: figure out whether we still have to do anything like that
            #   D['G']['inputpopulations'] = deepcopy(project_entry.populations)

            # Is this the first time? if so then we have to run simulations
            #   should_re_run = 'S' not in D

            # TODO call new_project.runsim instead
            result = new_project.runsim()
            current_app.logger.info("runsim result for project %s: %s" % (project_id, result))

            # D = updatedata(D, input_programs = project_entry.programs, savetofile=False, rerun=should_re_run)
            #   now, update relevant project_entry fields
            project_entry.settings = saves(new_project.settings)
            project_entry.data = saves(new_project.data)
            project_entry.created = new_project.created
            project_entry.updated = new_project.modified

            # update the programs and populations based on the data TODO: yes or no?
            #   getPopsAndProgsFromModel(project_entry, trustInputMetadata = False)

            db.session.add(project_entry)

            # save data upload timestamp
            data_upload_time = datetime.now(dateutil.tz.tzutc())
            # get file data
            filedata = open(server_filename, 'rb').read()
            # See if there is matching project data
            projdata = ProjectDataDb.query.get(project_entry.id)

            # update parsets
            result_parset_id = None
            parset_records_map = {record.id: record for record in project_entry.parsets}  # may be SQLAlchemy can do stuff like this already?
            for (parset_name, parset_entry) in new_project.parsets.iteritems():
                parset_record = parset_records_map.get(parset_entry.uuid)
                if not parset_record:
                    parset_record = ParsetsDb(
                        project_id=project_entry.id,
                        name=parset_name,
                        id=parset_entry.uuid
                    )
                if parset_record.name == "default":
                    result_parset_id = parset_entry.uuid
                parset_record.pars = saves(parset_entry.pars)
                db.session.add(parset_record)

            # update results (after runsim is invoked)
            results_map = {
                (record.parset_id, record.calculation_type): record
                for record in project_entry.results
            }
            result_record = results_map.get((result_parset_id, "simulation"))
            if not result_record:
                result_record = ResultsDb(
                    parset_id=result_parset_id,
                    project_id=project_entry.id,
                    calculation_type="simulation",
                    blob=saves(result)
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

        reply = {
            'file': source_filename,
            'result': 'Project %s is updated' % project_name
        }
        return reply


class ProjectData(Resource):
    class_decorators = [login_required]

    @swagger.operation(
        produces='application/x-gzip',
        summary='Download data for the project with the given id',
        notes="""
        if project exists, returns data (aka D) for it
        if project does not exist, returns an error.
        """
    )
    def get(self, project_id):
        current_app.logger.debug("/api/project/%s/data" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        new_project = project_entry.hydrate()

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR
        filename = project_entry.name + '.prj'
        server_filename = os.path.join(loaddir, filename)

        from optima.utils import save
        save(server_filename, new_project)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created project',
        parameters=[
            {
                'name': 'file',
                'dataType': 'file',
                'required': True,
                'description': 'Project file',
                'paramType': 'form',
            }
        ]
    )
    @marshal_with(file_resource)
    def post(self, project_id):
        """
        Uploads Data file, uses it to update the project model.
        Precondition: model should exist.
        """
        user_id = current_user.id
        current_app.logger.debug("uploadProject(project id: %s user:%s)" % (project_id, user_id))
        uploaded_file = request.files['file']

        if not uploaded_file:
            raise NoFileSubmitted()

        source_filename = secure_filename(uploaded_file.filename)
        if not allowed_file(source_filename):
            raise InvalidFileType(source_filename)

        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(project_id)

        from optima.utils import load
        new_project = load(uploaded_file)
        project_entry.restore(new_project)
        db.session.add(project_entry)

        db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Project %s is updated' % project_entry.name,
        }
        return reply

class ProjectFromData(Resource):
    class_decorators = [login_required]

    @swagger.operation(
        summary='Creates a project & uploads data to initialize it.',
        parameters=[
            {
                'name': 'file',
                'dataType': 'file',
                'required': True,
                'description': 'Project file',
                'paramType': 'form',
            },
            {
                'name': 'name',
                'dataType': 'string',
                'required': True,
                'description': 'New project name',
                'paramType': 'form'
            }
        ]
    )
    @marshal_with(file_resource)
    def post(self):
        from optima.project import version
        user_id = current_user.id
        project_name = request.values.get('name')
        if not project_name:
            raise NoProjectNameProvided()

        uploaded_file = request.files['file']

        if not uploaded_file:
            raise NoFileSubmitted()

        source_filename = secure_filename(uploaded_file.filename)
        if not allowed_file(source_filename):
            raise InvalidFileType(source_filename)

        from optima.utils import load
        new_project = load(uploaded_file)

        if new_project.data:
            datastart = int(new_project.data['years'][0])
            dataend = int(new_project.data['years'][-1])
            pops = []
            project_pops = new_project.data['pops']
            for i in range(len(project_pops['short'])):
                new_pop = {
                'name': project_pops['long'][i], 'short_name': project_pops['short'][i],
                'female': project_pops['female'][i], 'male':project_pops['male'][i],
                'age_from': int(project_pops['age'][i][0]), 'age_to': int(project_pops['age'][i][1])
                }
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

        reply = {'file': source_filename, 'result': 'Project %s is created' % project_name}
        return reply


program_parser = RequestParser()
program_parser.add_arguments({
    'name': {'required': True, 'location': 'json'},
    'short_name': {'required': True, 'location': 'json'},
    'category': {'required': True, 'location': 'json'},
    'active': {'type': bool, 'default': False},
    'parameters': {'type': dict, 'action': 'append', 'dest': 'pars'},
})


progset_parser = RequestParser()
progset_parser.add_arguments({
    'name': {'required': True},
    'programs': {'required': True, 'type': SubParser(program_parser), 'action': 'append'}
})


class Progset(Resource):
    class_decorators = [login_required]

    @swagger.operation(
        description='Download progsets for the project with the given id.',
        notes="""
            if project exists, returns progsets for it
            if project does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields, envelope='progsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ProgsetsDb).filter_by(project_id=project_entry.id).all()
        return reply

    @swagger.operation(
        description='Create a progset for the project with the given id.',
        parameters=progset_parser.swagger_parameters()
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def post(self, project_id):
        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        args = progset_parser.parse_args()

        progset_entry = ProgsetsDb(project_id, args['name'])
        db.session.add(progset_entry)
        db.session.flush()

        progset_entry.create_programs_from_list(args['programs'])

        db.session.commit()

        return progset_entry, 201


class ProgsetDoesNotExist(RecordDoesNotExist):
    _model = 'progset'


class ProgsetItem(Resource):
    class_decorators = [login_required]

    @swagger.operation(
        description='Download progset with the given id.',
        notes="""
            if progset exists, returns it
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def get(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = db.session.query(ProgsetsDb).get(progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)
        if str(progset_entry.project_id) != project_id:
            raise ProgsetDoesNotExist(id=progset_id)
        return progset_entry

    @swagger.operation(
        description='Update progset with the given id.',
        notes="""
            if progset exists, returns the updated version
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def put(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = db.session.query(ProgsetsDb).get(progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        if str(progset_entry.project_id) != project_id:
            raise ProgsetDoesNotExist(id=progset_id)

        args = progset_parser.parse_args()
        progset_entry.name = args['name']
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()

        progset_entry.create_programs_from_list(args.get('programs', []))

        db.session.commit()

        return progset_entry

    @swagger.operation(
        description='Delete progset with the given id.',
        notes="""
            if progset exists, deletes it
            if progset does not exist, returns an error.
        """
    )
    def delete(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = db.session.query(ProgsetsDb).get(progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        if str(progset_entry.project_id) != project_id:
            raise ProgsetDoesNotExist(id=progset_id)

        progset_entry.name
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()
        db.session.delete(progset_entry)
        db.session.commit()
        return '', 204
