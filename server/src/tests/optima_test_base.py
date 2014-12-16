#!/bin/env python
# -*- coding: utf-8 -*-
from api import app, init_db
from api import db
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

    def create_user(self):
        headers = {'Content-Type' : 'application/json'}
        create_data = '{"email":"test@test.com","password":"%s","name":"test"}' % self.test_password
        print ("create_user data: %s" % create_data)
        response = self.client.post('/api/user/create', data = create_data)
        return response

    def login(self):
        headers = {'Content-Type' : 'application/json'}
        login_data = '{"email":"test@test.com","password":"%s"}' % self.test_password
        self.client.post('/api/user/login', data=login_data, follow_redirects=True)

    def logout(self):
        self.client.get('/api/user/logout', follow_redirects=True)

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://test:test@localhost:5432/optima_test'
        app.config['TESTING'] = True
        print "app created %s" % app
        init_db()
        print "db created"
        self.client = app.test_client()
        self.test_password = hashlib.sha224("test").hexdigest() 

    def tearDown(self):
        self.logout()
        db.session.remove()
        db.drop_all()
        db.get_engine(app).dispose()
        print "db dropped"
