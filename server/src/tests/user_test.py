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


if __name__ == '__main__':
    unittest.main()
