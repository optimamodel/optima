import os
from datetime import datetime
import json

import dateutil
from flask import current_app, helpers, request, Response
from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger
from werkzeug.exceptions import Unauthorized
from werkzeug.utils import secure_filename

import optima as op
from server.webapp.dataio import (
    get_populations_from_project, set_populations_on_project, set_project_summary_on_project,
    get_project_summary_from_project_record,
    load_project_record, load_project, update_or_create_result_record,
    get_project_parameters, load_project_program_summaries, save_project_with_new_uids)
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, ResultsDb, ProjectDataDb, ProjectEconDb
from server.webapp.exceptions import ProjectDoesNotExist
from server.webapp.parse import get_default_populations
from server.webapp.resources.common import (
    file_resource, file_upload_form_parser, report_exception, verify_admin_request)
from server.webapp.utils import (
    secure_filename_input, AllowedSafeFilenameStorage, RequestParser, TEMPLATEDIR,
    templatepath, upload_dir_user)


class ProjectBase(Resource):
    method_decorators = [report_exception, login_required]

    def get_query(self):
        return ProjectDb.query

    def get(self):
        project_records = self.get_query().all()
        return {'projects': map(get_project_summary_from_project_record, project_records)}


population_parser = RequestParser()
population_parser.add_arguments({
    'short': {'required': True, 'location': 'json'},
    'name': {'required': True, 'location': 'json'},
    'female': {'type': bool, 'required': True, 'location': 'json'},
    'male': {'type': bool, 'required': True, 'location': 'json'},
    'injects': {'type': bool, 'required': True, 'location': 'json'},
    'sexworker': {'type': bool, 'required': True, 'location': 'json'},
    'age_from': {'type': int, 'location': 'json'},
    'age_to': {'type': int, 'location': 'json'},
})

project_parser = RequestParser()
project_parser.add_arguments({
    'name': {'required': True, 'type': str},
    'dataStart': {'type': int, 'default': op.default_datastart},
    'dataEnd': {'type': int, 'default': op.default_dataend},
    # FIXME: programs should be a "SubParser" with its own Parser
    # 'populations': {'type': (population_parser), 'required': True},
    'populations': {'type': dict, 'required': True, 'action': 'append'},
})

# editing datastart & dataend currently is not allowed
project_update_parser = RequestParser()
project_update_parser.add_arguments({
    'name': {'type': str},
    'populations': {'type': dict, 'action': 'append'},
    'canUpdate': {'type': bool, 'default': False},
    'dataStart': {'type': int, 'default': None},
    'dataEnd': {'type': int, 'default': None}
})


class ProjectsAll(ProjectBase):
    """
    A collection of all projects.
    """

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='List All Projects',
        note='Requires admin priviledges'
    )
    @report_exception
    @verify_admin_request
    def get(self):
        return super(ProjectsAll, self).get()


bulk_project_parser = RequestParser()
bulk_project_parser.add_arguments({
    'projects': {'required': True, 'action': 'append'},
})


class Projects(ProjectBase):
    """
    /api/project

    - GET: used in open/manage page to get project lists
    """

    def get_query(self):
        return super(Projects, self).get_query().filter_by(user_id=current_user.id)

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary="List all project for current user"
    )
    @report_exception
    def get(self):
        return super(Projects, self).get()

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Create a new Project with the given name and provided parameters.',
        notes="""Creates the project with the given name and provided parameters.
            Result: on the backend, new project is stored,
            spreadsheet with specified name and parameters given back to the user.""",
        parameters=project_parser.swagger_parameters()
    )
    @report_exception
    @login_required
    def post(self):
        current_app.logger.info(
            "create request: {} {}".format(request, request.data, request.headers))

        args = project_parser.parse_args()
        user_id = current_user.id

        current_app.logger.debug("createProject data: %s" % args)

        # create new project
        current_app.logger.debug("Creating new project %s by user %s:%s" % (
            args['name'], user_id, current_user.email))
        project_entry = ProjectDb(
            user_id=user_id
        )

        project = op.Project(
            name = args["name"]
        )
        set_populations_on_project(project, args["populations"])

        current_app.logger.debug(
            'Creating new project: %s' % project.name)

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project.name, project_entry.user_id))

        db.session.add(project_entry)
        db.session.commit()

        project.uid = project_entry.id
        project.data["years"] = (args['dataStart'], args['dataEnd'])

        project_entry.save_obj(project)

        new_project_template = secure_filename("{}.xlsx".format(args['name']))
        path = templatepath(new_project_template)
        op.makespreadsheet(
            path,
            pops=args['populations'],
            datastart=args['dataStart'],
            dataend=args['dataEnd'])

        current_app.logger.debug(
            "new_project_template: %s" % new_project_template)
        (dirname, basename) = (
            upload_dir_user(TEMPLATEDIR), new_project_template)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=new_project_template)
        response.headers['X-project-id'] = project_entry.id
        response.status_code = 201
        return response

    @swagger.operation(
        summary="Bulk delete for project with the provided ids",
        parameters=bulk_project_parser.swagger_parameters()
    )
    @report_exception
    def delete(self):
        project_ids = json.loads(request.data)['projects']
        for project_id in project_ids:
            record = load_project_record(project_id, raise_exception=True)
            record.recursive_delete()
        db.session.commit()
        return '', 204


class Project(Resource):
    """
    /api/project/<uuid:project_id>

    - GET: get active project summary
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @report_exception
    def get(self, project_id):
        project_entry = ProjectDb.query.get(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)
        if not current_user.is_admin and \
                        str(project_entry.user_id) != str(current_user.id):
            raise Unauthorized

        return get_project_summary_from_project_record(project_entry)

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Update a Project'
    )
    @report_exception
    def put(self, project_id):
        """
        Updates the project with the given id.
        This happens after users edit the project.
        """
        current_app.logger.debug(
            "updateProject %s for user %s" % (
                project_id, current_user.email))

        args = project_update_parser.parse_args()

        current_app.logger.debug(
            "project %s is in edit mode" % project_id)
        current_app.logger.debug(args)

        # can_update = args.pop('canUpdate', False) we'll calculate it based on DB
        # info + request info
        current_app.logger.debug("updateProject data: %s" % args)

        # Check whether we are editing a project
        project_entry = load_project_record(project_id) if project_id else None
        if not project_entry:
            raise ProjectDoesNotExist(id=project_id)

        project = project_entry.load()
        set_project_summary_on_project(project, args)

        current_app.logger.debug(
            "Editing project %s by user %s:%s" % (
                project.name, current_user.id, current_user.email))

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project.name, project_entry.user_id))
        db.session.add(project_entry)
        db.session.commit()
        project_entry.save_obj(project)

        secure_project_name = secure_filename(project.name)
        new_project_template = secure_project_name

        path = templatepath(secure_project_name)
        op.makespreadsheet(
            path,
            pops=args['populations'],
            datastart=args["dataStart"],
            dataend=args["dataEnd"])


        current_app.logger.debug(
            "new_project_template: %s" % new_project_template)
        (dirname, basename) = (
            upload_dir_user(TEMPLATEDIR), new_project_template)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=new_project_template)
        response.headers['X-project-id'] = project_entry.id
        return response

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Deletes the given project (and eventually, corresponding excel files)'
    )
    @report_exception
    def delete(self, project_id):
        current_app.logger.debug("deleteProject %s" % project_id)
        # only loads the project if current user is either owner or admin
        project_entry = load_project_record(project_id)

        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        project_entry.recursive_delete()

        db.session.commit()
        current_app.logger.debug(
            "project %s is deleted by user %s" % (project_id, current_user.id))

        return '', 204


class ProjectSpreadsheet(Resource):
    """
    Spreadsheet upload and download for the given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Generates workbook for the project with the given id.',
        notes="""
        if project exists, regenerates workbook for it
        if project does not exist, returns an error.
        """
    )
    @report_exception
    def get(self, project_id):
        cu = current_user
        current_app.logger.debug("get ProjectSpreadsheet(%s %s)" % (cu.id, project_id))
        project_entry = load_project_record(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        project = project_entry.load()

        # See if there is matching project data
        projdata = ProjectDataDb.query.get(project_id)

        wb_name = secure_filename('{}.xlsx'.format(project.name))
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
            # makeworkbook(wb_name, project.populations, project.programs, \
            #     project.datastart, project.dataend)
            path = templatepath(wb_name)
            op.makespreadsheet(
                path,
                pops=get_populations_from_project(project),
                datastart=project.data["years"][0],
                dataend=project.data["years"][-1])

            current_app.logger.debug(
                "project %s template created: %s" % (
                    project.name, wb_name)
            )
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
            # deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload the project workbook')
    @marshal_with(file_resource)
    def post(self, project_id):

        print ">>>> Load spreadsheet"

        project_record = load_project_record(project_id, raise_exception=True)
        project = project_record.load()

        project_name = project.name

        args = file_upload_form_parser.parse_args()

        # getting current user path
        # TODO replace this with app.config
        uploaded_file = args['file']
        data_dir = current_app.config['UPLOAD_FOLDER']
        load_dir = upload_dir_user(data_dir)
        if not load_dir:
            load_dir = data_dir
        source_filename = uploaded_file.source_filename
        filename = secure_filename(project_name + '.xlsx')
        server_filename = os.path.join(load_dir, filename)
        uploaded_file.save(server_filename)

        parset_name = "default"
        parset_names = project.parsets.keys()
        if parset_name in parset_names:
            parset_name = "uploaded from " + uploaded_file.source_filename
            i = 0
            while parset_name in parset_names:
                i += 1
                parset_name = "uploaded_from_%s (%d)" % (uploaded_file.source_filename, i)

        # Load parset from spreadsheet, will also runsim and store result
        project.loadspreadsheet(server_filename, parset_name, makedefaults=True)

        # Add progset defaults... and move them to inactive
        programs = op.defaults.defaultprograms(project)

        progset = project.progsets[parset_name]
        progset.inactive_programs = op.odict({x.name:x for x in programs})
        progset.programs = op.odict()

        with open(server_filename, 'rb') as f:
            # Save the spreadsheet if they want to download it again

            try:
                data_record = ProjectDataDb.query.get(project_id)
                data_record.meta = f.read()
            except:
                data_record = ProjectDataDb(project_id, f.read())

        db.session.add(data_record)
        db.session.add(project_record)

        result = project.results[-1]
        result_record = update_or_create_result_record(project, result, parset_name, "calibration")
        print ">>>> Store result(calibration) '%s'" % (result.name)
        db.session.add(result_record)

        db.session.commit()
        project_record.save_obj(project)

        reply = {
            'file': source_filename,
            'result': 'Project %s is updated' % project_name
        }
        return reply


class ProjectEcon(Resource):
    """
    Economic data export and import for the existing project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Generates economic data spreadsheet for the project with the given id.',
        notes="""
        if project exists, regenerates economic data spreadsheet for it
        or returns spreadsheet with existing data,
        if project does not exist, returns an error.
        """
    )
    def get(self, project_id):
        cu = current_user
        current_app.logger.debug("get ProjectEcon(%s %s)" % (cu.id, project_id))

        project = load_project(project_id)

        # See if there is matching project econ data
        projecon = ProjectEconDb.query.get(project.id)

        wb_name = secure_filename('{}_economics.xlsx'.format(project.name))
        if projecon is not None and len(projecon.meta) > 0:
            return Response(
                projecon.meta,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + wb_name
                })
        else:
            # if no project econdata found
            path = templatepath(wb_name)
            op.makeeconspreadsheet(
                path,
                datastart=project.datastart,
                dataend=project.dataend)

            current_app.logger.debug(
                "project %s economics spreadsheet created: %s" % (
                    project.name, wb_name)
            )
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
            # deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(
        summary='Upload the project economics data spreadsheet',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(file_resource)
    def post(self, project_id):

        DATADIR = current_app.config['UPLOAD_FOLDER']

        current_app.logger.debug(
            "POST /api/project/%s/economics" % project_id)

        project_record = load_project_record(project_id, raise_exception=True)
        project = project_record.load()

        project_name = project.name

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        # getting current user path
        loaddir = upload_dir_user(DATADIR)
        if not loaddir:
            loaddir = DATADIR

        source_filename = uploaded_file.source_filename

        filename = secure_filename(project_name + '_economics.xlsx')
        server_filename = os.path.join(loaddir, filename)
        uploaded_file.save(server_filename)

        # See if there is matching project
        current_app.logger.debug("project for user %s name %s: %s" % (
            current_user.id, project_name, project))

        project.loadeconomics(server_filename)
        project.modified = datetime.now(dateutil.tz.tzutc())
        current_app.logger.info(
            "after economics uploading: %s" % project)

        #   now, update relevant project fields
        # this adds to db.session all dependent entries
        project_record.save_obj(project)
        db.session.add(project_record)

        # save data upload timestamp
        data_upload_time = datetime.now(dateutil.tz.tzutc())
        # get file data
        filedata = open(server_filename, 'rb').read()
        # See if there is matching project econ data
        projecon = ProjectEconDb.query.get(project.id)

        # update existing
        if projecon is not None:
            projecon.meta = filedata
            projecon.updated = data_upload_time
        else:
            # create new project data
            projecon = ProjectEconDb(
                project_id=project.id,
                meta=filedata,
                updated=data_upload_time)

        # Save to db
        db.session.add(projecon)
        db.session.commit()

        reply = {
            'file': source_filename,
            'success': 'Project %s is updated with economics data' % project_name
        }
        return reply

    @swagger.operation(
        summary='Removes economics data from project'
    )
    def delete(self, project_id):
        cu = current_user
        current_app.logger.debug("user %s:POST /api/project/%s/economics" % (cu.id, project_id))
        project_record = load_project_record(project_id)
        project = project_record.load()
        if project is None:
            raise ProjectDoesNotExist(id=project_id)

        # See if there is matching project econ data
        projecon = ProjectEconDb.query.get(project.id)

        if projecon is not None and len(projecon.meta) > 0:
            project = project.load()
            if 'econ' not in project.data:
                current_app.logger.warning("No economics data has been found in project {}".format(project_id))
            else:
                del project.data['econ']
            project_record.restore(project)
            db.session.add(project_record)
            db.session.delete(projecon)
            db.session.commit()

            reply = {
                'success': 'Project %s economics data has been removed' % project_id
            }
            return reply, 204
        else:
            raise Exception("No economics data has been uploaded")


class ProjectData(Resource):
    """
    Export and import of the existing project in / from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/x-gzip',
        summary='Download data for the project with the given id',
        notes="""
        if project exists, returns data (aka D) for it
        if project does not exist, returns an error.
        """
    )
    @report_exception
    def get(self, project_id):
        current_app.logger.debug("/api/project/%s/data" % project_id)
        project_record = load_project_record(project_id, raise_exception=True)

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = project_record.as_file(loaddir)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created project',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(file_resource)
    def post(self, project_id):
        """
        Uploads Data file, uses it to update the project model.
        Precondition: model should exist.
        """
        user_id = current_user.id
        current_app.logger.debug(
            "uploadProject(project id: %s user:%s)" % (project_id, user_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

        project_record = load_project_record(project_id)
        if project_record is None:
            raise ProjectDoesNotExist(project_id)

        old_project = project_record.load()

        # Migrate it, so that older projects can be uploaded okay
        project = op.migrateproject(op.loadobj(uploaded_file))

        # Make sure they have the same name and uid...
        project.name = old_project.name
        project.uid = old_project.uid

        # Delete dependent objects, as the uids might be different and such
        project_record.delete_dependent_objects()

        if project.data:
            assert (project.parsets)
            result = project.runsim()
            current_app.logger.info(
                "runsim result for project %s: %s" % (project_id, result))

        project_record.save_obj(project)
        db.session.add(project_record)
        db.session.flush()

        if project.data:
            assert (project.parsets)
            result_record = update_or_create_result_record(project, result)
            db.session.add(result_record)

        db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Project %s is updated' % project.name,
        }
        return reply


project_upload_form_parser = RequestParser()
project_upload_form_parser.add_arguments({
    'file': {'type': AllowedSafeFilenameStorage, 'location': 'files', 'required': True},
    'name': {'required': True, 'help': 'Project name'},
})


class ProjectFromData(Resource):
    """
    /api/project/data
    - POST: upload a .PRJ file which is a project in python-pickled format    Import of a new project from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @report_exception
    def post(self):
        args = project_upload_form_parser.parse_args()
        uploaded_file = args['file']
        project_name = args['name']

        print "> Upload project '%s'" % args['name']
        project = op.loadobj(uploaded_file)

        # Migrate it, so that older projects can be uploaded okay
        project = op.migrateproject(project)

        project.name = project_name
        save_project_with_new_uids(project, current_user.id)
        print "> Upload end"

        response = {
            'file': uploaded_file.source_filename,
            'name': project_name,
            'id': str(project.uid)
        }
        return response, 201


project_copy_fields = {
    'project': fields.String,
    'user': fields.String,
    'copy_id': fields.String
}
project_copy_parser = RequestParser()
project_copy_parser.add_arguments({
    'to': {'required': True, 'type': secure_filename_input},
})


class ProjectCopy(Resource):
    @swagger.operation(
        summary='Copies the given project to a different name',
        parameters=project_copy_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(project_copy_fields)
    @login_required
    def post(self, project_id):
        args = project_copy_parser.parse_args()
        new_project_name = args['to']

        # Get project row for current user with project name
        project_record = load_project_record(
            project_id, all_data=True, raise_exception=True)
        project_user_id = project_record.user_id

        # force load the existing result
        project_result_exists = project_record.results

        project = project_record.load()

        new_project_record = ProjectDb(user_id=project_user_id)
        db.session.add(new_project_record)
        db.session.commit()

        # Make the loaded project have a new project ID plus the new chosen name
        project.uid = new_project_record.id
        project.name = new_project_name

        new_project_record.save_obj(project)

        project_record.name = new_project_name
        db.session.add(new_project_record)
        # change the creation and update time
        new_project_record.created = datetime.now(dateutil.tz.tzutc())
        new_project_record.updated = datetime.now(dateutil.tz.tzutc())
        db.session.flush()  # this updates the project ID to the new value

        if project_result_exists:
            # copy each result
            for result_record in project_record.results:
                if result_record.calculation_type != ResultsDb.DEFAULT_CALCULATION_TYPE:
                    continue
                result = op.loads(result_record.blob)
                parset_name = result.parset.name
                new_parset = [r for r in project.parsets.values() if r.name == parset_name]
                if not new_parset:
                    raise Exception(
                        "Could not find copied parset for result in copied project {}".format(project_id))
                result_record.parset_id = new_parset[0].uid
                db.session.expunge(result_record)
                # ???
                #make_transient(result_record)
                # set the id to None to ensure no duplicate ID
                result_record.id = None
                db.session.add(result_record)
        db.session.commit()
        # let's not copy working project, it should be either saved or
        # discarded
        payload = {
            'project': project_id,
            'user': project_user_id,
            'copy_id': new_project_record.id
        }
        return payload


class Portfolio(Resource):
    """
    POST /api/project/portfolio

    Accessed in project-api-services.js, used in open-ctrl.js to download
    selected projects in one big ZIP package. Requires the name
    of the projects that have to be collated.
    """

    @swagger.operation(
        produces='application/x-zip',
        summary='Download data for projects with the given ids as a zip file',
        parameters=bulk_project_parser.swagger_parameters()
    )
    @report_exception
    @login_required
    def post(self):
        from zipfile import ZipFile
        from uuid import uuid4

        for arg in bulk_project_parser.args:
            print('{} location: {}'.format(arg.name, arg.location))

        current_app.logger.debug("Download Portfolio (/api/project/portfolio)")
        args = bulk_project_parser.parse_args()
        current_app.logger.debug(
            "Portfolio requested for projects {}".format(args['projects']))

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        projects = [
            load_project_record(id, raise_exception=True).as_file(loaddir)
            for id in args['projects']
            ]

        zipfile_name = '{}.zip'.format(uuid4())
        zipfile_server_name = os.path.join(loaddir, zipfile_name)
        with ZipFile(zipfile_server_name, 'w') as portfolio:
            for project in projects:
                portfolio.write(
                    os.path.join(loaddir, project), 'portfolio/{}'.format(project))

        return helpers.send_from_directory(loaddir, zipfile_name)


class DefaultPrograms(Resource):
    """
    GET /api/project/<uuid:project_id>/defaults

    Packaged in api-service but used in program-set-ctrl to get the default set
    of programs when creating a new program set.
    """

    @swagger.operation(summary="Returns default programs, their categories and parameters")
    @report_exception
    @login_required
    def get(self, project_id):
        return {"programs": load_project_program_summaries(project_id)}


class DefaultParameters(Resource):
    """
    GET /api/project/<project_id>/parameters

    Returns all available parameters with their properties. Used by
    program-set in the program modal.
    """

    @swagger.operation(summary="List default parameters")
    @report_exception
    @login_required
    def get(self, project_id):
        project = load_project(project_id)

        return {'parameters': get_project_parameters(project)}


class DefaultPopulations(Resource):
    """
    GET /api/project/populations

    Report populations in projects in the project management page
    """

    @swagger.operation(summary='Returns default populations')
    @report_exception
    @login_required
    def get(self):
        return {'populations': get_default_populations()}
