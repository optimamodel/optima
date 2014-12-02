#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from optima.dbmodels import ProjectDb
from optima.dbconn import db

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

    def test_retrieve_project_info(self):
        # create project
        project = ProjectDb('test', 1, '2000', '2010', '2020', {}, {})
        db.session.add(project)
        db.session.commit()

        headers = [('project', 'test')]
        response = self.client.get('/api/project/info', headers=headers)
        self.assertEqual(response.status_code, 200)
        project_data = json.loads(response.data)
        self.assertEqual(project_data['name'], 'test')
        self.assertEqual(project_data['status'], 'OK')

    def test_retrieve_project_list(self):
        # create project
        project = ProjectDb('test2', 1, '2000', '2010', '2020', {}, {})
        db.session.add(project)
        db.session.commit()

        response = self.client.get('/api/project/list')
        self.assertEqual(response.status_code, 200)
        projects_data = json.loads(response.data)
        self.assertEqual(projects_data['projects'][0]['name'], 'test2')
        self.assertEqual(projects_data['projects'][0]['status'], 'OK')

    def test_project_params(self):
        from sim.parameters import parameter_name, parameters
        response = self.create_user()
        response = self.login()
        response = self.client.get('/api/project/params')
        print(response)
        self.assertEqual(response.status_code, 200)
        params = json.loads(response.data)['params']
        self.assertTrue(len(params)>0)
        self.assertTrue(set(params[0].keys())==set(["keys", "name", "modifiable"]))
        all_parameters = parameters()
        self.assertTrue(parameter_name(all_parameters, ['condom','reg']) == 'Condom usage probability, regular partnerships')


if __name__ == '__main__':
    unittest.main()
