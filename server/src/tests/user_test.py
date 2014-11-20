#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest

class UserTestCase(OptimaTestCase, unittest.TestCase):

    def setUp(self):
        super(UserTestCase, self).setUp()

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def test_current(self):
        response = self.test_client.get('/api/user/current', follow_redirects=True)
        assert(response.status_code==401)

if __name__ == '__main__':
    unittest.main()
