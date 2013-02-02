#!/usr/bin/env python
# encoding: utf-8
import unittest
from services.tests.dummy.dummy_services import *
from services.libs.domain import Domain


class TestDomain(unittest.TestCase):
    """
    Test services.libs.domains.Domain object functionality
    """

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
        self.assertEqual(self.domain.ttl, 20, 
                        "Domain.ttl setter didn't set anything")
        self.assertInvalidValue(self.domain, "ttl", 0)
        self.assertInvalidValue(self.domain, "ttl", -1)
        self.assertInvalidValue(self.domain, "ttl", 1000000)

    def test_domain_refresh_time(self):
        self.assertValidValue(self.domain, "refresh_time", 1)
        self.assertValidValue(self.domain, "refresh_time", 21)
        self.assertEqual(self.domain.refresh_time, 21,
                   "Domain.refresh_time setter didn't set anything")
        self.assertInvalidValue(self.domain, "refresh_time", 0)
        self.assertInvalidValue(self.domain, "refresh_time", -1)
        self.assertInvalidValue(self.domain, "refresh_time", 1000000)

    def test_domain_retry_time(self):
        self.assertValidValue(self.domain, "retry_time", 1)
        self.assertValidValue(self.domain, "retry_time", 22)
        self.assertEqual(self.domain.retry_time, 22,
                   "Domain.retry_time setter didn't set anything")
        self.assertInvalidValue(self.domain, "retry_time", 0)
        self.assertInvalidValue(self.domain, "retry_time", -1)
        self.assertInvalidValue(self.domain, "retry_time", 1000000)

    def test_domain_expire_time(self):
        self.assertValidValue(self.domain, "expire_time", 1)
        self.assertValidValue(self.domain, "expire_time", 23)
        self.assertEqual(self.domain.expire_time, 23,
                   "Domain.expire_time setter didn't set anything")
        self.assertInvalidValue(self.domain, "expire_time", 0)
        self.assertInvalidValue(self.domain, "expire_time", -1)
        self.assertInvalidValue(self.domain, "expire_time", 1000000)

    def test_domain_minimum_cache_time(self):
        self.assertValidValue(self.domain, "minimum_cache_time", 1)
        self.assertValidValue(self.domain, "minimum_cache_time", 24)
        self.assertEqual(self.domain.minimum_cache_time, 24,
                         "Domain.minimum_cache_time setter did't set anything")
        self.assertInvalidValue(self.domain, "minimum_cache_time", 0)
        self.assertInvalidValue(self.domain, "minimum_cache_time", -1)
        self.assertInvalidValue(self.domain, "minimum_cache_time", 1000000)

    def test_admin_address(self):
        self.assertValidValue(self.domain, "admin_address", "user@kapsi.fi")
        self.assertInvalidValue(self.domain, "admin_address", "user.kapsi.fi")
        self.assertEqual(self.domain.admin_address, "user@kapsi.fi",
                         "Domain.admin_address setter did't set anything")

    def test_masters(self):
        self.assertValidValue(self.domain, "masters", 
                             ['ns1.kapsi.fi', 'ns2.kapsi.fi'])
        self.assertValidValue(self.domain, "masters", ['1.2.3.4', '3.2.1.0'])
        self.assertEqual(self.domain.masters, ['1.2.3.4', '3.2.1.0'],
                         "Domain.masters setter did't set anything")
        self.assertInvalidValue(self.domain, "masters", ['1.2'])
        self.assertInvalidValue(self.domain, "masters", ['localhost'])

    def test_allow_transfer(self):
        self.assertValidValue(self.domain, "allow_transfer",
                             ['ns1.kapsi.fi', 'ns2.kapsi.fi'])
        self.assertValidValue(self.domain, "allow_transfer",
                                                         ['1.2.3.4', '3.2.1.0'])
        self.assertInvalidValue(self.domain, "allow_transfer", ['1.2'])
        self.assertInvalidValue(self.domain, "allow_transfer", ['localhost'])
        self.assertEqual(self.domain.allow_transfer, ['1.2.3.4', '3.2.1.0'],
                         "Domain.allow_transfer setter did't set anything")

    def test_name(self):
        self.assertValidValue(self.domain, "name", u"kapsi.fi")
        self.assertValidValue(self.domain, "name", u"long.and.dotty.domain.tld")
        self.assertValidValue(self.domain, "name", u"päälikkö.fi")
        self.assertValidValue(self.domain, "name", u"xn--plikk-graa2m.fi")
        self.assertValidValue(self.domain, "name", u"slash-domain.tld")
        self.assertInvalidValue(self.domain, "name", u"underscore_domain.com")
        self.assertInvalidValue(self.domain, "name", u"-invalid.com")
        self.assertInvalidValue(self.domain, "name", u"domain")
        self.assertInvalidValue(self.domain, "name", u"a.fi")
        self.assertInvalidValue(self.domain, "name", u"a..fi")
        self.assertInvalidValue(self.domain, "name", u"t.o.o.d.o.t.t.y.tld")


    def test_shared(self):
        self.assertValidValue(self.domain, "shared", True)
        self.assertValidValue(self.domain, "shared", False)
        self.assertInvalidValue(self.domain, "shared", "asdf")

    # @TODO: test commit and delete commands

class TestDomains(unittest.TestCase):
    """
    Test services.libs.domains.Domains object functionality
    """

    def setUp(self):
        self.srv = DummyServices(username='unittest', password='',
                                 server='localhost', database='services')
        self.srv.login()

    def test_creating(self):
        domain = self.srv.domains.add("kapsi.fi", shared=True, dns=True,
                                      domain_type="Master")
        self.assertEqual(domain.__class__, Domain, "domains.add should return" +
                                                    "Domain object")
        self.assertEqual(domain.admin_address,
                         self.srv.defaults.hostmaster_address, 
                         "domain hostmaster_address should be default")
        
if __name__ == '__main__':
    unittest.main()
