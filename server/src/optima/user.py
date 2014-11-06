#!/bin/env python
# -*- coding: utf-8 -*-
"""
    OpenID Example
    ~~~~~~~~~~~~~~

    This simple application shows how to integrate OpenID in your application.

    This example requires SQLAlchemy as a dependency.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from flask import Flask, render_template, request, jsonify, g, session, flash, \
     redirect, url_for, abort, Blueprint
from flask.ext.openid import OpenID
from openid.extensions import pape

# route prefix: /api/user
user = Blueprint('user',  __name__, static_folder = '../static')

from api import app

oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging  
# setup sqlalchemy

engine = create_engine(app.config['DATABASE_URI'])

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=True,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(60))
    email = Column(String(200))
    openid = Column(String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid


@user.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        logging.warning('before_request')
        g.user = User.query.filter_by(openid=session['openid']).first()


@user.after_request
def after_request(response):
    #db_session.remove()
    return response


@user.route('/loginform')
def login_form():
    return render_template('index.html')


@user.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    # Does the login via OpenID.  Has to call into `oid.try_login`
    # to start the OpenID machinery.
    # If we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(oid.get_next_url())
    
    # If we are trying to login
    if request.method == 'POST':
        
        openid = request.form.get('openid')
        print(openid);
        if openid:
            pape_req = pape.Request([])
            return oid.try_login(openid, ask_for=['email', 'nickname'],
                                         ask_for_optional=['fullname'],
                                         extensions=[pape_req])
                                         
    return jsonify({ 'status': 'Login',
                      'next': oid.get_next_url(),
                      'error': oid.fetch_error() 
                  })

@user.route('/current', methods=['GET'])
def current_user():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()
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
    user = User.query.filter_by(openid=resp.identity_url).first()
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
        db_session.add(User(name, email, session['openid']))
        db_session.commit()
        return redirect(oid.get_next_url())
    """
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))
    """


@user.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """If this is the user's first login, the create_or_login function
    will redirect here so that the user can set up his profile.
    """
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('login_form'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


@user.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db_session.delete(g.user)
            db_session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('login_form'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db_session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)


@user.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())

init_db()
"""if __name__ == '__main__':
    init_db()
    app.run()"""

