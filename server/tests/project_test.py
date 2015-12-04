#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from api import app
from flask import helpers
from uuid import uuid4


class ProjectTestCase(OptimaTestCase):
    """
    Test class for the project blueprint covering all /api/project endpoints.

    """

    def setUp(self):
        super(ProjectTestCase, self).setUp()
        self.create_user()
        self.login()

    def test_create_project(self):
        response = self.api_create_project()
        self.assertEqual(response.status_code, 200)

    def test_retrieve_project_info_fails(self):
        project_id = '{}'.format(uuid4())
        # It would probably be better to make sure the project id REALLY does not
        # exist firt. But this is uuid, so the chances are quite slim
        headers = [('project', 'test'), ('project-id', project_id)]
        response = self.client.get('/api/project/info', headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data), {
            u'reason': u'Project {} does not exist'.format(project_id)
        })

    def test_retrieve_project_info(self):
        project_id = self.create_project('test')

        headers = [('project', 'test'), ('project-id', str(project_id))]
        response = self.client.get('/api/project/info', headers=headers)
        self.assertEqual(response.status_code, 200)
        project_data = json.loads(response.data)
        self.assertEqual(project_data['name'], 'test')

    # def test_retrieve_project_list(self):
    #     project_id = self.create_project('test2')

    #     response = self.client.get('/api/project/list')
    #     self.assertEqual(response.status_code, 200)
    #     projects_data = json.loads(response.data)
    #     self.assertEqual(projects_data['projects'][0]['name'], 'test2')
    #     self.assertEqual(projects_data['projects'][0]['id'], project_id)

    # def test_project_parameters(self):
    #     from sim.parameters import parameter_name
    #     response = self.client.get('/api/project/parameters')
    #     print(response)
    #     self.assertEqual(response.status_code, 200)
    #     parameters = json.loads(response.data)['parameters']
    #     self.assertTrue(len(parameters)>0)
    #     self.assertTrue(set(parameters[0].keys())== \
    #         set(["keys", "name", "modifiable", "calibration", "dim", "input_keys", "page"]))
    #     self.assertTrue(parameter_name(['condom','reg']) == 'Condoms | Proportion of sexual acts in which condoms are used with regular partners')

    # def test_upload_data(self):
    #     import re
    #     import os
    #     import filecmp
    #     # create project
    #     response = self.api_create_project()
    #     self.assertEqual(response.status_code, 200)
    #     project_id = int(response.headers['x-project-id'])
    #     # upload data
    #     example_excel_file_name = 'example.xlsx'
    #     file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
    #     example_excel = open(file_path)
    #     headers = [('project', 'test'),('project-id',str(project_id))]
    #     response = self.client.post('api/project/update', headers=headers, data=dict(file=example_excel))
    #     example_excel.close()
    #     self.assertEqual(response.status_code, 200)
    #     # get data back and save the received file
    #     response = self.client.get('/api/project/workbook/%s' % project_id)
    #     content_disposition = response.headers.get('Content-Disposition')
    #     self.assertTrue(len(content_disposition)>0)
    #     file_name_info = re.search('filename=\s*(\S*)', content_disposition)
    #     self.assertTrue(len(file_name_info.groups())>0)
    #     file_name = file_name_info.group(1)
    #     self.assertEqual(file_name,'test.xlsx')
    #     output_path = '/tmp/project_test.xlsx'
    #     if os.path.exists(output_path):os.remove(output_path)
    #     f = open(output_path, 'wb')
    #     f.write(response.data)
    #     f.close()
    #     # compare with source file
    #     result = filecmp.cmp(file_path, output_path)
    #     self.assertTrue(result)
    #     os.remove(output_path)

    # def test_copy_project(self):
    #     # create project
    #     response = self.api_create_project()
    #     self.assertEqual(response.status_code, 200)
    #     project_id = int(response.headers['x-project-id'])
    #     # upload data so that we can check the existence of data in the copied project
    #     example_excel_file_name = 'example.xlsx'
    #     file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
    #     example_excel = open(file_path)
    #     headers = [('project', 'test'),('project-id',str(project_id))]
    #     response = self.client.post('api/project/update', headers=headers, data=dict(file=example_excel))
    #     example_excel.close()
    #     #get the info for the existing project
    #     response = self.client.get('/api/project/info', headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     old_info=json.loads(response.data)
    #     self.assertEqual(old_info['has_data'], True)
    #     response = self.client.post('/api/project/copy/%s?to=test_copy' % project_id, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     copy_info = json.loads(response.data)
    #     new_project_id=copy_info['copy_id']
    #     #open the copy of the project
    #     response = self.client.get('/api/project/open/%s' % new_project_id, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     #get info for the copy of the project
    #     headers = [('project', 'test_copy'),('project-id',str(new_project_id))]
    #     response = self.client.get('/api/project/info', headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     new_info = json.loads(response.data)
    #     self.assertEqual(old_info['has_data'], True)
    #     #compare some elements
    #     self.assertEqual(old_info['populations'], new_info['populations'])
    #     self.assertEqual(old_info['programs'], new_info['programs'])


if __name__ == '__main__':
    unittest.main()
