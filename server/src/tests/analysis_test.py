#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json

class AnalysisTestCase(OptimaTestCase, unittest.TestCase):
    """
    Test class for the analysis blueprint covering all /api/analysis endpoints.

    """

    def setUp(self):
        super(AnalysisTestCase, self).setUp()

    def tearDown(self):
        super(AnalysisTestCase, self).tearDown()

    def test_optimisation_start_response_without_a_project(self):
        response = self.test_client.get('/api/analysis/optimisation/start', follow_redirects=True)
        expected_data = { "reason": "No project is open", "status": "NOK"}
        self.assertEqual(json.loads(response.data), expected_data)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
