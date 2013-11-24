#!/usr/bin/env python
# encoding: utf-8

from lib.test_utils import *


class TestIndexRoute(BasicTest):
    """
    Test / route
    """

    schema = [
        JSONString('info', required=True)
    ]

    def test_root_get_anon(self):
        """
        Test GET / route as anonymous
        """
        self.assertQ('/', user=None, status=STATUS_OK, schema=self.schema)

    def test_root_get_user(self):
        """
        Test GET / route as user
        """
        u = self.user('test', [])
        self.assertQ('/', user=u, status=STATUS_OK, schema=self.schema)


class TestVersionRoute(BasicTest):
    """
    Test /versin route
    """

    schema = [
        JSONString('version', required=True)
    ]

    def test_version_get_anon(self):
        """
        Test GET /version route as anonymous
        """
        self.assertQ('/version', user=None, status=STATUS_OK,
                     schema=self.schema)

    def test_version_get_user(self):
        """
        Test GET /version route as user
        """
        u = self.user('test', [])
        self.assertQ('/version', user=u, status=STATUS_OK, schema=self.schema)

class TestErrorRoute(BasicTest):
    """
    Test /error route
    """
    def test_error_get_anon(self):
        """
        Test GET /version route as anonymous
        """
        self.assertQ('/error', user=None, status=STATUS_ERROR)

    def test_error_get_user(self):
        """
        Test GET /version route as user
        """
        u = self.user('test', [])
        self.assertQ('/error', user=u, status=STATUS_ERROR)

if __name__ == "__main__":
    import unittest
    unittest.main()
