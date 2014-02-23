#!/usr/bin/env python
# encoding: utf-8

"""
This file is part of Renki project

Base utils for testing
"""

from lib import check_settings
from lib import renki, utils, renki_settings as settings

from lib.auth import db as auth_db, permissions
from lib.enums import JSON_STATUS

import routes
import modules

from lib.database import connection

from webtest import TestApp, AppError
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JSONValidationError
import json

import time

import unittest
import logging
import logging.config


logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# Initialize database connection
check_settings.set_settings()

logger.setLevel(logging.DEBUG)
connection.initialize_connection(unittest=True)

# TODO:
# - Mute logging

logging.config.dictConfig({'version': 1,
    'disable_existing_loggers': True})
settings.DEBUG = True

### JSON validation ###

class JSONValidatorObject(object):
    TYPE = 'invalidtype'
    def __init__(self, name, required=True, enum=None):
        self.name = name
        self.required = required
        self.enum = enum

    def args(self):
        return {}

    def as_property(self):
        d = {
                'type': self.TYPE
        }
        for k, v in self.args().items():
            d[k] = v
        if self.enum:
            d['enum'] = self.enum
        return d

    def as_required(self):
        if self.required:
            return [self.name]
        return []


class JSONString(JSONValidatorObject):
    TYPE = 'string'

class JSONArray(JSONValidatorObject):
    TYPE = 'array'
    def __init__(self, *args, minItems=0, maxItems=None, **kwargs):
        super(JSONArray, self).__init__(*args, **kwargs)
        self.minItems = minItems
        self.maxItems = maxItems

    def args(self):
        d = {'minItems': self.minItems}
        if self.maxItems is not None:
            d['maxItems'] = self.maxItems
        return d

class JSONNumber(JSONValidatorObject):
    TYPE = 'number'
    def __init__(self, *args, minimum=None, maximum=None, **kwargs):
        super(JSONNumber, self).__init__(*args, **kwargs)
        self.minimum = minimum
        self.maximum = maximum

    def args(self):
        d = {}
        if self.minimum:
            d['minimum'] = self.minimum
        if self.maximum is not None:
            d['maximum'] = self.maximum
        return d

class JSONBoolean(JSONValidatorObject):
    TYPE = 'boolean'

#######################
# Response validation #
#######################

class ResponseStatus(object):
    HTTP_STATUS = None
    JSON_STATUS = None
    FIELDS = [JSONString('error', required=True),
              JSONString('status', required=True, enum=['ERROR']),
              JSONString('info', required=False)]

class STATUS_OK(ResponseStatus):
    HTTP_STATUS = 200
    JSON_STATUS = JSON_STATUS.OK
    FIELDS = [JSONString('status', required=True, enum=['OK'])]

class STATUS_ERROR(ResponseStatus):
    HTTP_STATUS = 400
    JSON_STATUS = JSON_STATUS.ERROR

class STATUS_DENIED(ResponseStatus):
    HTTP_STATUS = 403
    JSON_STATUS = JSON_STATUS.DENIED

class STATUS_NOTALLOWED(ResponseStatus):
    HTTP_STATUS = 405
    JSON_STATUS = JSON_STATUS.NOTALLOWED

class STATUS_NOAUTH(ResponseStatus):
    HTTP_STATUS = 401
    JSON_STATUS = JSON_STATUS.NOAUTH

class STATUS_CONFLICT(ResponseStatus):
    HTTP_STATUS = 409
    JSON_STATUS = JSON_STATUS.CONFLICT

class STATUS_NOTFOUND(ResponseStatus):
    HTTP_STATUS = 404
    JSON_STATUS = JSON_STATUS.NOTFOUND

class TestUser(object):
    def __init__(self, name, password, sessionkey, user):
        self.name = name
        self.sessionkey = sessionkey
        self.password = password
        self.user = user

class BasicTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        renki.app.catchall = False

    def setUp(self):
        """
        Initialize database and create tables, relations, indexes etc.
        """
        connection.session.rollback()
        self.app = TestApp(renki.app)
        connection.conn.create_tables()
        connection.session.commit()
        self._users = {}
        # Create permissions
        for permission in permissions.PERMISSIONS:
            if not auth_db.Permissions.query().filter(
                    auth_db.Permissions.name == permission).all():
                p = auth_db.Permissions()
                p.name = permission
                p.save()

    def tearDown(self):
        """
        Destroy tables, indexes and relations.
        """
        try:
            connection.session.rollback()
            connection.conn.drop_tables()
            connection.session.commit()
            connection.session.flush()
            connection.session.session().close()
        except:
            connection.session.rollback()
            raise

    def _get_error(self, item):
        error = None
        try:
            if 'error' in item.json:
                error = item.json['error']
        except (AttributeError, KeyError):
            pass
        return error


    def auth(self, user, password):
        """
        Authenticate user and return authentiction key
        """
        args = {'username': user, 'password': password}
        s = self.app.post('/login', params=args, status="*")
        self.assertStatus(s, STATUS_OK)
        return s.json['apikey']

    def user(self, name, perms=[]):
        """
        Create user with name `name` and permissions `permissins`
        return authenticated session
        """
        if name not in self._users:
            pw = utils.generate_key()
            user = auth_db.Users()
            user.id = len(self._users) + 1
            user.name = name
            user.set_password(pw)
            user.firstnames = 'test'
            user.lastname = 'test'
            user.save()
            connection.session.commit()
            for perm_name in perms:
                perm = auth_db.Permissions.query().filter(
                            auth_db.Permissions.name==perm_name).one()
                user.permissions.append(perm)
            connection.session.commit()
            sessionkey = self.auth(user=name, password=pw)
            u = TestUser(name=name, password=pw, sessionkey=sessionkey, user=user)
            self._users[name] = u
        return self._users[name]


    def q(self, route, user, method='GET', args={}):
        """
        Query route using `method` with args `args` as `user`
        returns response object
        """
        if user:
            args['apikey'] = user.sessionkey
        elif 'apikey' in args:
            del args['apikey']
        if method.upper() == 'GET':
            return self.app.get(route, params=args, status="*")
        elif method.upper() == 'POST':
            return self.app.post_json(route, params=args, status="*")
        elif method.upper() == 'PUT':
            return self.app.put_json(route, params=args, status="*")
        elif method.upper() == 'DELETE':
            if 'apikey' in args:
                route = "%s?apikey=%s" % (route, args['apikey'])
            return self.app.delete(route, params=args, status="*")
        self.fail("Method %s not implemented" % method)

    def assertContainsOne(self, database, cls = None):
        query = database.query()
        if cls is not None:
            query = query.filter(cls)
        self.assertEqual(query.count(), 1)

    def assertContainsMany(self, database, cls = None):
        query = database.query()
        if cls is not None:
            query = query.filter(cls)
        self.assertTrue(query.count() > 1)

    def assertContainsNone(self, database, cls = None):
        query = database.query()
        if cls is not None:
            query = query.filter(cls)
        self.assertEqual(query.count(), 0)

    def assertStatus(self, response, status):
        """
        Assert that response status is `status`
        """
        self.assertEqual(response.json['status'], status.JSON_STATUS,
            "Wrong JSON status code %s, excepted %s, error: %s" % (
            response.json['status'], status.JSON_STATUS,
            self._get_error(response)))
        self.assertEqual(response.status_int, status.HTTP_STATUS,
            "Wrong HTTP status code %s, excepted %s" %
                (response.status_int, status.HTTP_STATUS))

    def assertValidResponse(self, item, schema=[]):
        """
        Validates that response is valid json response
        @param schema: optional json schema.
        """
        if not schema:
            schema = []
        else:
            # Copy schema
            schema = [i for i in schema]
        schema.append(JSONString('status', required=True))
        d = {
            'type': 'object',
            'properties': {},
            "additionalProperties": False,
            "required": []
        }
        for i in schema:
            d['properties'][i.name] = i.as_property()
            for req in i.as_required():
                if req not in d["required"]:
                    d["required"].append(req)
        try:
            jsonschema_validate(item.json, schema=d)
        except JSONValidationError:
            self.fail("Response JSON is not valid")

    def assertQ(self, route, user, method='GET', args={}, status=None,
                schema=None):
        """
        Sortcut to execute query and validate status and response schema.
        """
        args = args.copy()
        if not schema and status and status != STATUS_OK:
            schema = status.FIELDS
        elif status and status != STATUS_OK:
            schema += status.FIELDS
        q = self.q(route=route, user=user, method=method, args=args)
        if status is not None:
            self.assertStatus(q, status)
        if schema:
            self.assertValidResponse(q, schema=schema)


