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
        from server.webapp.dbconn import db
        from server.webapp.dbmodels import UserDb
        ''' Helper method to create project and save it to the database '''
        admin = UserDb("admin", self.admin_email, self.admin_password, True)
        db.session.add(admin)
        db.session.commit()
        return str(admin.id)

    def list_users(self):
        return self.client.get('/api/user?secret=%s' % self.admin_password)

    def test_current_no_login(self):
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 401)

    def test_current_with_login(self):
        response = self.create_user()
        response = self.login()
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["email"], "test@test.com")
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["is_admin"], False)

    def test_current_admin(self):
        self.create_admin_user()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/user/current', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["email"], self.admin_email)
        self.assertEqual(data["name"], "admin")
        self.assertEqual(data["is_admin"], True)

    def test_list_users_as_admin(self):
        self.create_admin_user()
        response = self.create_user()
        response = self.logout()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/user')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        users = data.get('users', None)
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2, users)
        test_user = users[1]
        self.assertEqual(test_user['id'], self.get_user_id_by_email(self.default_email))
        self.assertEqual(test_user['email'], "test@test.com")
        self.assertEqual(test_user['name'], "test")
        self.assertNotIn('password', test_user)

    def test_list_users(self):
        self.create_admin_user()
        response = self.create_user()
        response = self.list_users()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        users = data.get('users', None)
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        test_user = users[1]
        self.assertEqual(test_user['id'], self.get_user_id_by_email(self.default_email))
        self.assertEqual(test_user['email'], "test@test.com")
        self.assertEqual(test_user['name'], "test")
        self.assertNotIn('password', test_user)

    def test_list_all_projects(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        # create two users
        response = self.create_user()
        default_id = self.get_user_id_by_email(self.default_email)
        response = self.login(self.default_email, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as second user and create a project
        response = self.create_user(name='test2', email=other_email)
        other_user = self.get_user_id_by_email(other_email)
        response = self.login(other_email, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/project/all')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        projects = data.get('projects')
        self.assertIsNotNone(projects, data)
        self.assertEqual(len(projects), 2, projects)
        self.assertIn('user_id', projects[0])
        self.assertIn('user_id', projects[1])
        user_ids = [p['user_id'] for p in projects]
        self.assertEqual(set(user_ids), set([default_id, other_user]))

    def test_admin_list_own_projects(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        response = self.login(self.admin_email, self.admin_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as another user and create a project
        response = self.create_user(name='test2', email=other_email)
        response = self.login(other_email, self.test_password)
        response = self.api_create_project()
        response = self.logout()
        # log in as admin
        response = self.login(self.admin_email, self.admin_password)
        response = self.client.get('/api/project')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # now admin should only see his own project
        projects = data.get('projects')
        self.assertIsNotNone(projects)
        self.assertEqual(len(projects), 1)

    def test_delete_user(self):
        other_email = 'test2@test.com'
        self.create_admin_user()
        # create two users
        response = self.create_user()
        response = self.create_user(name='test2', email=other_email)
        # log in as second user and create a project
        response = self.login(email=other_email)
        response = self.api_create_project()
        response = self.logout()
        # list users, verify we have 3
        response = self.list_users()
        users = json.loads(response.data).get('users')
        self.assertEqual(len(users), 3)
        # list projects for the second user, verify we have 1
        test_id = self.get_user_id_by_email(other_email)
        projects = self.list_projects(test_id)
        self.assertEqual(len(projects), 1)
        # delete second user
        response = self.client.delete('/api/user/%s?secret=%s' % (test_id, self.admin_password))
        self.assertEqual(response.status_code, 204)
        # list users again, verify we have 1 and it's the first one
        response = self.list_users()
        users = json.loads(response.data).get('users')
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        emails = set([user['email'] for user in users])
        self.assertNotIn('test2@test.com', emails)
        # list projects for the second user and verify that they are gone
        projects = self.list_projects(self.get_any_user_id(admin=True))
        self.assertEqual(len(projects), 0)

    def test_modify_user(self):
        import hashlib
        admin_id = self.create_admin_user()
        response = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        new_email = 'test1@test.com'
        response = self.client.put('/api/user/%s?secret=%s&email=%s&password=%s'
            % (admin_id, self.admin_password, new_email, new_password))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('id'), admin_id)
        response = self.login(email=new_email, password=new_password)
        response = self.api_create_project()
        self.assertEqual(response.status_code, 201)
        self.logout()

    def test_modify_user_nonadmin(self):
        import hashlib
        response = self.create_user()
        new_password = hashlib.sha224("test1").hexdigest()
        new_email = 'test1@test.com'
        user_id = self.get_user_id_by_email(self.default_email)
        response = self.client.put('/api/user/%s?secret=%s&email=%s&password=%s'
            % (user_id, self.test_password, new_email, new_password))
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
