#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json

class ProjectTestCase(OptimaTestCase):

    def setUp(self):
        super(ProjectTestCase, self).setUp()

    def tearDown(self):
        super(ProjectTestCase, self).tearDown()

    def test_create_project(self):
        data = {}
        json_data = json.dumps(data)
        response = self.test_client.post('/api/project/create/test', data = json_data, follow_redirects=True)
        assert(response.status_code==200)

if __name__ == '__main__':
    unittest.main()
