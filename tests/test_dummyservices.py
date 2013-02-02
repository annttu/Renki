#!/usr/bin/env python
# encoding: utf-8

import unittest

from services.tests.dummy.dummy_services import *

class TestDummyServices(unittest.TestCase):

    def setUp(self):
        self.srv = DummyServices(username='unittest', password='', server='localhost',
                                 database='services')
        self.srv.login()

    def test_admin(self):
        self.assertFalse(self.srv.is_admin(), "This user should not be admin")

    def test_get_user(self):
        self.assertEqual(u"Unittest User", self.srv.get_user().name)

    def test_get_customer_id(self):
        self.assertEqual(65535, self.srv.get_customer_id(), "Test user customer_id " +
                         "should be 65535")

if __name__ == '__main__':
    unittest.main()
