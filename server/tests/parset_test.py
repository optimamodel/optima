import json

from optima_test_base import OptimaTestCase
from flask import helpers
from server.api import app
from server.webapp.dbmodels import ProjectDb


class ParsetTestCase(OptimaTestCase):

    def setUp(self):
        super(ParsetTestCase, self).setUp()
        self.user = self.create_user()
        self.login()

        project_res = self.api_create_project()
        self.assertEqual(project_res.status_code, 201)
        self.project_id = str(project_res.headers['X-project-id'])
        print ">> Project returned {0}".format(self.project_id)

        # upload spreadsheet for newly created project that will create parsets as well
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        with open(file_path) as f:
            self.client.post('api/project/{}/spreadsheet'.format(self.project_id), data=dict(file=f))

    def test_get_parsets(self):
        # retrieve parsets  project -> id -> parsets
        response = self.client.get('api/project/{}/parsets'.format(self.project_id))

        # check there is one parset with name 'default'
        data = json.loads(response.data)
        self.assertTrue('parsets' in data)
        self.assertEqual(data['parsets'][0]['name'], 'default')

    def test_retrieve_calibrated_parameters(self):
        project = ProjectDb.query.get(self.project_id)

        parsets_response = self.client.get('api/project/{}/parsets'.format(self.project_id))
        parsets_data = json.loads(parsets_response.data)
        parset_id = parsets_data['parsets'][0]['id']

        calibrated_res = self.client.get('/api/parset/{}/calibration'.format(parset_id))
        calibrated_res_data = json.loads(calibrated_res.data)
        self.assertTrue('calibration' in calibrated_res_data)

        calibration_data = calibrated_res_data['calibration']
        self.assertEqual(calibration_data['parset_id'], parset_id)
        self.assertTrue(len(calibration_data['parameters']) > 0)
        self.assertTrue(len(calibration_data['selectors']) > 0)

        # We should expect len(populations) + 2 graphs -- total + one for each
        # population + one with all populations together.
        self.assertTrue(len(calibration_data['graphs']) > 0)

    def test_show_other_graph(self):
        parsets_response = self.client.get('api/project/{}/parsets'.format(self.project_id))
        parsets_data = json.loads(parsets_response.data)
        parset_id = parsets_data['parsets'][0]['id']

        calibrated_res = self.client.get('/api/parset/{}/calibration'.format(parset_id))
        calibrated_res_data = json.loads(calibrated_res.data)
        calibration_data = calibrated_res_data['calibration']
        third_graph_key = calibration_data['selectors'][2]['key']

        recalibrated_res = self.client.get('/api/parset/{0}/calibration?which={1}'.format(parset_id, third_graph_key))
        recalibrated_res_data = json.loads(recalibrated_res.data)
        self.assertTrue('calibration' in recalibrated_res_data)
        self.assertEqual(len(recalibrated_res_data['calibration']['graphs']), 1)

    def test_recalibrate_with_updated_parameters(self):
        parsets_response = self.client.get('api/project/{}/parsets'.format(self.project_id))
        parsets_data = json.loads(parsets_response.data)
        parset_id = parsets_data['parsets'][0]['id']

        calibrated_res = self.client.get('/api/parset/{}/calibration'.format(parset_id))
        calibrated_res_data = json.loads(calibrated_res.data)
        calibration_data = calibrated_res_data['calibration']

        updated_parameters = calibration_data['parameters']

        expectedParameterValue = 0.1
        for p in updated_parameters:
            if p['key'] == 'aidstest':
                p['value'] = expectedParameterValue
        headers = {'Content-Type': 'application/json'}
        recalibrated_res = self.client.put(
                '/api/parset/{0}/calibration'.format(parset_id),
                data=json.dumps({'parameters': updated_parameters}),
                headers=headers
        )
        recalibrated_res_data = json.loads(recalibrated_res.data)

        self.assertTrue('calibration' in recalibrated_res_data)
        recalibrated_data = recalibrated_res_data['calibration']

        project = ProjectDb.query.get(self.project_id)

        # We should expect len(populations) + 2 graphs -- total + one for each
        # population + one with all populations together.
        self.assertTrue(len(recalibrated_data['graphs']) > 0)

        self.assertIn('aidstest', [p['key'] for p in recalibrated_data['parameters']])
        for p in recalibrated_data['parameters']:
            if p['key'] == 'aidstest':
                self.assertEqual(p['value'], expectedParameterValue)
