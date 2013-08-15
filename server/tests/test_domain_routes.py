#!/usr/bin/env python
# encoding: utf-8

import unittest
from tests.base import *
from lib import utils


class TestDomainGetRoute(BaseRoutesTest):
    """
    Test GET /domains/ route
    """
    ROUTINE = '/domains/'
    DEFAULT_RETVAL = APIResponses.NOAUTH
    LOGIN_REQUIRED = True
    ADMIN_REQUIRED = False
    IGNORE_TEST = False

    GET_RETVAL = APIResponses.OK
    POST_RETVAL = APIResponses.NOTALLOWED
    PUT_RETVAL = APIResponses.NOTALLOWED
    DELETE_RETVAL = APIResponses.NOTALLOWED

    ANONYMOUS_DEFAULT = APIResponses.NOAUTH
    ANONYMOUS_GET = APIResponses.NOAUTH
    ANONYMOUS_DELETE = APIResponses.NOTALLOWED
    ANONYMOUS_PUT = APIResponses.NOAUTH
    ANONYMOUS_POST = APIResponses.NOTALLOWED


    GET_ARGS = {}

    #def test_domain_get(self):
    #    item = self.get('/domains', level=UserLevels.ANONYMOUS)
    #    self.assertAuthFailed(item)
    #    item = self.get('/domains', level=UserLevels.USER)
    #    self.assertOK(item)
    #    self.assertAuthSuccess(item)
    #    self.assertValidJSON(item)
    #    self.assertStatus(item, utils.OK_STATUS)
    #    self.assertJSONValueType(item, 'domains', list)

    #def test_domain_put(self):
    #    newdomain = {'name': 'example.com', 'dns_services': True}
    #    item = self.put('/domains/', newdomain)
    #    self.assertAuthFailed(item)
    #    item = self.put('/domains/', newdomain)
    #    self.assertOK(item)
    #    self.assertAuthSuccess(item)
    #    self.assertJSONValueType(item, 'id', int)
    #    self.assertJSONValueType(item, 'name', str)
    #    self.assertJSONValueType(item, 'member', int)
    #    self.assertJSONValueType(item, 'dns_services', bool)

if __name__ == '__main__':
    unittest.main()
