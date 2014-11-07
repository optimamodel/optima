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
from flask.ext.openid import OpenID
from openid.extensions import pape

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

from api import app, db
from models import UserDb
oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])


@user.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = UserDb.query.filter_by(openid=session['openid']).first()


@user.after_request
def after_request(response):
    return response

@user.route('/login', methods=['GET'])
@oid.loginhandler
def login():
      
    # Does the login via OpenID.  Has to call into `oid.try_login`
    # to start the OpenID machinery.
    # If we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(oid.get_next_url())
    
    # If we are trying to login
    if request.method == 'GET':
        
        open_id = request.values.get('openid');
        
        if open_id is None:
            abort(401)
        
        if open_id:
            pape_req = pape.Request([])
            return oid.try_login(open_id, ask_for=['email', 'nickname'],
                                         ask_for_optional=['fullname'],
                                         extensions=[pape_req])
                                         
    abort(401)

@user.route('/current', methods=['GET'])
def current_user():
    g.user = None
    if 'openid' in session:
        g.user = UserDb.query.filter_by(openid=session['openid']).first()
        return jsonify({ 'email': g.user.email, 'name': g.user.name })  

    abort(401)

@oid.after_login
def create_or_login(resp):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    session['openid'] = resp.identity_url
    if 'pape' in resp.extensions:
        pape_resp = resp.extensions['pape']
        session['auth_time'] = pape_resp.auth_time
    user = UserDb.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())

    name = resp.fullname or resp.nickname
    email = resp.email

    if not name:
        flash(u'Error: you have to provide a name')
    elif '@' not in email:
        flash(u'Error: you have to enter a valid email address')
    else:
        flash(u'Profile successfully created')
        db.session.add(UserDb(name, email, session['openid']))
        db.session.commit()
         
        return redirect(oid.get_next_url())

@user.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return jsonify({'status': 'OK'})
