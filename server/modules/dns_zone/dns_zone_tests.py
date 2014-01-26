#!/usr/bin/env python
# encoding: utf-8

"""
Some tests for DNS zone routes.
"""

from lib import test_utils as tu

"""
{'comment': '',
 'status': 'OK',
 'rname': 'root.renkidev.kapsi.fi',
 'retry': 7200,
 'record_ttl': 3600,
 'timestamp': '2014-01-06 16:57:15.563984',
 'refresh': 10800,
 'id': 1,
 'waiting': False,
 'expire': 1209600,
 'ttl': 2600,
 'domain_id': 5}
"""
def dns_zone_schema(domain_id=1):
    return [
    tu.JSONString('comment', required=True, enum=['foo bar']),
    tu.JSONBoolean('waiting', required=True, enum=[False]),
    tu.JSONNumber('id', required=True, enum=[1]),
    tu.JSONString('timestamp', required=True),
    tu.JSONString('rname', required=True, enum=['root.example.com']),
    tu.JSONNumber('domain_id', required=True, enum=[domain_id]),
    tu.JSONNumber('record_ttl', required=True, enum=[123]),
    tu.JSONNumber('refresh', required=True, enum=[1234]),
    tu.JSONNumber('expire', required=True, enum=[12345]),
    tu.JSONNumber('ttl', required=True, enum=[123456]),
    tu.JSONNumber('retry', required=True, enum=[123457])
]

class TestDNSZoneRoutine(tu.BasicTest):
    def test_dns_zone_get_user_anon(self):
        """
        Test as not authenticated user
        """
        u = self.user('test', ['dns_zone_modify_own', 'domains_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, args={})
        self.assertQ('/domains/1/dns', user=None, status=tu.STATUS_NOAUTH)
        self.assertQ('/domains/1/dns/', user=None, status=tu.STATUS_NOAUTH)

    def test_dns_zone_get_user_no_perm(self):
        """
        Test as authenticated user without sufficient permissions
        """
        u = self.user('test', ['dns_zone_modify_own', 'domains_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, args={'comment': 'foo bar'})
        u = self.user('test', [])
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/domains/1/dns/', user=u, status=tu.STATUS_DENIED)

    def test_dns_zone_add_user(self):
        """
        Test as authenticated user with sufficient permissions
        """
        u = self.user('test', ['dns_zone_view_own', 'domains_modify_own',
                               'dns_zone_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, schema=dns_zone_schema(),
                     args={'comment': 'foo bar', 'rname': 'root.example.com',
                           'record_ttl': 123,
                           'refresh': 1234,
                           'expire': 12345,
                           'ttl': 123456,
                           'retry': 123457})
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_OK,
                     schema=dns_zone_schema())
        self.assertQ('/domains/1/dns/', user=u, status=tu.STATUS_OK,
                     schema=dns_zone_schema())

    def test_dns_zone_get_other_user(self):
        u = self.user('test', ['dns_zone_view_own', 'domains_modify_own',
                               'dns_zone_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, schema=dns_zone_schema(),
                     args={'comment': 'foo bar', 'rname': 'root.example.com',
                           'record_ttl': 123,
                           'refresh': 1234,
                           'expire': 12345,
                           'ttl': 123456,
                           'retry': 123457})
        u2 = self.user('test2', ['dns_zone_view_own', 'domains_view_own'])
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u2, status=tu.STATUS_NOTFOUND)
        self.assertQ('/domains/1/dns/', user=u2, status=tu.STATUS_NOTFOUND)

    def test_dns_zone_delete_user(self):
        u = self.user('test', ['dns_zone_view_own', 'domains_modify_own',
                               'dns_zone_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, schema=dns_zone_schema(),
                     args={'comment': 'foo bar', 'rname': 'root.example.com',
                           'record_ttl': 123,
                           'refresh': 1234,
                           'expire': 12345,
                           'ttl': 123456,
                           'retry': 123457})
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', method='DELETE', user=u,
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_NOTFOUND)

def dns_record_schema(priority=None, key=None, ttl=3600, type='A'):
    return [
        tu.JSONString('comment', required=True, enum=['foo bar']),
        tu.JSONBoolean('waiting', required=True, enum=[False]),
        tu.JSONNumber('id', required=True, enum=[1]),
        tu.JSONString('timestamp', required=True),
        tu.JSONString('value', required=True),
        tu.JSONNumber('dns_zone_id', required=True, enum=[1]),
        tu.JSONString('piority', required=True, enum=[priority]),
        tu.JSONString('key', required=True, enum=[key]),
        tu.JSONNumber('ttl', required=True, enum=[ttl]),
        tu.JSONString('type', required=True, enum=[type]),

    ]

class TestDNSRecordRoutine(tu.BasicTest):
    def create_user_domain_dns(self):
        u = self.user('test', ['dns_zone_view_own', 'domains_modify_own',
                               'dns_zone_modify_own'])
        self.assertQ('/domains', user=u, method='POST',
                     args={'name': 'example.com', 'comment': 'foo bar'},
                     status=tu.STATUS_OK)
        self.assertQ('/domains/1/dns', user=u, method='PUT',
                     status=tu.STATUS_OK, schema=dns_zone_schema(),
                     args={'comment': 'foo bar', 'rname': 'root.example.com',
                           'record_ttl': 123,
                           'refresh': 1234,
                           'expire': 12345,
                           'ttl': 123456,
                           'retry': 123457})
        self.assertQ('/domains/1/dns', user=u, status=tu.STATUS_OK)
        return u

    def test_dns_record_get_anon(self):
        u = self.create_user_domain_dns()
        records_schema = [tu.JSONArray('records', minItems=0, maxItems=0)]
        self.assertQ('/domains/1/dns/records', user=u, status=tu.STATUS_OK,
                     schema=records_schema)

if __name__ == "__main__":
    import unittest
    unittest.main()

