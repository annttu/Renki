#!/usr/bin/env python
# encoding: utf-8

from test_setup import ServicesTestCase
from services.libs.domain import Domain

import unittest

class TestDomain(ServicesTestCase):
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

    def assertCommitSuccess(self):
        with self.assertRaises(Exception, "Commit should not fail"):
            self.vhost.commit()

    def assertCommitNotSuccess(self):
        self.assertRaises(self.vhost.commit(), "Commit should not success")

    def local_setup(self):
        self.domain = self.srv.domains.add("kapsi.fi")
        self.domain.dns = True
        self.domain.commit()
        self.vhost = self.domain.add_vhost()

    def test_vhost_add(self):
        """
        Test vhost creation
        """
        self.vhost.aliases = ['www', 'other']
        self.vhost.name = ''
        self.vhost.redirect_to = None
        # Should select proper server automatically
        self.vhost.server = None
        with self.assertRaises(Exception, "Vhost adding failed"):
            self.vhost.commit()

    def test_vhost_delete(self):
        """
        Test vhost deleting
        """
        self.test_vhost_add(self)
        try:
            self.vhost.delete()
        except:
            self.assertFalse(True, "Vhost delete should success")

    def test_vhost_name(self):
        self.assertInvalidValue(self.vhost, 'name', '.asdf')
        self.assertInvalidValue(self.vhost, 'name', '.')
        self.assertInvalidValue(self.vhost, 'name', 'asdf.')
        self.assertValidValue(self.vhost, 'name', '')
        self.assertValidValue(self.vhost, 'name', 'www')
        self.assertValidValue(self.vhost, 'name', 'www.www')

    def test_logaccess_add(self):
        """
        Test logaccess creation and delete
        """
        self.assertValidValue(self.vhost, 'locaccess', 's')
        self.assertValidValue(self.vhost, 'logaccess', False)
        self.assertValidValue(self.vhost, 'logaccess', True)


    def test_vhost_server_selecting(self):
        """
        Test vhost select server
        """
        pass

    # @TODO: test commit and delete commands

class TestDomains(ServicesTestCase):
    """
    Test services.libs.domains.Domains object functionality
    """

    def test_creating(self):
        domain = self.srv.domains.add("kapsi.fi", shared=True, dns=True,
                                      domain_type="Master")
        self.assertEqual(domain.__class__, Domain, "domains.add should return" +
                                                    "Domain object")
        self.assertEqual(domain.admin_address,
                         self.srv.defaults.hostmaster_address, 
                         "domain hostmaster_address should be default")
        self.assertTrue(domain.delete(), "Domain deleting should success")

if __name__ == '__main__':
    unittest.main()
