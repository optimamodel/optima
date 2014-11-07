#!/bin/env python
# -*- coding: utf-8 -*-
"""
User Module
~~~~~~~~~~~~~~

1. Get current logged in user.
2. Login a user using openid.
3. Logout.

"""
from flask import Flask, render_template, request, jsonify, g, session, flash, \
     redirect, url_for, abort, Blueprint
from flask.ext.openid import OpenID
from openid.extensions import pape

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

from api import app

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# System Imports
import hashlib

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
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
            db_session.add( u )
            db_session.commit()
            
            # Login this user
            session['userid'] = u.id
            
            # Remember the user
            g.user = u
            
            # Return user info
            return jsonify({'email': g.user.email, 'name': g.user.name })
            
    
    # We are here implies username is already taken
    return jsonify({'status': 'Username in use'})


@user.route('/login', methods=['POST'])
def login():
      
    # Make sure user is not logged in already.
    if g.user is None:
        
        # Make sure user is valid.
        username = request.values.get('username')
        
        if username is not None:
        
            # Get hashsed password
            password = hashlib.sha224( request.values.get('password') ).hexdigest()
            
            # Get user for this username
            u = UserDb.query.filter_by( email=username ).first()
            
            # Make sure user is valid and password matches
            if u is not None and u.password == password:
                
                # Login the user
                session['userid'] = u.id
                
                # Remember the user
                g.user = u
                
                # Return user info
                return jsonify({'email': g.user.email, 'name': g.user.name })
                
        
        # If we come here, login is not successful    
        abort(401)
                                         
    # User already loggedin
    return jsonify({'email': g.user.email, 'name': g.user.name })

@user.route('/current', methods=['GET'])
def current_user():
    g.user = None
    if 'userid' in session:
        g.user = UserDb.query.filter_by(id=session['userid']).first()
        return jsonify({ 'email': g.user.email, 'name': g.user.name })  

    abort(401)

@user.route('/logout')
def logout():
    session.pop('userid', None)
    flash(u'You have been signed out')
    return jsonify({'status': 'OK'})

init_db()
