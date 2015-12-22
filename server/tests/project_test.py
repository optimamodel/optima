#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from server.api import app
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
        self.assertEqual(response.status_code, 201)

    def test_retrieve_project_info_fails(self):
        project_id = '{}'.format(uuid4())
        # It would probably be better to make sure the project id REALLY does not
        # exist first. But this is uuid, so the chances are quite slim
        response = self.client.get('/api/project/{}'.format(project_id))
        self.assertEqual(response.status_code, 410)

    def test_retrieve_project_info(self):
        project_id = self.create_project('test')

        response = self.client.get('/api/project/{}'.format(project_id))
        self.assertEqual(response.status_code, 200)
        project_data = json.loads(response.data)
        self.assertEqual(project_data['name'], 'test')

    def test_retrieve_project_list(self):
        project_id = self.create_project('test2')

        response = self.client.get('/api/project')
        self.assertEqual(response.status_code, 200)
        projects_data = json.loads(response.data)
        self.assertEqual(projects_data['projects'][0]['name'], 'test2')
        self.assertEqual(projects_data['projects'][0]['id'], str(project_id))

    def test_project_parameters(self):
        from server.webapp.parameters import parameter_name
        response = self.client.get('/api/project/parameters')
        print(response)
        self.assertEqual(response.status_code, 200)
        parameters = json.loads(response.data)['parameters']
        self.assertTrue(len(parameters) > 0)
        self.assertTrue(set(parameters[0].keys()) ==
            set(["keys", "name", "modifiable", "calibration", "dim", "input_keys", "page"]))
        self.assertTrue(parameter_name(['condom', 'reg']) ==
            'Condoms | Proportion of sexual acts in which condoms are used with regular partners')

    def test_upload_data(self):
        import re
        import os
        import filecmp
        # create project
        response = self.api_create_project()
        self.assertEqual(response.status_code, 201)
        project_id = str(response.headers['X-project-id'])
        # upload data
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        response = self.client.post(
            'api/project/{}/spreadsheet'.format(project_id),
            data=dict(file=example_excel)
        )
        example_excel.close()
        self.assertEqual(response.status_code, 200, response.data)
        # get data back and save the received file
        response = self.client.get('/api/project/%s/spreadsheet' % project_id)
        content_disposition = response.headers.get('Content-Disposition')
        self.assertTrue(len(content_disposition) > 0)
        file_name_info = re.search('filename=\s*(\S*)', content_disposition)
        self.assertTrue(len(file_name_info.groups()) > 0)
        file_name = file_name_info.group(1)
        self.assertEqual(file_name, 'test.xlsx')
        output_path = '/tmp/project_test.xlsx'
        if os.path.exists(output_path):
            os.remove(output_path)
        f = open(output_path, 'wb')
        f.write(response.data)
        f.close()
        # compare with source file
        result = filecmp.cmp(file_path, output_path)
        self.assertTrue(result)
        os.remove(output_path)

    def test_copy_project(self):
        # create project
        response = self.api_create_project()
        self.assertEqual(response.status_code, 201)
        project_id = str(response.headers['X-project-id'])
        # upload data so that we can check the existence of data in the copied project
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        response = self.client.post(
            '/api/project/{}/spreadsheet'.format(project_id),
            data=dict(file=example_excel)
        )
        example_excel.close()
        # get the info for the existing project
        response = self.client.get('/api/project/{}'.format(project_id))
        self.assertEqual(response.status_code, 200)
        old_info = json.loads(response.data)
        self.assertEqual(old_info['has_data'], True)
        response = self.client.post('/api/project/%s/copy?to=test_copy' % project_id)
        self.assertEqual(response.status_code, 200)
        copy_info = json.loads(response.data)
        new_project_id = copy_info['copy_id']
        # open the copy of the project
        # get info for the copy of the project
        response = self.client.get('/api/project/{}'.format(new_project_id))
        self.assertEqual(response.status_code, 200)
        new_info = json.loads(response.data)
        self.assertEqual(old_info['has_data'], True)
        # compare some elements
        self.assertEqual(old_info['populations'], new_info['populations'])
        self.assertEqual(old_info['dataStart'], new_info['dataStart'])
        self.assertEqual(old_info['dataEnd'], new_info['dataEnd'])

    def test_download_upload_project(self):
        from io import BytesIO
        from server.webapp.dbmodels import ProjectDb
        from server.webapp.dbconn import db

        progsets_count = 3
        project = self.create_project('test', return_instance=True, progsets_count=progsets_count)

        self.assertEqual(len(project.progsets), progsets_count)

        # create a parset for the project
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        response = self.client.post('api/project/update', data=dict(file=example_excel))
        example_excel.close()

        response = self.client.get('/api/project/{}/data'.format(project.id))
        self.assertEqual(response.status_code, 200)

        # we need to get the project using the "regular" session instead of the "factory" session
        project = ProjectDb.query.filter_by(id=str(project.id)).first()
        project.name = 'Not test'
        project.progsets[0].recursive_delete()
        db.session.commit()

        project = ProjectDb.query.filter_by(id=str(project.id)).first()
        self.assertEqual(len(project.progsets), progsets_count - 1)
        self.assertNotEqual(project.name, 'test')  # still just making sure

        upload_response = self.client.post(
            '/api/project/{}/data'.format(project.id),
            data={
                'file': (BytesIO(response.data), 'project.prj'),
            }
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        # reloading from db after upload
        project = ProjectDb.query.filter_by(id=str(project.id)).first()
        self.assertEqual(project.name, 'test')
        self.assertEqual(len(project.progsets), progsets_count)
        self.assertNotEqual(project.progsets[0].programs[0].category, 'No category')

    def test_delete_project_with_parsets(self):
        project_id = self.create_project('test')

        # create a parset and result for the project
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        self.client.post(
            'api/project/{}/spreadsheet'.format(project_id),
            data=dict(file=example_excel))
        example_excel.close()

        response = self.client.delete('api/project/{}'.format(project_id))
        self.assertEqual(response.status_code, 204)

    def test_create_and_retrieve_progset(self):
        project_id = self.create_project('test_progset')
        progset_id = self.api_create_progset(project_id)

        response = self.client.get('/api/project/{}/progsets/{}'.format(
            project_id,
            progset_id
        ))
        self.assertEqual(response.status_code, 200)

    def test_update_progset(self):
        from server.webapp.dbmodels import ProgsetsDb, ProgramsDb

        project_id = self.create_project('test_progset')
        progset_id = self.api_create_progset(project_id)

        data = self.progset_test_data.copy()
        data['name'] = 'Edited progset'
        data['programs'][0]['active'] = False
        program_name = data['programs'][0]['name']

        headers = {'Content-Type': 'application/json'}
        response = self.client.put(
            '/api/project/{}/progsets/{}'.format(project_id, progset_id),
            data=json.dumps(data),
            headers=headers
        )
        self.assertEqual(response.status_code, 200, response.data)

        progset = ProgsetsDb.query.get(progset_id)
        self.assertEqual(progset.name, 'Edited progset')
        # looping around all programs to make sure no ancient data is left over
        for program in ProgramsDb.query.filter_by(progset_id=progset_id, name=program_name):
            self.assertEqual(program.active, False)

    def test_delete_progset(self):
        from server.webapp.dbmodels import ProgsetsDb, ProgramsDb

        project_id = self.create_project('test_progset')
        progset_id = self.api_create_progset(project_id)

        response = self.client.delete('/api/project/{}/progsets/{}'.format(project_id, progset_id))
        self.assertEqual(response.status_code, 204)

        progset = ProgsetsDb.query.get(progset_id)
        self.assertIsNone(progset)

        program_count = ProgramsDb.query.filter_by(progset_id=progset_id).count()
        self.assertEqual(program_count, 0)

    def test_delete_project_with_progset(self):
        project = self.create_project('test_progset', return_instance=True, progsets_count=1)

        self.assertEquals(len(project.progsets), 1)

        response = self.client.delete('/api/project/{}'.format(project.id))
        self.assertEqual(response.status_code, 204)

    def test_retrieve_list_of_progsets(self):
        project_id = self.create_project('test_progset')
        self.api_create_progset(project_id)
        self.api_create_progset(project_id)
        self.api_create_progset(project_id)

        response = self.client.get('/api/project/{}/progsets'.format(project_id))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue('progsets' in data)
        self.assertEqual(len(data['progsets']), 3)

    def test_progset_can_hydrate(self):
        from server.webapp.dbmodels import ProgsetsDb

        project_id = self.create_project('test_progset')
        progset_id = self.api_create_progset(project_id)

        progset = ProgsetsDb.query.get(progset_id)
        programset = progset.hydrate()

        self.assertIsNotNone(programset)

if __name__ == '__main__':
    unittest.main()
