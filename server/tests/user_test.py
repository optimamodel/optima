#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
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
        from server.tests.factories import UserFactory
        ''' Helper method to create project and save it to the database '''
        return self.create_record_with(UserFactory, name='admin',
            password=self.admin_password, is_admin=True)

    def list_users(self):
        return self.client.get('/api/user?secret=%s' % self.admin_password)

    def test_current_no_login(self):
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 401)

    def test_current_with_login(self):
        user = self.create_user()
        response = self.login()
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], user.username)
        self.assertEqual(data['email'], user.email)

    def test_current_admin(self):
        admin = self.create_admin_user()
        response = self.login(admin.username, self.admin_password)
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], admin.username)
        self.assertEqual(data['email'], admin.email)
        self.assertEqual(data['is_admin'], admin.is_admin)
        self.assertEqual(data['displayName'], 'admin')

    def test_list_users_as_admin(self):
        admin = self.create_admin_user()
        user = self.create_user()
        response = self.logout()
        response = self.login(admin.username, self.admin_password)
        response = self.client.get('/api/user')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        users = data.get('users', None)
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2, users)
        test_user = users[1]
        self.assertEqual(test_user['id'], str(user.id))
        self.assertEqual(test_user['email'], user.email)
        self.assertNotIn('password', test_user)

    def test_list_users(self):
        self.create_admin_user()
        user = self.create_user()
        response = self.list_users()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        users = data.get('users', None)
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        test_user = users[1]
        self.assertEqual(test_user['id'], str(user.id))
        self.assertEqual(test_user['email'], user.email)
        self.assertNotIn('password', test_user)

    def test_list_all_projects(self):
        admin = self.create_admin_user()
        # create two users
        user = self.create_user()
        response = self.login(user.username, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as second user and create a project
        other_user = self.create_user(username='test2')
        response = self.login(other_user.username, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        response = self.login(admin.username, self.admin_password)
        response = self.client.get('/api/project/all')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        projects = data.get('projects')
        self.assertIsNotNone(projects, data)
        self.assertEqual(len(projects), 2, projects)
        self.assertIn('user_id', projects[0])
        self.assertIn('user_id', projects[1])
        user_ids = [p['user_id'] for p in projects]
        self.assertEqual(set(user_ids), set([str(user.id), str(other_user.id)]))

    def test_admin_list_own_projects(self):
        admin = self.create_admin_user()
        response = self.login(admin.username, self.admin_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as another user and create a project
        user = self.create_user(username='test2')
        response = self.login(user.username, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as admin
        response = self.login(admin.username, self.admin_password)
        response = self.client.get('/api/project')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # now admin should only see his own project
        projects = data.get('projects')
        self.assertIsNotNone(projects)
        self.assertEqual(len(projects), 1)

    def test_delete_user(self):
        self.create_admin_user()
        # create two users
        user = self.create_user()
        other_user = self.create_user(username='test2')
        # log in as second user and create a project
        response = self.login(username=other_user.username)
        response = self.api_create_project()
        response = self.logout()
        # list users, verify we have 3
        response = self.list_users()
        users = json.loads(response.data).get('users')
        self.assertEqual(len(users), 3)
        # list projects for the second user, verify we have 1
        projects = self.list_projects(str(other_user.id))
        self.assertEqual(len(projects), 1)
        # delete second user
        response = self.client.delete('/api/user/%s?secret=%s' % (other_user.id, self.admin_password))
        self.assertEqual(response.status_code, 204)
        # list users again, verify we have 1 and it's the first one
        response = self.list_users()
        users = json.loads(response.data).get('users')
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        emails = set([user['email'] for user in users])
        self.assertNotIn(other_user.email, emails)
        # list projects for the second user and verify that they are gone
        projects = self.list_projects(self.get_any_user_id(admin=True))
        self.assertEqual(len(projects), 0)

    def test_modify_user(self):
        import hashlib
        admin = self.create_admin_user()
        self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        username = 'new_username'
        response = self.client.put('/api/user/%s?secret=%s&username=%s&password=%s'
            % (str(admin.id), self.admin_password, username, new_password))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('id'), str(admin.id))
        response = self.login(username=username, password=new_password)
        response = self.api_create_project()
        self.assertEqual(response.status_code, 201)
        self.logout()

    def test_modify_user_nonadmin(self):
        import hashlib
        user = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        username = 'new_username'
        response = self.client.put('/api/user/%s?secret=%s&username=%s&password=%s'
            % (user.id, self.test_password, username, new_password))
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
