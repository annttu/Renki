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
    IGNORE_DATABASE_FLUSH = True
    DEFAULT_RETVAL = APIResponses.NOAUTH
    LOGIN_REQUIRED = True
    ADMIN_REQUIRED = False
    IGNORE_TEST = False

    SKIP_PUT = True

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


class TestDomainPutRoute(BaseRoutesTest):
    """
    Test PUT /domains/ route
    """
    ROUTINE = '/domains/'
    DEFAULT_RETVAL = APIResponses.NOAUTH
    LOGIN_REQUIRED = True
    ADMIN_REQUIRED = False
    IGNORE_TEST = False

    SKIP_GET = True
    SKIP_POST = True
    SKIP_DELETE = True

    PUT_RETVAL = APIResponses.OK

    ANONYMOUS_DEFAULT = APIResponses.NOAUTH
    ANONYMOUS_PUT = APIResponses.NOAUTH

    PUT_ARGS = {'name': 'example.com', 'user_id': 2}

if __name__ == '__main__':
    unittest.main()
