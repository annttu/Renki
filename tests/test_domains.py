#!/usr/bin/env python
# encoding: utf-8
import unittest
from services.tests.dummy.dummy_services import *
from services.libs.domain import Domain


class TestDomain(unittest.TestCase):

    def assertInvalidValue(self, dest, key, value):
        failed = False
        try:
            setattr(dest, key, value)
        except ValueError:
            failed = True
            pass
        self.assertTrue(failed, "Domain should not accept %s value %s" % (key, value))

    def assertValidValue(self, dest, key, value):
        failed = False
        try:
            setattr(dest, key, value)
        except ValueError as e:
            #print("%s: %s" % (e.__class__, e))
            failed = True
            pass
        self.assertFalse(failed, "Domain should accept %s value %s" % (key, value))

    def setUp(self):
        self.srv = DummyServices(username='unittest', password='', server='localhost',
                                 database='services')
        self.srv.login()
        self.domain = Domain(self.srv)

    def test_domain_ttl(self):
        self.assertValidValue(self.domain, "ttl", 1)
        self.assertValidValue(self.domain, "ttl", 20)
        self.assertInvalidValue(self.domain, "ttl", 0)
        self.assertInvalidValue(self.domain, "ttl", -1)
        self.assertInvalidValue(self.domain, "ttl", 1000000)

    def test_domain_refresh_time(self):
        self.assertValidValue(self.domain, "refresh_time", 1)
        self.assertValidValue(self.domain, "refresh_time", 20)
        self.assertInvalidValue(self.domain, "refresh_time", 0)
        self.assertInvalidValue(self.domain, "refresh_time", -1)
        self.assertInvalidValue(self.domain, "refresh_time", 1000000)

    def test_domain_retry_time(self):
        self.assertValidValue(self.domain, "retry_time", 1)
        self.assertValidValue(self.domain, "retry_time", 20)
        self.assertInvalidValue(self.domain, "retry_time", 0)
        self.assertInvalidValue(self.domain, "retry_time", -1)
        self.assertInvalidValue(self.domain, "retry_time", 1000000)

    def test_domain_expire_time(self):
        self.assertValidValue(self.domain, "expire_time", 1)
        self.assertValidValue(self.domain, "expire_time", 20)
        self.assertInvalidValue(self.domain, "expire_time", 0)
        self.assertInvalidValue(self.domain, "expire_time", -1)
        self.assertInvalidValue(self.domain, "expire_time", 1000000)

    def test_domain_minimum_cache_time(self):
        self.assertValidValue(self.domain, "minimum_cache_time", 1)
        self.assertValidValue(self.domain, "minimum_cache_time", 20)
        self.assertInvalidValue(self.domain, "minimum_cache_time", 0)
        self.assertInvalidValue(self.domain, "minimum_cache_time", -1)
        self.assertInvalidValue(self.domain, "minimum_cache_time", 1000000)

    def test_admin_address(self):
        self.assertValidValue(self.domain, "admin_address", "user@kapsi.fi")
        self.assertInvalidValue(self.domain, "admin_address", "user.kapsi.fi")

    def test_masters(self):
        self.assertValidValue(self.domain, "masters", 
                             ['ns1.kapsi.fi', 'ns2.kapsi.fi'])
        self.assertValidValue(self.domain, "masters", ['1.2.3.4', '3.2.1.0'])
        self.assertInvalidValue(self.domain, "masters", ['1.2'])
        self.assertInvalidValue(self.domain, "masters", ['localhost'])

    def test_allow_transfer(self):
        self.assertValidValue(self.domain, "allow_transfer", 
                             ['ns1.kapsi.fi', 'ns2.kapsi.fi'])
        self.assertValidValue(self.domain, "allow_transfer", ['1.2.3.4', '3.2.1.0'])
        self.assertInvalidValue(self.domain, "allow_transfer", ['1.2'])
        self.assertInvalidValue(self.domain, "allow_transfer", ['localhost'])

if __name__ == '__main__':
    unittest.main()
