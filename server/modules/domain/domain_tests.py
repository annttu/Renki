#!/usr/bin/env python
# encoding: utf-8

"""
Some tests for domain routes.
"""

from lib import test_utils as tu

domain_schema =  [
    tu.JSONString('name', required=True, enum=['example.com']),
    tu.JSONString('comment', required=True, enum=['foo bar']),
    tu.JSONNumber('user_id', required=True, enum=[1]),
    tu.JSONNumber('id', required=True, enum=[1]),
    tu.JSONBoolean('waiting', required=True, enum=[False]),
    tu.JSONString('timestamp', required=True)
]

class TestDomainsRoutine(tu.BasicTest):
    def test_domains_get_user_anon(self):
        """
        Test as not authenticated user
        """
        self.assertQ('/domains', user=None, status=tu.STATUS_NOAUTH)
        self.assertQ('/domains/', user=None, status=tu.STATUS_NOAUTH)

    def test_domains_get_user_no_perm(self):
        """
        Test as authenticated user without sufficient permissions
        """
        u = self.user('test', [])
        self.assertQ('/domains', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/domains/', user=u, status=tu.STATUS_DENIED)

    def test_domains_get_user(self):
        """
        Test as authenticated user with sufficient permissions
        """
        u = self.user('test', ['domains_view_own'])
        schema = [
            tu.JSONArray('domains', minItems=0, maxItems=0, required=True),
        ]
        self.assertQ('/domains', user=u, status=tu.STATUS_OK, schema=schema)
        self.assertQ('/domains/', user=u, status=tu.STATUS_OK, schema=schema)

    def test_domains_post_user(self):
        """
        Test POST /domains as user with sufficient rights
        """
        u = self.user('test', ['domains_modify_own'])
        args = {'name': 'example.com', 'comment': 'foo bar'}
        self.assertQ('/domains', user=u, method='POST', status=tu.STATUS_OK,
                     schema=domain_schema, args=args)
        args['name'] = 'example2.com'
        domain_schema_2 = [i for i in domain_schema if i.name not in ['name', 'id']]
        domain_schema_2.append(tu.JSONString('name', required=True, enum=['example2.com']))
        domain_schema_2.append(tu.JSONNumber('id', required=True, enum=[2]))
        self.assertQ('/domains/', user=u, method='POST', status=tu.STATUS_OK,
                     schema=domain_schema_2, args=args)

    def test_domains_post_user_wrong_userid(self):
        """
        Test POST /domains as user with sufficient rights
        """
        u = self.user('test', ['domains_modify_own'])
        args = {'name': 'example.com', 'comment': 'foo bar', 'user_id': 2}
        self.assertQ('/domains', user=u, method='POST',
                     status=tu.STATUS_OK, args=args, schema=domain_schema)

    def test_domains_post_user_noperm(self):
        """
        Test POST /domains as user without sufficient rights
        """
        u = self.user('test', [])
        args = {'name': 'example.com', 'comment': 'foo bar'}
        self.assertQ('/domains', user=u, method='POST',
                     status=tu.STATUS_DENIED, args=args)
        self.assertQ('/domains/', user=u, method='POST',
                     status=tu.STATUS_DENIED, args=args)

    def test_domains_post_user_anon(self):
        """
        Test POST /domains as anonumous
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        self.assertQ('/domains', user=None, method='POST',
                     status=tu.STATUS_NOAUTH, args=args)
        self.assertQ('/domains/', user=None, method='POST',
                     status=tu.STATUS_NOAUTH, args=args)

    def test_domains_get_domain_user(self):
        """
        Test GET /domains/<domain_id>/ as user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/domains/1', user=u, method='GET',
                     args=args, status=tu.STATUS_OK,
                     schema=domain_schema)

    def test_domains_get_domain_user_noper(self):
        """
        Test GET /domains/<domain_id>/ as user without proper permissions
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/domains/1', user=u, method='GET',
                     status=tu.STATUS_DENIED)

    def test_domains_get_domain_user_anon(self):
        """
        Test GET /domains/<domain_id>/ as anonymous user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/domains/1', user=None, method='GET',
                     status=tu.STATUS_NOAUTH)

    def test_domains_get_domain_user_notown(self):
        """
        Test GET /domains/<domain_id>/ as anonymous user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        u2 = self.user('test2', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains/1', user=u2, method='GET',
                     status=tu.STATUS_NOTFOUND)

    def test_domains_get_domain_admin(self):
        """
        Test GET /<user_id>/domains/<domain_id>/ as admin
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        a = self.user('admin', ['domains_modify_all', 'domains_view_all'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/1/domains/1', user=a, method='GET',
                     status=tu.STATUS_OK, schema=domain_schema)

    def test_domains_get_domain_admin_noperm(self):
        """
        Test GET /<user_id>/domains/<domain_id>/ as admin
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        a = self.user('admin', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/1/domains/1', user=a, method='GET',
                     status=tu.STATUS_DENIED)

    def test_domains_delete_domain_user(self):
        """
        Test DELETE /domains/<domain_id>/ as user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/domains/1', user=u, method='DELETE',
                     status=tu.STATUS_OK)
        # Ensure list is empty
        schema = [
            tu.JSONArray('domains', minItems=0, maxItems=0, required=True),
        ]
        self.assertQ('/domains', user=u, status=tu.STATUS_OK, schema=schema)

    def test_domains_delete_domain_user_notown(self):
        """
        Test DELETE /domains/<domain_id>/ as user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        u2 = self.user('test2', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains/1', user=u2, method='DELETE',
                     status=tu.STATUS_NOTFOUND)
        # Ensure list is not empty
        schema = [
            tu.JSONArray('domains', minItems=1, maxItems=1, required=True),
        ]
        self.assertQ('/domains', user=u, status=tu.STATUS_OK, schema=schema)

    def test_domains_delete_domain_user_anon(self):
        """
        Test DELETE /domains/<domain_id>/ as user
        """
        args = {'name': 'example.com', 'comment': 'foo bar'}
        u = self.user('test', ['domains_modify_own', 'domains_view_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args=args, status=tu.STATUS_OK)
        self.assertQ('/domains/1', user=None, method='DELETE',
                     status=tu.STATUS_NOAUTH)


if __name__ == "__main__":
    import unittest
    unittest.main()

