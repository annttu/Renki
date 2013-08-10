#!/usr/bin/env python
# encoding: utf-8

import unittest
from tests.base import TestRoutes
from lib import utils, renki


class TestGenericRoutes(TestRoutes):
    """
    Test server user routes
    """
    def test_index(self):
        item = self.get('/')
        self.assertValidJSON(item)
        self.assertStatus(item, utils.OK_STATUS)

    def test_version(self):
        item = self.get('/version')
        self.assertValidJSON(item)
        self.assertOK(item)
        self.assertStatus(item, utils.OK_STATUS)
        self.assertJSONValue(item, 'version', renki.__version__)

    def test_error(self):
        item = self.get('/error')
        self.assertValidJSON(item)
        self.assertOK(item)
        self.assertStatus(item, utils.ERROR_STATUS)
        self.assertJSONContains(item, 'error')

if __name__ == '__main__':
    unittest.main()
