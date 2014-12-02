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
        expected_data = { "reason": "No project is open", "status": "NOK"}
        print "response data: %s" % response.data
        self.assertEqual(response.status_code, 401)

"""
test too complicated to set up atm, need to upload excel file to replicate the flow
    def test_scenario_params(self):
        from sim.parameters import parameter_name, parameters
        response = self.create_user()
        response = self.login()
        response = self.client.post('/api/project/create/test', data = '{}', follow_redirects=True)
        headers = [('project', 'test')]
        response = self.client.get('/api/analysis/scenarios/params', headers = headers)
        print(response)
        self.assertEqual(response.status_code, 200)
        params = json.loads(response.data)['params']
        self.assertTrue(len(params)>0)
        self.assertTrue(set(params[0].keys())==set(["keys", "name"]))
        all_parameters = parameters()
        self.assertTrue(parameter_name(all_parameters, ['condom','reg']) == 'Condom usage probability, regular partnerships')
"""

if __name__ == '__main__':
    unittest.main()
