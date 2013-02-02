#!/usr/bin/env python
# encoding: utf-8
"""
domain.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012 - 2013
"""

from services.exceptions import *
import logging
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import mapper

from services.libs.tools import is_int, is_bool, valid_fqdn, valid_ipv4_address, \
                                valid_ipv6_address, idna_domain

from lepl.apps.rfc3696 import Email

valid_email = Email()

class Domains(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.domain')


    def list(self):
        """List user all domains"""
        try:
            res = self.main.session.query(self.main.Domains)
            if self.main.customer_id:
                res = res.filter(self.main.Domains.t_customers_id==self.main.customer_id)
            else:
                self.main.require_admin()
            res = res.all()
            self.main.session.commit()
            return res
        except DatabaseError as e:
            raise RuntimeError(e)

    def get(self, name=None, domain_id=None,getall=False):
        """Get user domain matching name"""
        if not name and not domain_id:
            raise RuntimeError('Give either name or domain_id')
        if name:
            name = name.split('.')
            domain = ''
            while len(name) > 0:
                if len(domain) > 0:
                    domain = "%s.%s" % (name.pop(), domain)
                else:
                    domain = name.pop()
                search = self.main.session.query(self.main.Domains).filter(self.main.Domains.name == domain)
                if self.main.customer_id and not getall:
                    ## Get from domains owned by user and from shared domains
                    search = search.filter(or_(self.main.Domains.t_customers_id==self.main.customer_id, self.main.Domains.shared == True))
                search = search.all()
                if len(search) == 1:
                    return search[0]
            raise DoesNotExist('Domain %s not found' % domain)
        else:
            if not is_int(domain_id):
                raise RuntimeError('Invalid domain_id %s given' % domain_id)
            try:
                search = self.main.session.query(self.main.Domains).filter(self.main.Domains.t_domains_id == domain_id)
                if self.main.customer_id and not getall:
                    search = search.filter(self.main.Domains.t_customers_id==self.main.customer_id)
                search = search.one()
                self.main.session.commit()
                return search
            except NoResultFound:
                raise DoesNotExist('Domain id %s does not found' % domain_id)
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Error while getting domain')

    def add(self, domain, shared=False,dns=True, admin_address=None,
            domain_type='MASTER', refresh_time=None, retry_time=None,
            expire_time=None, minimum_cache_time=None, ttl=None,commit=True):
        """
        Create new Domain object

        """
        new = Domain(self.main)
        new.t_customers_id = self.main.customer_id
        new.name = domain
        new.shared = shared
        new.dns = dns
        new.domain_type = domain_type.upper()
        new.admin_address = admin_address
        new.refresh_time = refresh_time
        new.retry_time = retry_time
        new.expire_time = expire_time
        new.minimum_cache_time = minimum_cache_time
        new.ttl = ttl
        if commit:
            new.commit()
        return new


class Domain(object):
    """Domain object, holds information about spesific domain
    """

    def __init__(self, main, domain_id=None):
        # Force domain_id to be either None or positive integer
        self.main = main
        assert(domain_id == None or str(domain_id).isdigit())
        # Domain object values
        self._name = None
        self._domain_id = domain_id
        self._t_customers_id = None
        self._shared = None
        self._dns = None
        self.created = None
        self.updated = None
        self._refresh_time = None
        self._retry_time = None
        self._expire_time = None
        self._minimum_cache_time = None
        self._ttl = None
        self._admin_address = self.main.defaults.hostmaster_address
        self._domain_type = None
        self._masters = []
        self._allow_transfer = []
        self._approved = None

        # Other values
        self._vhosts = None
        self._email_aliases = None
        self._mailboxes = None
        self._database_object = None
        if self._domain_id:
            self._from_database()

    def commit(self):
        """
        Commit changes on Domain object to database
        """
        if not self._database_object:
            # Create new 
            self._database_object = self.main.Domains()
        self._database_object.name = self.name
        self._database_object.t_customers_id = self._t_customers_id
        self._database_object.shared = self._shared
        self._database_object.dns = self._dns
        self._database_object.domain_type = self._domain_type
        self._database_object.admin_address = self._admin_address
        self._database_object.refresh_time = self._refresh_time
        self._database_object.retry_time = self._retry_time
        self._database_object.expire_time = self._expire_time
        self._database_object.minimum_cache_time = self._minimum_cache_time
        self._database_object.ttl = self._ttl
        self._database_object.masters = self._masters
        self._database_object.allow_transfer = self._allow_transfer
        self._database_object._approved = self._approved
        # commit changes to database
        self.main.session.add(self._database_object)
        if not self.main.safe_commit():
            raise RuntimeError('Cannot add domain %s' % domain)
        self._domain_id = self._database_object.t_domains_id
        return True

    def _from_database(self, database_object=None):
        """
        Fetch Domain content from database
        """
        raise NotImplemented('TODO')
        if database_object:
            self._database_object = database_object
        elif not self._database_object:
            # fetch object from database
                search = search.filter(self.main.Domains.t_customers_id==self.main.customer_id)
                search = search.one()
                if not self.main.safe_commit():
                    raise RuntimeError("Cannot fetch Domain %s from database" %
                                       self._domain_id)
                self.database_object = search
        if self._database_object:
            # set variables
            self._name = self._database_object.name
            self._t_customers_id = self._database_object.t_customers_id
            # TODO


    def _get_vhosts(self):
        """
        Internal method to fetch vhosts
        """
        if not self.domain_id:
            raise RuntimeError("Cannot fetch vhost for uncommitted domain")
        elif self._vhosts == None:
            self.vhosts = self.main.vhosts.get(t_domains_id=self.domain_id)


    def _get_email_aliases(self):
        """
        Internal method to fetch email_aliases
        """
        if self.domain_id == None or self.name == None:
            raise RuntimeError("Cannot fetch email aliases for uncommitted domain")
        elif self._email_aliases == None:
           self._email_aliases =  self.main.mailboxes.list_aliases(self.name)


    def _get_mailboxes(self):
        """
        Internal method to fetch mailboxes
        """
        if self.domain_id == None or self.name == None:
            raise RuntimeError("Cannot fetch mailboxes for uncommitted domain")
        elif self._mailboxes == None:
            self._mailboxes = self.main.mailboxes.list(self.name)


    def list_vhosts(self):
        """
        Get list of vhosts on this domain
        """
        if self._vhosts == None:
            self._get_vhosts()
        if self._vhosts:
            return self._vhosts
        return []

    def list_email_aliases(self):
        """
        Get list of email addresses related to this domain
        """
        self._get_email_aliases()
        if self._email_aliases:
            return self._email_aliases
        return []

    def list_mailboxes(self):
        """
        Get list of email boxes related to this domain
        """
        self._get_mailboxes()
        if self._mailboxes:
            return self._mailboxes
        return []

    def delete(self):
        """
        Delete domain and related services

        Command gets directly committed to database

        This command deletes also all this domain related services
        - vhosts
        - email addresses
        """
        if not self.domain_id:
            raise RuntimeError("Can't delete domain from database")
        if not self.database_object:
            self.from_database()

        raise NotImplemented('TODO')

        for vhost in self.get_vhosts():
            vhost.delete()
        for mail_alias in self.list_email_addresses():
            mail_alias.delete()
        for mailbox in self.list_mailboxes():
            mailbox.delete()
        self.main.session.delete(self._database_object)
        try:
            self.main.session.commit()
        except OperationalError as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Operational error')
        except IntegrityError as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Cannot delete domain %s' % domain)
        return True


    # Domain values are properties

    @property
    def domain_id(self):
        if self._database_object:
            return self.database_object.t_domains_id
        return None

    @property
    def t_domains_id(self):
        return self.domain_id

    # t_domains_id is constant

    @property
    def t_customers_id(self):
        return self._t_customers_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if valid_fqdn(value):
            self._name = idna_domain(value).lower()
        else:
            raise ValueError('Domain name must be valid fully qualified domain name')

    @property
    def shared(self):
        return self._shared

    @shared.setter
    def shared(self, value):
        if not isinstance(value, bool):
            raise ValueError('A shared value must be boolean!')
        self._shared = value

    @property
    def dns(self):
        return self._dns

    @dns.setter
    def dns(self, value):
        if not isinstance(value, bool):
            raise ValueError('A dns value must be boolean!')
        self._dns = value

    @property
    def refresh_time(self):
        return self._refresh_time

    @refresh_time.setter
    def refresh_time(self, value):
        if value == None:
            value = self.main.defaults.retry_time
        if not isinstance(value, int):
            raise ValueError('A refresh_time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError('A refresh_time value must be between 1 and 999999')
        self._refresh_time = value

    @property
    def retry_time(self):
        return self._retry_time

    @retry_time.setter
    def retry_time(self, value):
        if value == None:
             value = self.main.defaults.retry_time
        if not isinstance(value, int):
            raise ValueError('A retry_time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError('A retry_time value must be between 1 and 999999')
        self._retry_time = value

    @property
    def expire_time(self):
        return self._expire_time

    @expire_time.setter
    def expire_time(self, value):
        if value == None:
             value = self.main.defaults.expire_time
        if not isinstance(value, int):
            raise ValueError('An expire time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError(
                           'A expire time value must be between 1 and 999999')
        self._expire_time = value


    @property
    def minimum_cache_time(self):
        return self._minimum_cache_time

    @minimum_cache_time.setter
    def minimum_cache_time(self, value):
        if value == None:
            value = self.main.defaults.minimum_cache_time
        if not isinstance(value, int):
            raise ValueError('A minimum cache time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError(
                    'A minimum cache time value must be between 1 and 999999')
        self._minimum_cache_time = value

    @property
    def ttl(self):
        return self._ttl

    @ttl.setter
    def ttl(self, value):
        if value == None:
            value = self.main.defaults.ttl
        if not isinstance(value, int):
            raise ValueError('A TTL value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError('A TTL value must be between 1 and 999999')
        self._ttl = value

    @property
    def admin_address(self):
        return self._admin_address
    @admin_address.setter
    def admin_address(self, value):
        if not value:
            self._admin_address = self.main.defaults.hostmaster_address
            return
        elif isinstance(value, str):
            value = unicode(value)
        if not isinstance(value, unicode):
            print(type(value))
            raise ValueError('An admin address must be string!')
        elif not valid_email(value):
            raise ValueError('An admin address must be valid email address!')
        self._admin_address = value

    @property
    def domain_type(self):
        return self._domain_type

    @domain_type.setter
    def domain_type(self, value):
        if not isinstance(value, str):
            raise ValueError('Domain type must be string!')
        elif value.upper() not in ['MASTER', 'SLAVE', 'NONE']:
            raise ValueError(
                            'Domain type must be either MASTER, SLAVE or NONE')
        self._domain_type = value.upper()
    @property
    def masters(self):
        return self._masters

    @masters.setter
    def masters(self, value):
        if not isinstance(value, list):
            raise ValueError('Masters value must be list!')
        values = []
        for ns in value:
            if not isinstance(ns, str) and not isinstance(ns, unicode):
                raise ValueError('Masters list contains invalid values!')
            ns = ns.strip()
            if not valid_fqdn(ns) and not valid_ipv4_address(ns) and \
                 not valid_ipv6_address(ns):
                raise ValueError('%s is not valid value for masters' % ns)
            elif ns == "localhost":
                raise ValueError("Masters server address can't be localhost!")
            values.append(ns)
        self._masters = values

    @property
    def allow_transfer(self):
        return self._allow_transfer

    @allow_transfer.setter
    def allow_transfer(self, value):
        if not isinstance(value, list):
            raise ValueError('Allow transfer value must be list!')
        values = []
        for ns in value:
            if not isinstance(ns, str) and not isinstance(ns, unicode):
                raise ValueError('Masters list contains invalid values!')
            ns = ns.strip()
            if not valid_fqdn(ns) and not valid_ipv4_address(ns) and \
                 not valid_ipv6_address(ns):
                raise ValueError('%s is not valid value for masters' % ns)
            elif ns == "localhost":
                raise ValueError("Masters server address can't be localhost!")
            values.append(ns)
        self._allow_transfer = values

    def __str__(self):
        return "Domain %s owner id %s" % (self.name, self.t_customers_id)

    def __unicode__(self):
        return unicode(self.__str__())

    def __repr__(self):
        return self.__str__()
