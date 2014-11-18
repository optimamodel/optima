import os
import api
import unittest
import tempfile
import json

class ApiTestCase(unittest.TestCase):

  def setUp(self):
#        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
    api.app.config['TESTING'] = True
    api.app.config['LOGIN_DISABLED'] = True
    print("starting test app")
    api.app.login_manager.init_app(api.app)
   # self.app = flaskr.app.test_client()
    self.test_client = api.app.test_client()
#        flaskr.init_db()
  
  def test_create_project(self):
    headers = [('Content-Type', 'application/json')]
    data = {}
    json_data = json.dumps(data)
    json_data_length = len(json_data)
    headers.append(('Content-Length', json_data_length))
    response = self.test_client.post('/api/project/create/test', headers=headers, data = json_data, follow_redirects=True)
    print(dir(response))
    print (response.status)
    assert(response.status_code==200)


  def tearDown(self):
    print "tearDown"
    pass
 #       os.close(self.db_fd)
 #       os.unlink(flaskr.app.config['DATABASE'])

if __name__ == '__main__':
  unittest.main()