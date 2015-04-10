#!/bin/env python
# -*- coding: utf-8 -*-
"""
User Module
~~~~~~~~~~~~~~

1. Get current logged in user.
2. Login a user using username and password.
3. Logout.

"""
from flask import request, jsonify, g, session, flash, abort, Blueprint, url_for, current_app
from flask.ext.login import LoginManager, login_user, current_user, logout_user, redirect, login_required # pylint: disable=E0611,F0401
from optima.dbconn import db
from optima.dbmodels import UserDb
from optima.utils import verify_admin_request
import logging
import json
import traceback


# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

# Login Manager
login_manager = LoginManager()

@user.record
def record_params(setup_state):
    app = setup_state.app
    login_manager.init_app(app)

@user.before_request
def before_request():
    db.engine.dispose()
    g.user = None
    if 'user_id' in session:
        g.user = UserDb.query.filter_by(id=session['user_id']).first()

@user.route('/create', methods=['POST'])
def create_user():
    current_app.logger.info("create request: %s %s" % (request, request.data))
    data = request.get_json(force=True)
    current_app.logger.debug("/user/create %s" % data)
    # Check if the user already exists
    email = data.get('email')
    name = data.get('name')
#   password is now hashed on the client side using sha224
    password = data.get('password')

    if email is not None and name is not None and password is not None:
        # Get user for this username (if exists)
        no_of_users = UserDb.query.filter_by( email=email ).count()

        if no_of_users>0:
            return jsonify({'reason':'This email is already in use'}), 409 #409 - Conflict
        else:
            # Save to db
            u = UserDb(name, email, password)
            db.session.add( u )
            db.session.commit()

            # Login this user
            login_user(u)

            # Return user info
            return jsonify({'email': u.email, 'name': u.name })
    else:
        return jsonify({'reason':'Not all parameters are set'}), 400 #400 - Bad Request

@user.route('/login', methods=['POST'])
def login():
    current_app.logger.debug("/user/login %s" % request.get_json(force=True))
    # Make sure user is not logged in already.
    cu = current_user

    if cu.is_anonymous():
        current_app.logger.debug("current user anonymous, proceed with logging in")
        # Make sure user is valid.
        username = request.json['email']

        if username is not None:
            try:
                # Get hashsed password
                password = request.json['password']

                # Get user for this username
                u = UserDb.query.filter_by( email=username ).first()

                # Make sure user is valid and password matches
                if u is not None and u.password == password:
                    # Login the user
                    login_user(u)
                    # Return user info
                    return jsonify({'email': u.email, 'name': u.name })

            except Exception, err:
                var = traceback.format_exc()
                print("Exception when logging user %s: \n%s" % (username, var))

        # If we came here, login did not succeed
        abort(401)
    else:
        # User logged in, redirect
        current_app.logger.warning("User already logged in:%s %s" % (cu.name, cu.password))
        return redirect(request.args.get("next") or url_for("site"))

@user.route('/current', methods=['GET'])
def current_user_api():
    cu = current_user
    if not cu.is_anonymous():
        return jsonify({ 'email': cu.email, 'name': cu.name, 'is_admin': cu.is_admin })
    else:
        return jsonify({ 'reason': 'User is not logged in' }), 401

@user.route('/logout')
@login_required
def logout():
    cu = current_user
    username = cu.name
    current_app.logger.debug("logging out user %s" % username)
    logout_user()
    session.clear()
    flash(u'You have been signed out')
    current_app.logger.debug("User %s is signed out" % username)
    return redirect(url_for("site"))


#lists all the users. For internal reasons, this is implemented as console-only functionality
#with user hashed password as secret (can be changed later)
@user.route('/list')
@verify_admin_request
def list_users():
    current_app.logger.debug('/api/user/list %s' % request.args)
    result = []
    users = UserDb.query.all()
    for u in users:
        result.append({'id':u.id, 'name':u.name, 'email':u.email})
    return jsonify({'users':result})

#deletes the given user by ID
@user.route('/delete/<user_id>', methods=['DELETE'])
@verify_admin_request
def delete(user_id):
    current_app.logger.debug('/api/user/delete/%s' % user_id)
    user = UserDb.query.get(user_id)
    if not user:
        return jsonify({'reason': 'User does not exist'}), 404
    else:
        user_email = user.email
        from dbmodels import ProjectDb, WorkingProjectDb, ProjectDataDb, WorkLogDb
        from sqlalchemy.orm import load_only
        #delete all corresponding projects and working projects as well
        projects = ProjectDb.query.filter_by(user_id=user_id).options(load_only("id")).all()
        project_ids = [project.id for project in projects]
        current_app.logger.debug("project_ids for user %s:%s" % (user_id, project_ids))
        WorkLogDb.query.filter(WorkLogDb.id.in_(project_ids)).delete(synchronize_session=False)
        ProjectDataDb.query.filter(ProjectDataDb.id.in_(project_ids)).delete(synchronize_session=False)
        WorkingProjectDb.query.filter(WorkingProjectDb.id.in_(project_ids)).delete(synchronize_session=False)
        ProjectDb.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        current_app.logger.info("deleted user:%s %s" % (user_id, user_email))
        return jsonify({'deleted':user_id})

#modify user by ID (can change email, name and/or password)
@user.route('/modify/<user_id>', methods=['PUT'])
@verify_admin_request
def modify(user_id):
    current_app.logger.debug('/api/user/modify/%s' % user_id)
    user = UserDb.query.get(user_id)
    if not user:
        return jsonify({'reason': 'User does not exist'}), 404
    else:
        new_email = request.args.get('email')
        if new_email is not None:
            user.email = new_email
        new_name = request.args.get('name')
        if new_name is not None:
            user.name = new_name
        new_password = request.args.get('password')
        #might change if we decide to hash PW twice
        if new_password is not None:
            user.password = new_password
        db.session.add(user)
        db.session.commit()
        current_app.logger.info("modified user:%s" % user_id)
        return jsonify({'modified':user_id})

#For Login Manager
@login_manager.user_loader
def load_user(userid):
    try:
        u = UserDb.query.filter_by(id=userid).first()
    except:
        u = None
    return u

@login_manager.request_loader
def load_user_from_request(request):

    # try to login using the secret url arg
    secret = request.args.get('secret')
    if secret:
        user = UserDb.query.filter_by(password = secret, is_admin=True).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None

@login_manager.unauthorized_handler
def unauthorized_handler():
    abort(401)
