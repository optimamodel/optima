import traceback

from flask import request, current_app, abort, session, flash, redirect, url_for

from flask_restful import Resource, fields, marshal_with, reqparse
from flask.ext.login import login_user, current_user, logout_user, login_required

from server.webapp.dbconn import db
from server.webapp.dbmodels import UserDb

from server.webapp.fields import Uuid
from server.webapp.inputs import email, hashed_password
from server.webapp.exceptions import UserAlreadyExists, RecordDoesNotExist
from server.webapp.utils import verify_admin_request


user_fields = {
    'id': Uuid,
    'name': fields.String,
    'email': fields.String,
    'is_admin': fields.Boolean,
}


user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=email, required=True)
user_parser.add_argument('name', required=True)
user_parser.add_argument('password', type=hashed_password, required=True)


user_update_parser = reqparse.RequestParser()
user_update_parser.add_argument('email', type=email)
user_update_parser.add_argument('name')
user_update_parser.add_argument('password', type=hashed_password)


class User(Resource):

    @marshal_with(user_fields, envelope='users')
    def get(self):
        current_app.logger.debug('/api/user/list {}'.format(request.args))
        return UserDb.query.all()

    @marshal_with(user_fields)
    def post(self):
        current_app.logger.info("create request: {} {}".format(request, request.data))
        args = user_parser.parse_args()

        same_user_count = UserDb.query.filter_by(email=args.email).count()

        if same_user_count > 0:
            raise UserAlreadyExists('This email is already in use')

        user = UserDb(args.name, args.email, args.password)
        db.session.add(user)
        db.session.commit()

        return user, 201


class UserDetail(Resource):
    method_decorators = [verify_admin_request]

    def delete(self, user_id):
        current_app.logger.debug('/api/user/delete/{}'.format(user_id))
        user = UserDb.query.get(user_id)

        if user is None:
            raise RecordDoesNotExist(user_id)

        user_email = user.email
        from server.webapp.dbmodels import ProjectDb, WorkingProjectDb, ProjectDataDb, WorkLogDb
        from sqlalchemy.orm import load_only

        # delete all corresponding projects and working projects as well
        # project and related records delete should be on a method on the project model
        projects = ProjectDb.query.filter_by(user_id=user_id).options(load_only("id")).all()
        project_ids = [project.id for project in projects]
        current_app.logger.debug("project_ids for user %s:%s" % (user_id, project_ids))
        WorkLogDb.query.filter(WorkLogDb.id.in_(project_ids)).delete(synchronize_session=False)
        ProjectDataDb.query.filter(ProjectDataDb.id.in_(project_ids)).delete(synchronize_session=False)
        WorkingProjectDb.query.filter(WorkingProjectDb.id.in_(project_ids)).delete(synchronize_session=False)
        ProjectDb.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()

        current_app.logger.info("deleted user:{} {}".format(user_id, user_email))

        return '', 204

    @marshal_with(user_fields)
    def put(self, user_id):
        current_app.logger.debug('/api/user/{}'.format(user_id))

        user = UserDb.query.get(user_id)
        if user is None:
            raise RecordDoesNotExist(user_id)

        args = user_update_parser.parse_args()
        for key, value in args.iteritems():
            if value is not None:
                setattr(user, key, value)

        db.session.commit()

        current_app.logger.info("modified user: {}".format(user_id))

        return user


# Authentication


user_login_parser = reqparse.RequestParser()
user_login_parser.add_argument('email', type=email, required=True)
user_login_parser.add_argument('password', type=hashed_password, required=True)


class CurrentUser(Resource):
    method_decorators = [login_required, ]

    @marshal_with(user_fields)
    def get(self):
        return current_user


class UserLogin(Resource):

    @marshal_with(user_fields)
    def post(self):
        current_app.logger.debug("/user/login {}".format(request.get_json(force=True)))

        if current_user.is_anonymous():
            current_app.logger.debug("current user anonymous, proceed with logging in")

            args = user_login_parser.parse_args()
            try:
                # Get user for this username
                user = UserDb.query.filter_by(email=args['email']).first()

                # Make sure user is valid and password matches
                if user is not None and user.password == args['password']:
                    login_user(user)
                    return user

            except Exception:
                var = traceback.format_exc()
                print("Exception when logging user {}: \n{}".format(args['email'], var))

            abort(401)

        else:
            return current_user


class UserLogout(Resource):
    method_decorators = [login_required, ]

    def get(self):
        current_app.logger.debug("logging out user {}".format(
            current_user.name
        ))
        logout_user()
        session.clear()
        flash(u'You have been signed out')

        return redirect(url_for("site"))
