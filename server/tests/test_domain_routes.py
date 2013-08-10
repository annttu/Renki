#!/usr/bin/env python
# encoding: utf-8

import unittest
from tests.base import TestRoutes
from lib import utils


class TestDomainRoutes(TestRoutes):
    """
    Test server domain routes
    """
    def test_domain_get(self):
        item = self.get('/domains')
        self.assertAuthFailed(item)
        self.getKey()
        item = self.get('/domains')
        self.assertOK(item)
        self.assertAuthSuccess(item)
        self.assertValidJSON(item)
        self.assertStatus(item, utils.OK_STATUS)
        self.assertJSONValueType(item, 'domains', list)

    def test_domain_put(self):
        newdomain = {'name': 'example.com', 'dns_services': True}
        item = self.put('/domains/', newdomain)
        self.assertAuthFailed(item)
        self.getKey()
        item = self.put('/domains/', newdomain)
        self.assertOK(item)
        self.assertAuthSuccess(item)
        self.assertJSONValueType(item, 'id', int)
        self.assertJSONValueType(item, 'name', str)
        self.assertJSONValueType(item, 'member', int)
        self.assertJSONValueType(item, 'dns_services', bool)

if __name__ == '__main__':
    unittest.main()
