#!/bin/env python
# -*- coding: utf-8 -*-
"""
User Module
~~~~~~~~~~~~~~

1. Get current logged in user.
2. Login a user using openid.
3. Logout.

"""
from flask import Flask, request, jsonify, g, session, flash, \
     redirect, url_for, abort, Blueprint
from flask.ext.login import LoginManager, login_user, current_user, logout_user, AnonymousUserMixin
from openid.extensions import pape

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')


from api import app, db
from models import UserDb

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
    if 'userid' in session:
        g.user = UserDb.query.filter_by(id=session['userid']).first()

@user.route('/create', methods=['POST'])
def create_user():
    
    # Check if the user already exists
    email = request.values.get('email')
    name = request.values.get('name')
    password = hashlib.sha224( request.values.get('password') ).hexdigest()
    
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
    return jsonify({'status': 'Username in use'})

@user.route('/login', methods=['POST'])
def login():
      
    # Make sure user is not logged in already.
    cu = current_user
    
    if cu.is_anonymous():
        
        # Make sure user is valid.
        username = request.values.get('username')
        
        if username is not None:
        
            # Get hashsed password
            password = hashlib.sha224( request.values.get('password') ).hexdigest()
            
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
    if cu.is_anonymous() == False:
        return jsonify({ 'email': cu.email, 'name': cu.name })  

    abort(401)

@user.route('/logout')
def logout():
    logout_user()
    flash(u'You have been signed out')
    return jsonify({'status': 'OK'})

#For Login Manager
@login_manager.user_loader
def load_user(userid):
    u = None;    
    try:
        u = UserDb.query.filter_by(id=userid).first()
    except:
        u = None;
        
    return u
    
@login_manager.unauthorized_handler
def unauthorized_handler():
    abort(401)
