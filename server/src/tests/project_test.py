#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json

class ProjectTestCase(OptimaTestCase):
    """
    Test class for the project blueprint covering all /api/project endpoints.

    """


    def setUp(self):
        super(ProjectTestCase, self).setUp()
        response = self.create_user()
        response = self.login()

    def tearDown(self):
        self.logout()

    def test_create_project(self):
        response = self.client.post('/api/project/create/test', data = '{}', follow_redirects=True)
        assert(response.status_code==200)

if __name__ == '__main__':
    unittest.main()
