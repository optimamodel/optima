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

    def test_optimisation_start_response_without_a_project(self):
        response = self.client.get('/api/analysis/optimisation/start', follow_redirects=True)
        expected_data = { "reason": "No project is open", "status": "NOK"}
        print "response data: %s" % response.data
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
