#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from optima.dbmodels import ProjectDb

class ProjectTestCase(OptimaTestCase):
    """
    Test class for the project blueprint covering all /api/project endpoints.

    """

    def setUp(self):
        super(ProjectTestCase, self).setUp()
        response = self.create_user()
        response = self.login()

    def test_create_project(self):
        response = self.client.post('/api/project/create/test', data = '{}')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_project_info_fails(self):
        headers = [('project', 'test')]
        response = self.client.get('/api/project/info', headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data), { "status": "NOK" })

if __name__ == '__main__':
    unittest.main()
