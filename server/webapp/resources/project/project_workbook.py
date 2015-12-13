from flask import Response
from flask import current_app
from flask import helpers
from flask.ext.login import current_user
from flask.ext.login import login_required
from flask_restful import Resource
from server.webapp.dataio import TEMPLATEDIR
from server.webapp.dataio import upload_dir_user
from server.webapp.dbmodels import ProjectDataDb
from server.webapp.exceptions import ProjectNotFound
from server.webapp.utils import load_project
from server.webapp.utils import report_exception


class ProjectWorkbook(Resource):

    @login_required
    @report_exception()
    def get(self, project_id):
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
            raise ProjectNotFound(id=project_id)
        else:
            # See if there is matching project data
            projdata = ProjectDataDb.query.get(project_entry.id)

            if projdata is not None and len(projdata.meta) > 0:
                return Response(
                    projdata.meta,
                    mimetype='application/octet-stream',
                    headers={
                        'Content-Disposition': 'attachment;filename=' + project_entry.name+'.xlsx'})
            else:
                # if no project data found
                D = project_entry.model
                wb_name = D['G']['workbookname']
                # TODO fix after v2
                # makeworkbook(wb_name, project_entry.populations,
                # project_entry.programs, \
                #     project_entry.datastart, project_entry.dataend)
                current_app.logger.debug(
                    "project %s template created: %s" % (project_entry.name, wb_name))
                (dirname, basename) = (upload_dir_user(TEMPLATEDIR), wb_name)
                # deliberately don't save the template as uploaded data
                return helpers.send_from_directory(dirname, basename)
