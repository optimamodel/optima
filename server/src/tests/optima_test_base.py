#!/bin/env python
# -*- coding: utf-8 -*-
from api import app

class OptimaTestCase(object):
    """
    Baseclass for Optima API endpoint tests.

    This baseclass provides a setup that can be inherited & combined with
    unittest.TestCase to run API tests.

    Example:

        class SomeTestCase(OptimaTestCase, unittest.TestCase):

            def setUp(self):
                super(SomeTestCase, self).setUp()

            def tearDown(self):
                super(SomeTestCase, self).tearDown()

            def test_a_response(self):
                response = self.test_client.get('/api/path')
                self.assertEqual(response.status_code, 200)

    """

    def setUp(self):
        app.config['TESTING'] = True
        app.config['LOGIN_DISABLED'] = True
        app.login_manager.init_app(app)
        self.test_client = app.test_client()

    def tearDown(self):
        pass
