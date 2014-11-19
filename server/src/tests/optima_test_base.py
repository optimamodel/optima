#!/bin/env python
# -*- coding: utf-8 -*-
from api import app
import unittest

class OptimaTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['LOGIN_DISABLED'] = True
        app.login_manager.init_app(app)
        self.test_client = app.test_client()

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
