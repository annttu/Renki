#!/usr/bin/env python
# encoding: utf-8

"""
Some tests for domain routes etc.
"""

from lib import test_base as base

import unittest


class BaseDomainRouteTests(base.SimpleRouteTest):
    FLUSH_TABLES = True
    def test_domains_get_anonymous(self):
        #do_test(self, routine, method, args, user, response, status):
        self.do_test(route='/domains', method='GET', args={},
                     user=base.UserLevels.ANONYMOUS, response=None,
                     status=base.APIResponses.NOAUTH)
        self.do_test(route='/domains/', method='GET', args={},
                     user=base.UserLevels.ANONYMOUS, response=None,
                     status=base.APIResponses.NOAUTH)

    def test_domains_get_user(self):
        schema = {
            'type': 'object',
            'properties': {
                "status": {'type': 'string'},
                "domains": {
                    "type": "array",
                    "minItems": 0
                    }
                },
            "additionalProperties": False,
            "required": ["status", "domains"]
        }
        self.do_test(route='/domains', method='GET', args={},
                     user=base.UserLevels.USER, response=schema,
                     status=base.APIResponses.OK)
        self.do_test(route='/domains/', method='GET', args={},
                     user=base.UserLevels.USER, response=schema,
                     status=base.APIResponses.OK)

    def test_domains_get_admin(self):
        schema = {
            'type': 'object',
            'properties': {
                "status": {'type': 'string'},
                "domains": {
                    "type": "array",
                    "minItems": 0
                    }
                },
            "additionalProperties": False,
            "required": ["status", "domains"]
        }
        self.do_test(route='/domains', method='GET', args={},
                     user=base.UserLevels.ADMIN, response=schema,
                     status=base.APIResponses.OK)
        self.do_test(route='/domains/', method='GET', args={},
                     user=base.UserLevels.ADMIN, response=schema,
                     status=base.APIResponses.OK)

    def test_domains_put_anonymous(self):
        self.do_test(route='/domains', method='PUT', args={},
                     user=base.UserLevels.ANONYMOUS, response=None,
                     status=base.APIResponses.NOAUTH)

    def test_domains_put_user(self):
        args = {'name': 'example.com'}
        schema = {
            'type': 'object',
            'properties': {
                "status": {'type': 'string'},
                "name": {
                    "type": "string",
                    "enum" : ["example.com"]
                    },
                "id": {
                    "type": "number",
                    "enum": [1]
                    },
                "user_id": {
                    "type": "number",
                    "enum": [2]
                    }
                },
            "additionalProperties": False,
            "required": ["status", "name", "id", "user_id"]
        }
        self.do_test(route='/domains', method='PUT', args=args,
                     user=base.UserLevels.USER, response=schema,
                     status=base.APIResponses.OK)

    def test_domains_put_admin_other(self):
        args = {'name': 'example.com', 'user_id': 1}
        schema = {
            'type': 'object',
            'properties': {
                "status": {'type': 'string'},
                "name": {
                    "type": "string",
                    "enum" : ["example.com"]
                    },
                "id": {'type': "number",
                    "enum": [1]
                    },
                "user_id": {'type': "number",
                    "enum": [1]
                    }
                },
            "additionalProperties": False,
            "required": ["status", "name", "id", "user_id"]
        }
        self.do_test(route='/domains', method='PUT', args=args,
                     user=base.UserLevels.ADMIN, response=schema,
                     status=base.APIResponses.OK)

    def test_domains_put_admin(self):
        args = {'name': 'example.com', 'user_id': 2}
        schema = {
            'type': 'object',
            'properties': {
                "status": {'type': 'string'},
                "name": {
                    "type": "string",
                    "enum" : ["example.com"]
                    },
                "id": {'type': "number",
                    "enum": [1]
                    },
                "user_id": {'type': "number",
                    "enum": [2]
                    }
                },
            "additionalProperties": False,
            "required": ["status", "name", "id", "user_id"]
        }
        self.do_test(route='/domains', method='PUT', args=args,
                     user=base.UserLevels.ADMIN, response=schema,
                     status=base.APIResponses.OK)

    def test_domains_post(self):
        """
        POST is not allowed method
        """
        self.do_test(route='/domains', method='POST', args={},
                     user=base.UserLevels.ADMIN, response=None,
                     status=base.APIResponses.NOTALLOWED)
        self.do_test(route='/domains', method='POST', args={},
                     user=base.UserLevels.USER, response=None,
                     status=base.APIResponses.NOTALLOWED)
        self.do_test(route='/domains', method='POST', args={},
                     user=base.UserLevels.ANONYMOUS, response=None,
                     status=base.APIResponses.NOTALLOWED)

if __name__ == '__main__':
    unittest.main()
