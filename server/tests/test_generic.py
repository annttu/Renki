#!/usr/bin/env python
# encoding: utf-8

import unittest
from tests.base import BaseRoutesTest, APIResponses


class TestIndexRoute(BaseRoutesTest):
    """
    Test / route
    """
    LOGIN_REQUIRED = False
    IGNORE_DATABASE_FLUSH = True
    ROUTINE = '/'
    DEFAULT_RETVAL = APIResponses.OK
    POST_RETVAL = APIResponses.NOTALLOWED
    PUT_RETVAL = APIResponses.NOTALLOWED
    DELETE_RETVAL = APIResponses.NOTALLOWED
    IGNORE_TEST = False


class TestVersionRoute(BaseRoutesTest):
    """
    Test /versin route
    """
    LOGIN_REQUIRED = False
    IGNORE_DATABASE_FLUSH = True
    ROUTINE = '/version'
    DEFAULT_RETVAL = APIResponses.OK
    POST_RETVAL = APIResponses.NOTALLOWED
    PUT_RETVAL = APIResponses.NOTALLOWED
    DELETE_RETVAL = APIResponses.NOTALLOWED
    IGNORE_TEST = False

    RESPONSE_SCHEMA = {
        'type': "object",
        'properties': {
            'version': {'type': 'string'},
        },
        'required': ['version']
    }


class TestErrorRoute(BaseRoutesTest):
    """
    Test /error route
    """
    LOGIN_REQUIRED = False
    IGNORE_DATABASE_FLUSH = True
    ROUTINE = '/error'
    DEFAULT_RETVAL = APIResponses.ERROR
    POST_RETVAL = APIResponses.ERROR
    PUT_RETVAL = APIResponses.ERROR
    DELETE_RETVAL = APIResponses.ERROR
    IGNORE_TEST = False

    RESPONSE_SCHEMA = {
        'type': "object",
        'properties': {
            'version': {'type': 'string'},
        },
        'required': ['version']
    }

if __name__ == '__main__':
    unittest.main()
