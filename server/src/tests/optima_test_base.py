#!/bin/env python
# -*- coding: utf-8 -*-
from api import app, init_db
from optima.dbconn import db
from optima.dbmodels import ProjectDb
import unittest
import hashlib

class OptimaTestCase(unittest.TestCase):
    """
    Baseclass for Optima API endpoint tests.

    This baseclass provides a setup that can be inherited to run API tests.

    Example:

        class SomeTestCase(OptimaTestCase):

            def setUp(self):
                super(SomeTestCase, self).setUp()

            def tearDown(self):
                super(SomeTestCase, self).tearDown()

            def test_a_response(self):
                response = self.test_client.get('/api/path')
                self.assertEqual(response.status_code, 200)


    """

    default_name = 'test'
    default_email = 'test@test.com'


    def create_user(self, name = default_name, email = default_email):
        headers = {'Content-Type' : 'application/json'}
        create_data = '{"email":"%s","password":"%s","name":"%s"}' % (email, self.test_password, name)
        print ("create_user data: %s" % create_data)
        response = self.client.post('/api/user/create', data = create_data)
        return response

    def create_project(self, name):
        """ Helper method to create project and save it to the database """
        project = ProjectDb(name, 1, '2000', '2010', '2020', {}, {})
        db.session.add(project)
        db.session.commit()

    def list_projects(self, user_id):
        """ Helper method to list projects for the given user id"""
        projects = ProjectDb.query.filter_by(user_id=user_id).all()
        return [project for project in projects]

    def login(self, email=default_email):
        headers = {'Content-Type' : 'application/json'}
        login_data = '{"email":"%s","password":"%s"}' % (email, self.test_password)
        self.client.post('/api/user/login', data=login_data, follow_redirects=True)

    def logout(self):
        self.client.get('/api/user/logout', follow_redirects=True)

    def setUp(self):
        self.test_password = hashlib.sha224("test").hexdigest()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://test:test@localhost:5432/optima_test'
        app.config['TESTING'] = True
        print "app created %s" % app
        init_db()
        print "db created"
        self.client = app.test_client()

    def tearDown(self):
        self.logout()
        db.session.remove()
        db.drop_all()
        db.get_engine(app).dispose()
        print "db dropped"
