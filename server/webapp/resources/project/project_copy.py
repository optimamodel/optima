from datetime import datetime
import dateutil
from flask import request, abort
from flask.ext.login import login_required
from flask_restful import Resource
from flask_restful import marshal_with
from flask_restful_swagger import swagger
from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb
from server.webapp.utils import load_project
from server.webapp.resources.project.project import ProjectDoesNotExist
from server.webapp.resources.project.fields import project_copy_fields


class ProjectCopy(Resource):

    @swagger.operation(
        responseClass=ProjectDb.__name__,
        summary='Copy a Project'
    )
    @marshal_with(project_copy_fields)
    @login_required
    def post(self, project_id):
        """
        Copies the given project to a different name
        usage: /api/project/copy/<project_id>?to=<new_project_name>
        """
        from sqlalchemy.orm.session import make_transient
        # from server.webapp.dataio import projectpath
        new_project_name = request.args.get('to')
        if not new_project_name:
            abort(400)
        # Get project row for current user with project name
        project_entry = load_project(project_id, all_data=True)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)
        project_user_id = project_entry.user_id

        # force load the existing data, parset and result
        project_data_exists = project_entry.project_data
        project_parset_exists = project_entry.parsets
        project_result_exists = project_entry.results

        db.session.expunge(project_entry)
        make_transient(project_entry)

        project_entry.id = None
        project_entry.name = new_project_name

        # change the creation and update time
        project_entry.created = datetime.now(dateutil.tz.tzutc())
        project_entry.updated = datetime.now(dateutil.tz.tzutc())
        # Question, why not use datetime.utcnow() instead
        # of dateutil.tz.tzutc()?
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
        # let's not copy working project, it should be either saved or
        # discarded
        payload = {
            'project': project_id,
            'user': project_user_id,
            'copy_id': new_project_id
        }
        return payload
