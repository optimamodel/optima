import json
import os
from datetime import datetime
import dateutil

from flask import current_app, helpers, request, Response
from flask.ext.login import current_user, login_required
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger
from werkzeug.utils import secure_filename

import optima as op
from optima.utils import loaddbobj

from server.webapp.dataio import (
    get_populations_from_project, load_project_summary, update_project_with_spreadsheet_download,
    load_project_record, load_project, update_or_create_result_record,
    load_project_parameters, load_project_program_summaries, save_project_as_new, load_project_summaries,
    create_project_with_spreadsheet_download, delete_projects)
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, ResultsDb, ProjectDataDb, ProjectEconDb
from server.webapp.exceptions import ProjectDoesNotExist
from server.webapp.parse import get_default_populations
from server.webapp.resources.common import (
    file_resource, file_upload_form_parser, report_exception, verify_admin_request)
from server.webapp.utils import (
    secure_filename_input, RequestParser, TEMPLATEDIR,
    templatepath, upload_dir_user, normalize_obj)


def get_post_json():
    return normalize_obj(request.get_json())


class ProjectsAll(Resource):
    method_decorators = [report_exception, verify_admin_request]

    @swagger.operation(summary="List all projects (for admins)")
    def get(self):
        """
        GET /api/project/all - returns list of all project_summaries
        """
        return {'projects': load_project_summaries()}


class Projects(Resource):
    """
    /api/project
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="List all project for current user")
    def get(self):
        """
        GET /api/project - return list of projects for a user
        """
        return {'projects': load_project_summaries(current_user.id)}

    @swagger.operation(summary="Create new project")
    def post(self):
        """
        POST /api/project - creates a new project
        Post-json: project_summary
        """
        summary = normalize_obj(request.get_json())
        project_id, dirname, basename = create_project_with_spreadsheet_download(
            current_user.id, summary)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.status_code = 201
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary="Bulk delete for project with the provided ids")
    def delete(self):
        """
        DELETE /api/project - deletes a bunch of projects
        Post-body:
            projects: list of project_ids to delete
        """
        delete_projects(json.loads(request.data)['projects'])
        return '', 204


class Project(Resource):
    """
    /api/project/<uuid:project_id>
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Open a Project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id> - returns a project summary
        """
        return load_project_summary(project_id)

    @swagger.operation(summary='Update a Project')
    def put(self, project_id):
        """
        PUT /api/project/<uuid:project_id> - updates a project
        Post-arg: project_summary
        """
        project_summary = normalize_obj(request.get_json())
        dirname, basename = update_project_with_spreadsheet_download(
            project_id, project_summary)
        print("> Project template: %s" % basename)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary='Deletes project')
    def delete(self, project_id):
        """
        DELETE /api/project/<uuid:project_id> - deletes a single project
        """
        delete_projects([project_id])
        return '', 204


class ProjectSpreadsheet(Resource):
    """
    /api/project/<uuid:project_id>/spreadsheet
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Generates workbook for the project with the given id.')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/spreadsheet
        Downloads template spreadsheet or pre-uploaded spreadsheet
        """
        cu = current_user
        current_app.logger.debug("get ProjectSpreadsheet(%s %s)" % (cu.id, project_id))

        project_entry = load_project_record(project_id)
        project = project_entry.load()
        xls_filename = secure_filename('{}.xlsx'.format(project.name))

        project_data_record = ProjectDataDb.query.get(project_id)
        if project_data_record is not None and len(project_data_record.meta) > 0:
            data_in_xls = project_data_record.meta
            return Response(
                data_in_xls,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + xls_filename
                })
        else:
            path = templatepath(xls_filename)
            op.makespreadsheet(
                path,
                pops=get_populations_from_project(project),
                datastart=project.data["years"][0],
                dataend=project.data["years"][-1])

            current_app.logger.debug(
                "project %s template created: %s" % (
                    project.name, xls_filename)
            )
            (dirname, basename) = (upload_dir_user(TEMPLATEDIR), xls_filename)
            # deliberately don't save the template as uploaded data
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload the project workbook')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/spreadsheet
        Loads filled-out spreadsheet as data
        """

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


class ProjectData(Resource):
    """
    /api/project/<uuid:project_id>/data
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Download .prj file for project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/data
        Downloads .prj file for the project
        """
        current_app.logger.debug("/api/project/%s/data" % project_id)
        project_record = load_project_record(project_id, raise_exception=True)
        dirname = upload_dir_user(TEMPLATEDIR)
        if not dirname:
            dirname = TEMPLATEDIR
        filename = project_record.as_file(dirname)
        return helpers.send_from_directory(dirname, filename)

    @swagger.operation(summary='Update existing project with .prj')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/data
        Replaces project with an uploaded .prj file
        """
        file = request.files['file']
        filename = secure_filename(file.filename)
        full_filename = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)
        file.save(full_filename)

        project = loaddbobj(full_filename)

        project_record = load_project_record(project_id)
        project_record.save_obj(project)
        db.session.add(project_record)
        db.session.commit()

        reply = {
            'file': filename,
            'result': 'Project %s is updated' % project.name,
        }
        return reply


class ProjectFromData(Resource):
    method_decorators = [report_exception, login_required]

    def post(self):
        """
        POST /api/project/data - upload new .prj file
        form-url: name: name of project
        file: upload file
        """
        project_name = request.form.get('name')
        file = request.files['file']

        print "> Upload project '%s'" % project_name
        filename = secure_filename(file.filename)
        full_filename = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)
        file.save(full_filename)

        project = loaddbobj(full_filename)
        project.name = project_name

        save_project_as_new(project, current_user.id)

        project_id = project.uid

        response = {
            'file': filename,
            'name': project_name,
            'id': project_id
        }
        return response, 201


class ProjectCopy(Resource):
    method_decorators = [report_exception, login_required]
    @swagger.operation(summary='Copies the given project to a different name')
    def post(self, project_id):
        """
        POST '/api/project/<uuid:project_id>/copy'
        Post-json:
            to: new project name
        """
        args = normalize_obj(request.get_json())

        new_project_name = args['to']

        # Get project row for current user with project name
        project_record = load_project_record(
            project_id, raise_exception=True)
        user_id = project_record.user_id

        project = project_record.load()
        project.name = new_project_name
        save_project_as_new(project, user_id)

        copy_project_id = project.uid

        result_records = project_record.results
        if result_records:
            # copy each result
            for result_record in result_records:
                result = op.loads(result_record.blob)
                result_record.project_id = copy_project_id

                # reset the parset_id in results to new project
                parset_name = result.parset.name
                new_parset = [r for r in project.parsets.values() if r.name == parset_name]
                if not new_parset:
                    raise Exception(
                        "Could not find copied parset for result in copied project {}".format(project_id))
                copy_parset_id = new_parset[0].uid
                result_record.parset_id = copy_parset_id

                # resets result_record into a new record
                db.session.expunge(result_record)
                result_record.id = None
                db.session.add(result_record)

        db.session.commit()

        payload = {
            'project': project_id,
            'user': user_id,
            'copy_id': project.uid
        }
        return payload


class Portfolio(Resource):
    """
    POST /api/project/portfolio

    Accessed in project-api-services.js, used in open-ctrl.js to download
    selected projects in one big ZIP package. Requires the name
    of the projects that have to be collated.
    """

    @swagger.operation(summary='Download data for projects with the given ids as a zip file')
    @report_exception
    @login_required
    def post(self):
        from zipfile import ZipFile
        from uuid import uuid4
        args = normalize_obj(request.get_json())
        print("> Portfolio requested for projects {}".format(args['projects']))

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        projects = [
            load_project_record(id, raise_exception=True).as_file(loaddir)
            for id in args['projects']]

        zipfile_name = '{}.zip'.format(uuid4())
        zipfile_server_name = os.path.join(loaddir, zipfile_name)
        with ZipFile(zipfile_server_name, 'w') as portfolio:
            for project in projects:
                portfolio.write(
                    os.path.join(loaddir, project), 'portfolio/{}'.format(project))

        return helpers.send_from_directory(loaddir, zipfile_name)


class DefaultPrograms(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="Returns default programs, their categories and parameters")
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/defaults
        Returns default programs for program-set modal
        """
        return {"programs": load_project_program_summaries(project_id)}


class DefaultParameters(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary="List default parameters")
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parameters
        Returns available parameters for program modal
        """
        return {'parameters': load_project_parameters(project_id)}


class DefaultPopulations(Resource):
    method_decorators = [report_exception, login_required]

    @swagger.operation(summary='Returns default populations')
    def get(self):
        """
        GET /api/project/populations
        Returns default populations for project management
        """
        return {'populations': get_default_populations()}




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