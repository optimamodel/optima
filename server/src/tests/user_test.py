#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
from api import app
import json

class UserTestCase(OptimaTestCase):
    """
    Test class for the user blueprint covering all /api/user endpoints.

    """

    def list_users(self):
        return self.client.get('/api/user/list?secret=%s' % self.test_password)

    def test_current_no_login(self):
        response = self.client.get('/api/user/current', follow_redirects=True)
        assert(response.status_code==401)


    def test_current_with_login(self):
        response = self.create_user()
        response = self.login()
        response = self.client.get('/api/user/current', follow_redirects=True)
        print("with_login: %s" % response)
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data["email"]=="test@test.com")
        assert(data["name"]=="test")


    def test_list_users(self):
        response = self.create_user()
        response = self.list_users()
        assert(response.status_code==200)
        data = json.loads(response.data)
        users = data.get('users', None)
        assert(users is not None)
        assert(len(users)==1)
        test_user = users[0]
        assert(test_user['id']==1)
        assert(test_user['email']=="test@test.com")
        assert(test_user['name'] == "test")
        assert('password' not in test_user)

    def test_delete_user(self):
        other_email = 'test2@test.com'
        #create two users
        response = self.create_user()
        response = self.create_user(name='test2', email=other_email)
        #log in as second user and create a project
        response = self.login(email=other_email)
        response = self.client.post('/api/project/create/test', data = '{}')
        response = self.logout()
        #list users, verify we have 2
        response = self.list_users()
        users = json.loads(response.data).get('users')
        assert(len(users)==2)
        #list projects for the second user, verify we have 1
        projects = self.list_projects(2)
        assert(len(projects)==1)
        #delete second user
        response = self.client.delete('/api/user/delete/2?secret=%s' % self.test_password)
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data.get('deleted') is not None)
        assert(data.get('status')=='OK')
        #list users again, verify we have 1 and it's the first one
        response = self.list_users()
        users = json.loads(response.data).get('users')
        assert(users is not None)
        assert(len(users)==1)
        assert(users[0]['email']=='test@test.com')
        #list projects for the second user and verify that they are gone
        projects = self.list_projects(2)
        assert(len(projects)==0)

    def test_modify_user(self):
        import hashlib
        response = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        new_email = 'test1@test.com'
        response = self.client.put('/api/user/modify/1?secret=%s&email=%s&password=%s' \
            % (self.test_password, new_email, new_password))
        assert(response.status_code==200)
        data = json.loads(response.data)
        print('modified:%s' % data)
        assert(data.get('status')=='OK')
        assert(data.get('modified')=='1')
        response = self.login(email=new_email, password = new_password)
        response = self.client.post('/api/project/create/test', data = '{}')
        assert(response.status_code==200)
        response=self.logout()

if __name__ == '__main__':
    unittest.main()
