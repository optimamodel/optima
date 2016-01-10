import os
from datetime import datetime
import dateutil

from flask import current_app, helpers, request, Response, abort
from werkzeug.exceptions import Unauthorized

from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger

import optima as op

from server.webapp.dataio import TEMPLATEDIR, templatepath, upload_dir_user
from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ProjectDataDb, ProjectDb, ResultsDb

from server.webapp.inputs import secure_filename_input, AllowedSafeFilenameStorage
from server.webapp.exceptions import ProjectDoesNotExist
from server.webapp.fields import Uuid, Json

from server.webapp.utils import (load_project, verify_admin_request, report_exception,
                                 delete_spreadsheet, RequestParser)


class ProjectBase(Resource):
    method_decorators = [report_exception, login_required]

    def get_query(self):
        return ProjectDb.query

    @marshal_with(ProjectDb.resource_fields, envelope='projects')
    def get(self):
        projects = self.get_query().all()
        for p in projects:
            p.has_data_now = p.has_data()
        return projects


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
    'datastart': {'type': int, 'default': op.default_datastart},
    'dataend': {'type': int, 'default': op.default_dataend},
    # FIXME: programs should be a "SubParser" with its own Parser
    # 'populations': {'type': (population_parser), 'required': True},
    'populations': {'type': dict, 'required': True, 'action': 'append'},
})


# editing datastart & dataend currently is not allowed
project_update_parser = RequestParser()
project_update_parser.add_arguments({
    'name': {'type': secure_filename_input},
    'populations': {'type': dict, 'action': 'append'},
    'canUpdate': {'type': bool, 'default': False},
    'datastart': {'type': int, 'default': None},
    'dataend': {'type': int, 'default': None}
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
    @verify_admin_request
    def get(self):
        return super(ProjectsAll, self).get()


bulk_project_parser = RequestParser()
bulk_project_parser.add_arguments({
    'projects': {'required': True, 'action': 'append'},
})


class Projects(ProjectBase):
    """
    A collection of projects for the given user.
    """

    def get_query(self):
        return super(Projects, self).get_query().filter_by(user_id=current_user.id)

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary="List all project for current user"
    )
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
            user_id=user_id,
            version=op.version,
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
        new_project_template = "{}.xlsx".format(args['name'])

        path = templatepath(new_project_template)
        op.makespreadsheet(
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

    @swagger.operation(
        summary="Bulk delete for project with the provided ids",
        parameters=bulk_project_parser.swagger_parameters()
    )
    def delete(self):
        # dirty hack in case the wsgi layer didn't put json data where it belongs
        from flask import request
        import json

        class FakeRequest:
            def __init__(self, data):
                self.json = json.loads(data)

        try:
            req = FakeRequest(request.data)
        except ValueError:
            req = request
        # end of dirty hack

        args = bulk_project_parser.parse_args(req=req)

        projects = [
            load_project(id, raise_exception=True)
            for id in args['projects']
        ]

        for project in projects:
            project.recursive_delete()

        db.session.commit()

        return '', 204


class Project(Resource):
    """
    An individual project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Open a Project'
    )
    @marshal_with(ProjectDb.resource_fields)
    def get(self, project_id):
        query = ProjectDb.query
        project_entry = query.get(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)
        if not current_user.is_admin and \
                str(project_entry.user_id) != str(current_user.id):
            raise Unauthorized
        project_entry.has_data_now = project_entry.has_data()  # no other way to make it work for methods and not attributes?
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

        args = project_update_parser.parse_args()

        current_app.logger.debug(
            "project %s is in edit mode" % project_id)
        current_app.logger.debug(args)

#        can_update = args.pop('canUpdate', False) we'll calculate it based on DB info + request info
        current_app.logger.debug("updateProject data: %s" % args)

        # Check whether we are editing a project
        project_entry = load_project(project_id) if project_id else None
        if not project_entry:
            raise ProjectDoesNotExist(id=project_id)

        current_populations = project_entry.populations
        new_populations = args.get('populations', {})
        can_update = (current_populations == new_populations)
        current_app.logger.debug("can_update %s: %s" % (project_id, can_update))

        for name, value in args.iteritems():
            if value is not None:
                setattr(project_entry, name, value)

        current_app.logger.debug(
            "Editing project %s by user %s:%s" % (
                project_entry.name, current_user.id, current_user.email))

        # because programs no longer apply here, we don't seem to have to recalculate the results
        # not sure what to do with startdate and enddate though... let's see how it goes )

        if not can_update:
            db.session.query(ProjectDataDb).filter_by(id=project_entry.id).delete()
            db.session.commit()

        # Save to db
        current_app.logger.debug("About to persist project %s for user %s" % (
            project_entry.name, project_entry.user_id))
        db.session.add(project_entry)
        db.session.commit()

        new_project_template = project_entry.name

        path = templatepath(project_entry.name)
        op.makespreadsheet(
            path,
            pops=args['populations'],
            datastart=project_entry.datastart,
            dataend=project_entry.dataend)

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
file_upload_form_parser = RequestParser()
file_upload_form_parser.add_argument('file', type=AllowedSafeFilenameStorage, location='files', required=True)


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
            path = templatepath(wb_name)
            op.makespreadsheet(
                path,
                pops=project_entry.populations,
                datastart=project_entry.datastart,
                dataend=project_entry.dataend)

            current_app.logger.debug(
                "project %s template created: %s" % (project_entry.name, wb_name)
            )
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
            # deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename)

    @swagger.operation(
        produces='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        summary='Upload the project workbook',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @marshal_with(file_resource)
    def post(self, project_id):

        # TODO replace this with app.config
        DATADIR = current_app.config['UPLOAD_FOLDER']
        CALIBRATION_TYPE = 'calibration'

        current_app.logger.debug("PUT /api/project/%s/spreadsheet" % project_id)

        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        project_name = project_entry.name
        user_id = current_user.id
        current_app.logger.debug("uploadExcel(project id: %s user:%s)" % (project_id, user_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        # getting current user path
        loaddir = upload_dir_user(DATADIR)
        if not loaddir:
            loaddir = DATADIR

        source_filename = uploaded_file.source_filename

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
            parset_records_map = {record.id: record for record in project_entry.parsets}
            # may be SQLAlchemy can do stuff like this already?
            for (parset_name, parset_entry) in new_project.parsets.iteritems():
                parset_record = parset_records_map.get(parset_entry.uid)
                if not parset_record:
                    parset_record = ParsetsDb(
                        project_id=project_entry.id,
                        name=parset_name,
                        id=parset_entry.uid
                    )
                if parset_record.name == "default":
                    result_parset_id = parset_entry.uid
                parset_record.pars = saves(parset_entry.pars)
                db.session.add(parset_record)

            # update results (after runsim is invoked)
            result_record = [item for item in project_entry.results if
                             item.parset_id == result_parset_id and
                             item.calculation_type == ResultsDb.CALIBRATION_TYPE]
            if result_record:
                result_record = result_record[0]
                result_record.blob = saves(result)
            if not result_record:
                result_record = ResultsDb(
                    parset_id=result_parset_id,
                    project_id=project_entry.id,
                    calculation_type=ResultsDb.CALIBRATION_TYPE,
                    blob=saves(result)
                )
            db.session.add(result_record)

            # update existing
            if projdata is not None:
                projdata.meta = filedata
                projdata.upload_time = data_upload_time
            else:
                # create new project data
                projdata = ProjectDataDb(
                    project_id=project_entry.id,
                    meta=filedata,
                    updated=data_upload_time)

            # Save to db
            db.session.add(projdata)
            db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Project %s is updated' % project_name
        }
        return reply


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
    def get(self, project_id):
        current_app.logger.debug("/api/project/%s/data" % project_id)
        project_entry = load_project(project_id, raise_exception=True)

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = project_entry.as_file(loaddir)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created project',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @marshal_with(file_resource)
    def post(self, project_id):
        """
        Uploads Data file, uses it to update the project model.
        Precondition: model should exist.
        """
        user_id = current_user.id
        current_app.logger.debug("uploadProject(project id: %s user:%s)" % (project_id, user_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

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


project_upload_form_parser = RequestParser()
project_upload_form_parser.add_arguments({
    'file': {'type': AllowedSafeFilenameStorage, 'location': 'files', 'required': True},
    'name': {'required': True, 'help': 'Project name'},
})


project_upload_resource = file_resource.copy()
project_upload_resource['id'] = Uuid


class ProjectFromData(Resource):
    """
    Import of a new project from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        summary='Creates a project & uploads data to initialize it.',
        parameters=project_upload_form_parser.swagger_parameters()
    )
    @marshal_with(project_upload_resource)
    def post(self):
        from optima.project import version
        user_id = current_user.id

        args = project_upload_form_parser.parse_args()
        uploaded_file = args['file']
        project_name = args['name']

        source_filename = uploaded_file.source_filename

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
                    'female': project_pops['female'][i], 'male': project_pops['male'][i],
                    'age_from': int(project_pops['age'][i][0]), 'age_to': int(project_pops['age'][i][1])
                }
                pops.append(new_pop)
        else:
            from optima.makespreadsheet import default_datastart, default_dataend
            datastart = default_datastart
            dataend = default_dataend
            pops = {}

        project_entry = ProjectDb(
            project_name, user_id, datastart,
            dataend,
            pops,
            version=version)

        # New project ID needs to be generated before calling restore
        db.session.add(project_entry)
        db.session.flush()

        project_entry.restore(new_project)
        project_entry.name = project_name
        db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Project %s is created' % project_name,
            'id': str(project_entry.id)
        }
        return reply


project_copy_fields = {
    'project': Uuid,
    'user': Uuid,
    'copy_id': Uuid
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
    @marshal_with(project_copy_fields)
    @login_required
    @report_exception
    def post(self, project_id):
        from sqlalchemy.orm.session import make_transient
        # from server.webapp.dataio import projectpath
        args = project_copy_parser.parse_args()
        new_project_name = args['to']

        # Get project row for current user with project name
        project_entry = load_project(project_id, all_data=True, raise_exception=True)
        project_user_id = project_entry.user_id

        be_project = project_entry.hydrate()

        # force load the existing result
        project_result_exists = project_entry.results

        db.session.expunge(project_entry)
        make_transient(project_entry)

        project_entry.id = None
        db.session.add(project_entry)
        db.session.flush()  # this updates the project ID to the new value

        project_entry.restore(be_project)
        project_entry.name = new_project_name

        # change the creation and update time
        project_entry.created = datetime.now(dateutil.tz.tzutc())
        project_entry.updated = datetime.now(dateutil.tz.tzutc())
        # Question, why not use datetime.utcnow() instead
        # of dateutil.tz.tzutc()?
        # it's the same, without the need to import more
        new_project_id = project_entry.id

        if project_result_exists:
            # copy each result
            for result in project_entry.results:
                db.session.expunge(result)
                make_transient(result)
                # set the id to None to ensure no duplicate ID
                result.id = None
                db.session.add(result)
        db.session.commit()
        # let's not copy working project, it should be either saved or
        # discarded
        payload = {
            'project': project_id,
            'user': project_user_id,
            'copy_id': new_project_id
        }
        return payload


class Portfolio(Resource):

    @swagger.operation(
        produces='application/x-zip',
        summary='Download data for projects with the given ids as a zip file',
        parameters=bulk_project_parser.swagger_parameters()
    )
    @login_required
    @report_exception
    def post(self):
        from zipfile import ZipFile
        from uuid import uuid4

        for arg in bulk_project_parser.args:
            print('{} location: {}'.format(arg.name, arg.location))

        current_app.logger.debug("Download Portfolio (/api/project/portfolio)")
        args = bulk_project_parser.parse_args()
        current_app.logger.debug("Portfolio requested for projects {}".format(args['projects']))

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        projects = [
            load_project(id, raise_exception=True).as_file(loaddir)
            for id in args['projects']
        ]

        zipfile_name = '{}.zip'.format(uuid4())
        zipfile_server_name = os.path.join(loaddir, zipfile_name)
        with ZipFile(zipfile_server_name, 'w') as portfolio:
            for project in projects:
                portfolio.write(os.path.join(loaddir, project), 'portfolio/{}'.format(project))

        return helpers.send_from_directory(loaddir, zipfile_name)

defaults_fields = {
    "categories": Json,
    "programs": Json
}

class Defaults(Resource):
    @swagger.operation(
        summary="""Gives default programs, program categories and program parameters
                for the given program"""
    )
    @marshal_with(defaults_fields)
    @login_required
    def get(self, project_id):
        from server.webapp.programs import get_default_programs, program_categories

        project = load_project(project_id, raise_exception=True)
        programs = get_default_programs(project)
        program_categories = program_categories(project)
        for p in programs:
            p['active'] = False
        payload = {
            "programs": programs,
            "categories": program_categories
        }
        return payload
