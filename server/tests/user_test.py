#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
from server.api import app
import json

class UserTestCase(OptimaTestCase):
    """
    Test class for the user blueprint covering all /api/user endpoints.

    """

    def setUp(self):
        import hashlib
        self.admin_email = "admin@test.com"
        self.admin_password = hashlib.sha224("admin").hexdigest()
        OptimaTestCase.setUp(self)

    def create_admin_user(self):
        from server.webapp.dbconn import db
        from server.webapp.dbmodels import UserDb
        ''' Helper method to create project and save it to the database '''
        admin = UserDb("admin", self.admin_email, self.admin_password, True)
        db.session.add(admin)
        db.session.commit()

    def list_users(self):
        return self.client.get('/api/user/list?secret=%s' % self.admin_password)

    def test_current_no_login(self):
        response = self.client.get('/api/user/current', follow_redirects=True)
        assert(response.status_code==401)

    def test_current_with_login(self):
        response = self.create_user()
        response = self.login()
        response = self.client.get('/api/user/current', follow_redirects=True)
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data["email"]=="test@test.com")
        assert(data["name"]=="test")
        assert(data["is_admin"]==False)

    def test_current_admin(self):
        self.create_admin_user()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/user/current', follow_redirects=True)
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data["email"]==self.admin_email)
        assert(data["name"]=="admin")
        assert(data["is_admin"]==True)

    def test_list_users_as_admin(self):
        self.create_admin_user()
        response = self.create_user()
        response = self.logout()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/user/list')
        assert(response.status_code==200)
        data = json.loads(response.data)
        users = data.get('users', None)
        assert(users is not None)
        assert(len(users)==2)
        test_user = users[1]
        assert(test_user['id']==2)
        assert(test_user['email']=="test@test.com")
        assert(test_user['name'] == "test")
        assert('password' not in test_user)

    def test_list_users(self):
        self.create_admin_user()
        response = self.create_user()
        response = self.list_users()
        assert(response.status_code==200)
        data = json.loads(response.data)
        users = data.get('users', None)
        assert(users is not None)
        assert(len(users)==2)
        test_user = users[1]
        assert(test_user['id']==2)
        assert(test_user['email']=="test@test.com")
        assert(test_user['name'] == "test")
        assert('password' not in test_user)

    def test_list_all_projects(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        #create two users
        response = self.create_user()
        response = self.api_create_project()
        response = self.logout()
        #log in as second user and create a project
        response = self.create_user(name='test2', email=other_email)
        response = self.api_create_project()
        response = self.logout()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/project/list/all')
        assert(response.status_code==200)
        data = json.loads(response.data)
        projects = data.get('projects')
        assert(projects is not None)
        assert(len(projects)==2)
        assert('user_id' in projects[0] and 'user_id' in projects[1])
        user_ids = [p['user_id'] for p in projects]
        assert(set(user_ids)==set([2,3]))

    def test_admin_list_own_projects(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        response = self.login(self.admin_email, self.admin_password)
        response = self.api_create_project()
        response = self.logout()
        #log in as another user and create a project
        response = self.create_user(name='test2', email=other_email)
        response = self.api_create_project()
        response = self.logout()
        #log in as admin
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/project/list')
        assert(response.status_code==200)
        data = json.loads(response.data)
        # now admin should only see his own project
        projects = data.get('projects')
        assert(projects is not None)
        assert(len(projects)==1)
        assert('user_id' not in projects[0])

    def test_delete_user(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        #create two users
        response = self.create_user()
        response = self.create_user(name='test2', email=other_email)
        #log in as second user and create a project
        response = self.login(email=other_email)
        response = self.api_create_project()
        response = self.logout()
        #list users, verify we have 3
        response = self.list_users()
        users = json.loads(response.data).get('users')
        assert(len(users)==3)
        #list projects for the second user, verify we have 1
        projects = self.list_projects(3)
        assert(len(projects)==1)
        #delete second user
        response = self.client.delete('/api/user/delete/3?secret=%s' % self.admin_password)
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data.get('deleted')=='3')
        #list users again, verify we have 1 and it's the first one
        response = self.list_users()
        users = json.loads(response.data).get('users')
        assert(users is not None)
        assert(len(users)==2)
        emails = set([user['email'] for user in users])
        assert('test2@test.com' not in emails)
        #list projects for the second user and verify that they are gone
        projects = self.list_projects(2)
        assert(len(projects)==0)

    def test_modify_user(self):
        import hashlib
        self.create_admin_user()
        response = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        new_email = 'test1@test.com'
        response = self.client.put('/api/user/modify/2?secret=%s&email=%s&password=%s' \
            % (self.admin_password, new_email, new_password))
        assert(response.status_code==200)
        data = json.loads(response.data)
        assert(data.get('modified')=='2')
        response = self.login(email=new_email, password = new_password)
        response = self.api_create_project()
        assert(response.status_code==200)
        response=self.logout()

    def test_modify_user_nonadmin(self):
        import hashlib
        response = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        new_email = 'test1@test.com'
        response = self.client.put('/api/user/modify/1?secret=%s&email=%s&password=%s' \
            % (self.test_password, new_email, new_password))
        assert(response.status_code==404)

if __name__ == '__main__':
    unittest.main()
