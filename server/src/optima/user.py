#!/bin/env python
# -*- coding: utf-8 -*-
"""
User Module
~~~~~~~~~~~~~~

1. Get current logged in user.
2. Login a user using username and password.
3. Logout.

"""
from flask import request, jsonify, g, session, flash, abort, Blueprint
from flask.ext.login import LoginManager, login_user, current_user, logout_user
from dbconn import db
from dbmodels import UserDb

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

# System Imports
import hashlib

# Login Manager
login_manager = LoginManager()

@user.record
def record_params(setup_state):
    app = setup_state.app
    login_manager.init_app(app)

@user.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = UserDb.query.filter_by(id=session['user_id']).first()

@user.route('/create', methods=['POST'])
def create_user():
    print("create request: %s %s" % (request, request.data))
    print("/user/create %s" % request.get_json(force=True))
    # Check if the user already exists
    email = request.json['email']
    name = request.json['name']
    password = hashlib.sha224( request.json['password'] ).hexdigest()

    if email is not None and name is not None and password is not None:
        # Get user for this username (if exists)
        try:
            no_of_users = UserDb.query.filter_by( email=email ).count()
        except:
            no_of_users = 0

        if no_of_users == 0:

            # Save to db
            u = UserDb(name, email, password)
            db.session.add( u )
            db.session.commit()

            # Login this user
            login_user(u)

            # Return user info
            return jsonify({'email': u.email, 'name': u.name })

    # We are here implies username is already taken
    return jsonify({'status': 'This email is already in use'})

@user.route('/login', methods=['POST'])
def login():
    print("/user/login %s" % request.get_json(force=True))
    # Make sure user is not logged in already.
    cu = current_user

    if cu.is_anonymous():

        # Make sure user is valid.
        username = request.json['email']

        if username is not None:

            # Get hashsed password
            password = hashlib.sha224( request.json['password'] ).hexdigest()

            # Get user for this username
            try:
                u = UserDb.query.filter_by( email=username ).first()
            except:
                u = None

            # Make sure user is valid and password matches
            if u is not None and u.password == password:

                # Login the user
                login_user(u)

                # Return user info
                return jsonify({'email': u.email, 'name': u.name })

        # If we come here, login is not successful    
        abort(401)

    # User already loggedin
    return jsonify({'email': cu.email, 'name': cu.name })

@user.route('/current', methods=['GET'])
def current_user_api():
    cu = current_user
    if not cu.is_anonymous():
        return jsonify({ 'email': cu.email, 'name': cu.name })

    abort(401)

@user.route('/logout')
def logout():
    session.clear()
    logout_user()
    flash(u'You have been signed out')
    return jsonify({'status': 'OK'})

#For Login Manager
@login_manager.user_loader
def load_user(userid):
    try:
        u = UserDb.query.filter_by(id=userid).first()
    except:
        u = None
    return u

@login_manager.unauthorized_handler
def unauthorized_handler():
    abort(401)
