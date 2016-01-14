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
        self.user = self.create_user()
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
        project_id = self.create_project(name='test')

        response = self.client.get('/api/project/{}'.format(project_id))
        self.assertEqual(response.status_code, 200)
        project_data = json.loads(response.data)
        self.assertEqual(project_data['name'], 'test')

    def test_retrieve_project_list(self):
        project_id = self.create_project(name='test2')

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
        from server.webapp.dbmodels import ProjectDb
        from server.tests.factories import ProgsetsFactory, ProgramsFactory

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

        # create progsets and make sure they are part of the project
        progsets_count = 2
        for x in range(progsets_count):
            progset = self.create_record_with(ProgsetsFactory, project_id=project_id)
            self.create_record_with(ProgramsFactory, project_id=project_id, progset_id=progset.id)
        project = ProjectDb.query.filter_by(id=str(project_id)).first()
        self.assertEqual(len(project.progsets), progsets_count)

        response = self.client.post('/api/project/%s/copy' % project_id, data={
            'to': 'test_copy'
        })
        self.assertEqual(response.status_code, 200)
        copy_info = json.loads(response.data)
        new_project_id = copy_info['copy_id']
        # open the copy of the project
        # get info for the copy of the project
        response = self.client.get('/api/project/{}'.format(new_project_id))
        self.assertEqual(response.status_code, 200)
        new_info = json.loads(response.data)
        self.assertEqual(new_info['has_data'], True)
        # compare some elements
        self.assertEqual(old_info['populations'], new_info['populations'])
        self.assertEqual(old_info['dataStart'], new_info['dataStart'])
        self.assertEqual(old_info['dataEnd'], new_info['dataEnd'])

        new_project = ProjectDb.query.filter_by(id=str(new_project_id)).first()
        self.assertEquals(len(new_project.progsets), progsets_count)

    def _create_project_and_download(self, **kwargs):
        progsets_count = 3
        project = self.create_project(name='test', return_instance=True, progsets_count=progsets_count, **kwargs)

        self.assertEqual(len(project.progsets), progsets_count)

        # create a parset for the project
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        response = self.client.post('api/project/update', data=dict(file=example_excel))
        example_excel.close()

        response = self.client.get('/api/project/{}/data'.format(project.id))
        self.assertEqual(response.status_code, 200)

        return progsets_count, project, response

    def test_download_upload_project(self):
        from server.webapp.dbmodels import ProjectDb
        from server.webapp.dbconn import db
        from io import BytesIO

        progsets_count, project, response = self._create_project_and_download()
        # we need to get the project using the "regular" session instead of the "factory" session
        project = ProjectDb.query.filter_by(id=str(project.id)).first()
        project.name = 'Not test'
        project.progsets[0].recursive_delete('fetch')
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

    def test_download_upload_as_new_project(self):
        from server.webapp.dbmodels import ProjectDb
        from io import BytesIO

        progsets_count, project, response = self._create_project_and_download()

        upload_response = self.client.post(
            '/api/project/data',
            data={
                'name': 'upload_as_new',
                'file': (BytesIO(response.data), 'project.prj'),
            }
        )

        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        # loading new project from db after upload
        data = json.loads(upload_response.data)
        self.assertIn('id', data)

        project = ProjectDb.query.filter_by(id=data['id']).first()
        self.assertEqual(project.name, 'upload_as_new')
        self.assertEqual(len(project.progsets), progsets_count)
        self.assertNotEqual(project.progsets[0].programs[0].category, 'No category')

    def test_download_upload_on_copied_project(self):
        from server.webapp.dbmodels import ProjectDb
        from io import BytesIO

        progsets_count, project, response = self._create_project_and_download(populations=[
            {
                'age_to': 49,
                'age_from': 15,
                'name': "Female sex workers",
                'short_name': "FSW",
                'female': True,
                'male': False
            }, {
                'age_to': 49,
                'age_from': 15,
                'name': "Clients of sex workers",
                'short_name': "Clients",
                'female': False,
                'male': True
            }
        ])

        copy_response = self.client.post('/api/project/{}/copy'.format(project.id), data={
            'to': 'test_copy'
        })
        self.assertEqual(copy_response.status_code, 200)
        copy_info = json.loads(copy_response.data)
        new_project_id = copy_info['copy_id']

        upload_response = self.client.post(
            '/api/project/{}/data'.format(new_project_id),
            data={
                'file': (BytesIO(response.data), 'project.prj'),
            }
        )

        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        project = ProjectDb.query.filter_by(id=new_project_id).first()
        self.assertEqual(len(project.progsets), progsets_count)
        self.assertNotEqual(project.progsets[0].programs[0].category, 'No category')

    def test_delete_project_with_parsets(self):
        project_id = self.create_project()

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
        project_id = self.create_project()
        progset_id = self.api_create_progset(project_id)

        response = self.client.get('/api/project/{}/progsets/{}'.format(
            project_id,
            progset_id
        ))
        self.assertEqual(response.status_code, 200)

    def test_update_progset(self):
        from server.webapp.dbmodels import ProgsetsDb, ProgramsDb

        project_id = self.create_project(name='test_progset')
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

        project_id = self.create_project()
        progset_id = self.api_create_progset(project_id)

        response = self.client.delete('/api/project/{}/progsets/{}'.format(project_id, progset_id))
        self.assertEqual(response.status_code, 204)

        progset = ProgsetsDb.query.get(progset_id)
        self.assertIsNone(progset)

        program_count = ProgramsDb.query.filter_by(progset_id=progset_id).count()
        self.assertEqual(program_count, 0)

    def test_delete_project_with_progset(self):
        project = self.create_project(name='test_progset', return_instance=True, progsets_count=1)

        self.assertEquals(len(project.progsets), 1)

        response = self.client.delete('/api/project/{}'.format(project.id))
        self.assertEqual(response.status_code, 204)

    def test_retrieve_list_of_progsets(self):
        progsets_count = 3
        project = self.create_project(progsets_count=progsets_count, return_instance=True)
        self.assertEqual(len(project.progsets), progsets_count)

        response = self.client.get('/api/project/{}/progsets'.format(project.id))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue('progsets' in data)
        self.assertEqual(len(data['progsets']), progsets_count)

    def test_progset_can_hydrate_and_restore(self):
        from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ProjectDb

        programs_per_progset = 3
        pars = [
            {
                'param': 'condcas',
                'pops': ['MSM', 'MSF'],
                'active': True
            }, {
                'param': 'condcom',
                'pops': [('MSM', 'MSF'), ],
                'active': True
            }
        ]

        project = self.create_project(
            progsets_count=1,
            programs_per_progset=programs_per_progset,
            return_instance=True,
            pars=pars
        )
        progset_id = str(project.progsets[0].id)
        program = project.progsets[0].programs[0]
        program_name = program.short_name

        progset = ProgsetsDb.query.get(progset_id)
        program_count = ProgramsDb.query \
            .filter_by(progset_id=progset_id, active=True) \
            .count()
        self.assertEqual(program_count, programs_per_progset)
        programset = progset.hydrate()

        self.assertIsNotNone(programset)

        # reload from db
        project = ProjectDb.query.filter_by(id=str(project.id)).first()

        be_project = project.hydrate()
        new_project = self.create_project(return_instance=True)
        new_project.restore(be_project)

        programs = ProgramsDb.query \
            .filter_by(project_id=str(new_project.id), active=True) \
            .all()

        self.assertEqual(len(programs), programs_per_progset)

        program_names = [
            program.short_name
            for program in ProgramsDb.query
                .filter_by(project_id=str(new_project.id), active=True)
                .all()
        ]

        self.assertIn(program_name, program_names)

        program = ProgramsDb.query \
                .filter_by(project_id=str(new_project.id), active=True) \
                .filter_by(short_name=program_name).first()

        self.assertIsNotNone(program)
        self.assertEqual(len(program.pars), len(pars))

    def test_default_programs_for_project_restore(self):
        from server.webapp.dbmodels import ProgramsDb, ProjectDb
        from server.webapp.programs import get_default_programs
        from server.webapp.populations import populations

        project = self.create_project(
            progsets_count=1,
            programs_per_progset=0,
            return_instance=True,
            populations=populations()
        )
        progset_id = str(project.progsets[0].id)

        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        example_excel = open(file_path)
        # this will now restore default programs as well
        response = self.client.post(
            'api/project/{}/spreadsheet'.format(project.id),
            data=dict(file=example_excel)
        )
        example_excel.close()
        self.assertEqual(response.status_code, 200, response.data)

        project = ProjectDb.query.filter_by(id=project.id).first()
        be_project = project.hydrate()

        program_list = get_default_programs(be_project)
        program_count = ProgramsDb.query.filter_by(project_id=str(project.id)).count()

        self.assertEqual(program_count, len(program_list))

    def test_bulk_delete(self):
        from server.webapp.dbmodels import ProjectDb

        project_count = 5
        projects_to_delete = 2
        project_ids = [
            self.create_project(user_id=self.user.id)
            for i in range(project_count)
        ]

        self.assertEqual(ProjectDb.query.count(), project_count)

        # test bulk delete projects for current user

        response = self.client.delete('/api/project', data={'projects': project_ids[:projects_to_delete]})
        self.assertEqual(response.status_code, 204)
        projects_left = project_count - projects_to_delete
        self.assertEqual(ProjectDb.query.count(), projects_left)

        other_user = self.create_user()
        project_ids.append(self.create_project(user_id=other_user.id))
        projects_left += 1

        self.assertEqual(ProjectDb.query.count(), projects_left)

        response = self.client.delete('/api/project', data={'projects': project_ids[projects_to_delete:]})
        self.assertEqual(response.status_code, 410)
        self.assertEqual(ProjectDb.query.count(), projects_left)

    def test_portfolio(self):
        from io import BytesIO
        from zipfile import ZipFile
        from server.webapp.dbmodels import ProjectDb
        from optima.utils import load

        project_count = 5
        projects = [
            self.create_project(user_id=self.user.id, return_instance=True)
            for i in range(project_count)
        ]

        self.assertEqual(ProjectDb.query.count(), project_count)
        response = self.client.post(
            '/api/project/portfolio',
            data={'projects': [
                str(project.id)
                for project in projects
            ]})
        self.assertEqual(response.status_code, 200)

        first_project_filename = 'portfolio/{}.prj'.format(projects[0].name)
        zip_file = ZipFile(BytesIO(response.data))
        self.assertEqual(len(zip_file.namelist()), project_count)
        self.assertIn(first_project_filename, zip_file.namelist())

        project_file = BytesIO(zip_file.read(first_project_filename))
        be_project = load(project_file)
        self.assertEqual(be_project.name, projects[0].name)

    def test_parset_get(self):
        from server.webapp.dbmodels import ProjectDb
        parset_count = 2

        project_id = self.create_project(parset_count=parset_count)
        project = ProjectDb.query.filter_by(id=project_id).first()
        self.assertEqual(len(project.parsets), parset_count)

        response = self.client.get('/api/project/{}/parsets'.format(project.id))
        self.assertEqual(response.status_code, 200, response.data)

        parset_data = json.loads(response.data)
        self.assertIn('parsets', parset_data)
        self.assertEqual(len(parset_data['parsets']), parset_count)

    def test_parset_delete(self):
        from server.webapp.dbmodels import ProjectDb
        parset_count = 2

        project_id = self.create_project(parset_count=parset_count)
        project = ProjectDb.query.filter_by(id=project_id).first()
        self.assertEqual(len(project.parsets), parset_count)

        response = self.client.delete('/api/project/{}/parsets/{}'.format(
            project.id, project.parsets[0].id
        ))
        self.assertEqual(response.status_code, 204, response.data)

        project = ProjectDb.query.filter_by(id=project_id).first()
        self.assertEqual(len(project.parsets), parset_count - 1)


if __name__ == '__main__':
    unittest.main()
