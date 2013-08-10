#!/usr/bin/env python
# encoding: utf-8

from webtest import TestApp, AppError
import unittest
from lib import renki, utils
# Register routes
import routes


class TestRoutes(unittest.TestCase):
    def setUp(self):
        renki.app.catchall = False
        self.app = TestApp(renki.app)
        self.key = None

    def getKey(self):
        r = self.app.post_json('/login',
                               {'username': 'test', 'password': 'test'})
        if 'key' in r.json:
            self.key = r.json['key']
        self.assertTrue(self.key is not None, "Api key request failed")
        item = self.get('/login/valid')
        self.assertOK(item)

    def get(self, url, params={}):
        if self.key:
            params['key'] = self.key
        return self.app.get(url, params=params, status="*")

    def post(self, url, data={}):
        if self.key:
            data['key'] = self.key
        return self.app.post_json(url, data, status="*")

    def put(self, url, data={}):
        if self.key:
            data['key'] = self.key
        return self.app.put_json(url, data, status="*")

    def delete(self, url, params={}):
        if self.key:
            params['key'] = self.key
        return self.app.delete(url, params=params, status="*")

    def assertValidJSON(self, item):
        self.assertTrue(item.content_type == 'application/json',
                        "Content type not JSON")
        self.assertTrue('status' in item.json, 'status is mandatory argument')

    def assertStatus(self, item, status=utils.OK_STATUS):
        self.assertTrue(item.json['status'] in utils.STATUS_CODES,
                        "Invalid status code %s" % item.json['status'])

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

    def assertOK(self, item):
        self.assertEqual(item.status_int, 200,
                          "Status code is not 200")

    def assertAuthFailed(self, item):
        self.assertEqual(item.status_int, 401,
                        "Authentication error not given")

    def assertAuthSuccess(self, item):
        self.assertEqual(item.status_int, 200,
                        "Authentication error given")
