#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from api import app

class AnalysisTestCase(OptimaTestCase):
    """
    Test class for the analysis blueprint covering all /api/analysis endpoints.

    """

    def test_optimization_start_response_without_a_project(self):
        response = self.client.post('/api/analysis/optimization/start', follow_redirects=True)
        expected_data = { "reason": "No project is open"}
        print "response data: %s" % response.data
        self.assertEqual(response.status_code, 401)

    def test_list_scenarios(self):
        from sim.scenarios import defaultscenarios
        from sim.dataio import tojson
        response = self.create_user()
        response = self.login()
        project_id = self.create_project('test')
        projects = self.list_projects(1)
        D = projects[0].model
        headers = [('project', 'test'),('project-id',str(project_id))]
        response = self.client.get('/api/analysis/scenarios/list', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertTrue('scenarios' in data)
        scenarios = data.get('scenarios')
        self.assertTrue(scenarios is not None)
        default_scenarios = tojson(defaultscenarios(D))
        self.assertEqual(scenarios, default_scenarios)

if __name__ == '__main__':
    unittest.main()
