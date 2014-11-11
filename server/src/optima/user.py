#!/bin/env python
# -*- coding: utf-8 -*-
"""
User Module
~~~~~~~~~~~~~~

1. Get current logged in user.
2. Login a user using username and password.
3. Logout.

"""
from flask import Flask, render_template, request, jsonify, g, session, flash, \
     redirect, url_for, abort, Blueprint
from flask.ext.login import LoginManager, login_user, current_user, logout_user, AnonymousUserMixin

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

from api import app

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# System Imports
import hashlib

# Login Manager
login_manager = LoginManager()

# setup sqlalchemy
engine = create_engine('postgresql+psycopg2://optima:optima@localhost:5432/optima')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=True,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)


class UserDb(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(60))
    email = Column(String(200))
    password = Column(String(200))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
    
    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False
    
    def is_authenticated(self):
        return True


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
            db_session.add( u )
            db_session.commit()
            
            # Login this user
            login_user(u)
            
            # Return user info
            return jsonify({'email': u.email, 'name': u.name })

    # We are here implies username is already taken
    return jsonify({'status': 'This email is already in use'})


@user.route('/login', methods=['POST'])
def login():
      
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

init_db()
