#!/usr/bin/env python
# encoding: utf-8


from lib import renki, utils
from lib.enums import JSON_STATUS
# Register routes
import routes

from webtest import TestApp, AppError
import unittest
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JSONValidationError


class UserLevels:
    ADMIN = 'A'
    USER = 'U'
    NORMAL = USER
    ANONYMOUS = 'N'
    ALL = [ADMIN, USER, ANONYMOUS]


class APIResponses:
    OK = 1
    ERROR = 2
    NOAUTH = 3
    DENIED = 4
    DEFAULT = 5
    NOTALLOWED = 6


def validate_value(value, validator):
    if isinstance(validator, type(lambda x: x)):
        return validator(value)
    elif validator in [int, str, list, dict]:
        return isinstance(value, validator)
    return value == validator


def module_name():
    return __file__.split('/')[-1]

# REQUEST vars


class Required:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value


class Optional:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value


class Invalid:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value


class BaseRoutesTest(unittest.TestCase):

    LOGIN_REQUIRED = True
    ADMIN_REQUIRED = False
    IGNORE_TEST = False

    ROUTINE = None
    POST_ARGS = []
    GET_ARGS = []
    PUT_ARGS = []
    DELETE_ARGS = []

    DEFAULT_RETVAL = APIResponses.OK
    GET_RETVAL = APIResponses.DEFAULT
    POST_RETVAL = APIResponses.NOTALLOWED
    PUT_RETVAL = APIResponses.NOTALLOWED
    DELETE_RETVAL = APIResponses.NOTALLOWED

    # JSONSchema used to validate retval
    RESPONSE_SCHEMA = {}

    ANONYMOUS_DEFAULT = APIResponses.DEFAULT
    ANONYMOUS_POST = APIResponses.DEFAULT
    ANONYMOUS_PUT = APIResponses.DEFAULT
    ANONYMOUS_GET = APIResponses.DEFAULT
    ANONYMOUS_DELETE = APIResponses.DEFAULT

    USER_DEFAULT = APIResponses.DEFAULT
    USER_POST = APIResponses.DEFAULT
    USER_PUT = APIResponses.DEFAULT
    USER_GET = APIResponses.DEFAULT
    USER_DELETE = APIResponses.DEFAULT

    ADMIN_DEFAULT = APIResponses.DEFAULT
    ADMIN_POST = APIResponses.DEFAULT
    ADMIN_PUT = APIResponses.DEFAULT
    ADMIN_GET = APIResponses.DEFAULT
    ADMIN_DELETE = APIResponses.DEFAULT

    @classmethod
    def setUpClass(cls):
        if cls.ROUTINE is None:
            cls.IGNORE_TEST = True

    def setUp(self):

        renki.app.catchall = False
        self.app = TestApp(renki.app)
        self.userkey = None
        self.adminkey = None
        self.getKeys()

    def getKeys(self):
        self.getUserKey()
        self.getAdminKey()

    def getUserKey(self):
        r = self.post('/login', {'username': 'test', 'password': 'test'})
        if 'key' in r.json:
            self.userkey = r.json['key']

    def getAdminKey(self):
        r = self.post('/login', {'username': 'admin', 'password': 'admin'})
        if 'key' in r.json:
            self.adminkey = r.json['key']

    def _getKey(self, params={}, level=UserLevels.ANONYMOUS):
        if level == UserLevels.USER:
            params['key'] = self.userkey
        elif level == UserLevels.ADMIN:
            params['key'] = self.adminkey
        return params

    def get(self, url, params={}, level=UserLevels.ANONYMOUS):
        params = self._getKey(params=params, level=level)
        return self.app.get(url, params=params, status="*")

    def post(self, url, data={}, level=UserLevels.ANONYMOUS):
        data = self._getKey(params=data, level=level)
        return self.app.post_json(url, data, status="*")

    def put(self, url, data={}, level=UserLevels.ANONYMOUS):
        data = self._getKey(params=data, level=level)
        return self.app.put_json(url, data, status="*")

    def delete(self, url, params={}, level=UserLevels.ANONYMOUS):
        params = self._getKey(params=params, level=level)
        return self.app.delete(url, params=params, status="*")

    def assertValidJSON(self, item, schema=None):
        self.assertTrue(item.content_type == 'application/json',
                        "Content type not JSON")
        self.assertTrue('status' in item.json, 'status is mandatory argument')
        if schema:
            try:
                jsonschema_validate(item.json, schema=schema)
            except JSONValidationError:
                raise AssertionError("Response json is not valid")

    def assertStatus(self, item, status=JSON_STATUS.OK):
        self.assertEqual(item.json['status'], status,
                         "Invalid status code %s, excepted %s" % (
                                    item.json['status'], status))

    def assertJSONContains(self, item, key):
        self.assertTrue(key in item.json,
                        '%s not found from JSON' % key)

    def assertJSONValue(self, item, key, value):
        self.assertJSONContains(item, key)
        self.assertTrue(item.json[key] == value,
                        "Value of key %s is invalid" % key)

    def assertJSONValueType(self, item, key, type):
        self.assertJSONContains(item, key)
        self.assertTrue(isinstance(item.json[key], type),
                        "Value of key %s have invalid type" % key)

    def assertHTTPStatus(self, item, code, msg=None):
        if not msg:
            msg = "Status code is not %s" % code
        self.assertEqual(item.status_int, code, msg)

    def assertContent(self, item, content):
        for k, v in content.items():
            self.assertTrue(k in item.json, "Key %s not in response" % k)
            if isinstance(v, type(lambda x: x)):
                # v is validator
                self.assertTrue(v(item.json[k]))
            else:
                self.assertEquals(item.json[k], v, "Invalid value for key %s"
                                  % k)

    def assertOK(self, item):
        self.assertHTTPStatus(item, 200)
        self.assertStatus(item, JSON_STATUS.OK)

    def assertERROR(self, item):
        self.assertStatus(item, JSON_STATUS.ERROR)
        self.assertHTTPStatus(item, 400)
        self.assertContent(item, {'error': lambda x: bool(x)})

    def assertNOTALLOWED(self, item):
        self.assertHTTPStatus(item, 405)
        self.assertStatus(item, JSON_STATUS.NOTALLOWED)
        self.assertContent(item, {'error': lambda x: bool(x)})

    def assertDENIED(self, item):
        self.assertStatus(item, JSON_STATUS.DENIED)
        self.assertHTTPStatus(item, 401)
        self.assertContent(item, {'error': lambda x: bool(x)})

    def assertAuthFailed(self, item):
        self.assertHTTPStatus(item, 401,
                         "Authentication error not given")
        self.assertStatus(item, JSON_STATUS.NOAUTH)

    def assertAuthSuccess(self, item):
        self.assertHTTPStatus(item, 200)
        self.assertStatus(item, JSON_STATUS.OK)

    def test_keys(self):
        """
        Test key fetch
        """
        self.assertTrue(self.userkey is not None, "API key request failed")
        self.assertTrue(self.adminkey is not None, "API key request failed")
        item = self.get('/login/valid', level=UserLevels.USER)
        self.assertOK(item)
        item = self.get('/login/valid', level=UserLevels.ADMIN)
        self.assertOK(item)

    def resolve_excepted(self, method, level):
        """
        Resolve excepted output.

        Value is resolved from most spesific to least specific.

        <LEVEL>_<METHOD>
        <LEVEL>_DEFAULT
        <METHOD>_RETVAL
        DEFAULT_RETVAL
        """
        excepted = getattr(self, '%s_%s' % (level, method))
        level_default = getattr(self, '%s_DEFAULT' % level)
        if (self.LOGIN_REQUIRED or self.ADMIN_REQUIRED) \
                and level == 'ANONYMOUS':
            if excepted == APIResponses.DEFAULT and \
                    level_default == APIResponses.DEFAULT:
                return APIResponses.NOAUTH
        elif self.ADMIN_REQUIRED and level == 'USER':
            if excepted == APIResponses.DEFAULT and \
                    level_default == APIResponses.DEFAULT:
                return APIResponses.DENIED
        if excepted == APIResponses.DEFAULT:
            excepted = getattr(self, '%s_DEFAULT' % level)
        if excepted == APIResponses.DEFAULT:
            excepted = getattr(self, '%s_RETVAL' % method)
        if excepted == APIResponses.DEFAULT:
            excepted = self.DEFAULT_RETVAL
        return excepted

    def do_test(self, method, level, args=None):
        """
        Do test as user @level with method @method

        @param level: User permission level to use in test
        @type level: enum [USER, ADMIN, ANONYMOUS]
        @param method: HTTP method to use in test [POST,GET,PUT,DELETE]
        @type param: enum
        """
        if self.IGNORE_TEST:
            print("Skipping")
            unittest.skip('Ignored test')
            return
        if not args:
            args = getattr(self, '%s_ARGS' % method)
        if level in ['USER', 'ANONYMOUS', 'ADMIN']:
            level_enum = getattr(UserLevels, level)
        if method == 'DELETE':
            item = self.delete(self.ROUTINE, params=args,
                               level=level_enum)
        elif method == 'POST':
            item = self.post(self.ROUTINE, data=args,
                            level=level_enum)
        elif method == 'PUT':
            item = self.put(self.ROUTINE, data=args,
                            level=level_enum)
        else:
            item = self.get(self.ROUTINE, params=args,
                            level=level_enum)
        excepted = self.resolve_excepted(method, level)
        if excepted == APIResponses.ERROR:
            self.assertERROR(item)
        elif excepted == APIResponses.DENIED:
            self.assertDENIED(item)
        elif excepted == APIResponses.OK:
            self.assertOK(item)
            self.assertValidJSON(item, schema=self.RESPONSE_SCHEMA)
        elif excepted == APIResponses.NOTALLOWED:
            self.assertNOTALLOWED(item)
        elif excepted == APIResponses.NOAUTH:
            self.assertAuthFailed(item)
        else:
            raise AssertionError('Invalid excepted value %s' % excepted)

    #@unittest.skipIf(module_name() == 'base.py',  'Base test')
    def test_anonymous_get(self):
        """
        Test get as anonymous user
        """
        self.do_test('GET', 'ANONYMOUS')

    #@unittest.skipIf(module_name() == 'base.py',  'Base test')
    def test_anonymous_put(self):
        """
        Test put as anonymous user
        """
        self.do_test('PUT', 'ANONYMOUS')

    #@unittest.skipIf(module_name() == 'base.py',  'Base test')
    def test_anonymous_post(self):
        """
        Test post as anonymous user
        """
        self.do_test('POST', 'ANONYMOUS')

    #@unittest.skipIf(module_name() == 'base.py',  'Base test')
    def test_anonymous_delete(self):
        """
        Test delete as anonymous user
        """
        self.do_test('DELETE', 'ANONYMOUS')
