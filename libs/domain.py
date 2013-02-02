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

from services.libs.tools import is_int, is_bool, valid_fqdn, valid_ipv4_address, valid_ipv6_address

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
                    expire_time=None, minimum_cache_time=None, ttl=None):
        """add domain for user"""
        new = self.main.Domains()
        new.t_customers_id = self.main.customer_id
        new.name = domain
        new.shared = shared
        new.dns = dns
        if domain_type.upper() in ['MASTER', 'SLAVE', 'NONE']:
            new.domain_type = domain_type.upper()
        elif domain_type:
            raise RuntimeError('Invalid domain type %s' % domain_type)
        if admin_address:
            new.admin_address = admin_address
        else:
            new.admin_address = self.main.defaults.hostmaster_address
        if refresh_time:
            if refresh_time >= 1 and refresh_time <= 999999:
                new.refresh_time = refresh_time
            else:
                raise RuntimeError('Invalid refresh_time %s' % refresh_time)
        if retry_time:
            if retry_time >= 1 and retry_time <= 999999:
                new.retry_time = retry_time
            else:
                raise RuntimeError('Invalid retry_time %s' % retry_time)
        if expire_time:
            if expire_time >= 1 and expire_time <= 999999:
                new.expire_time = expire_time
            else:
                raise RuntimeError('Invalid expire_time %s' % expire_time)
        if minimum_cache_time:
            if minimum_cache_time >= 1 and minimum_cache_time <= 999999:
                new.minimum_cache_time = minimum_cache_time
            else:
                raise RuntimeError('Invalid minimum_cache_time %s' % minimum_cache_time)
        if ttl:
            if ttl >= 1 and ttl <= 999999:
                new.ttl = ttl
            else:
                raise RuntimeError('Invalid ttl %s' % ttl)
        try:
            self.main.session.add(new)
            self.main.session.commit()
        except OperationalError as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Operational error')
        except IntegrityError as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Cannot add domain %s' % domain)

        return True

    def delete(self, domain):
        """Delete given domain and it dependencies
        """
        # delete these before domain
        # - vhosts
        # - mail aliases
        # - mailboxes
        if not domain or domain == '':
            raise RuntimeError('No domain given to del_domain')
        try:
            dom = self.get(domain)
        except DoesNotExist:
            raise RuntimeError('Domain %s does not found' % domain)
        for vhost in self.main.vhosts.list(domain):
            self.main.session.delete(vhost)
        for mail_alias in self.main.mailboxes.list_aliases(domain):
            self.main.session.delete(mail_alias)
        for mailbox in self.main.mailboxes.list(domain):
            self.main.session.delete(mailbox)
        self.main.session.delete(dom)
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

class Domain(object):
    """Domain object, holds information about spesific domain
    """

    def __init__(self, main, domain_id=None):
        # Force domain_id to be either None or positive integer
        self.main = main
        assert(domain_id == None or str(domain_id).isdigit())
        self.name = None
        self.domain_id = id
        self.t_customers_id = None
        self._shared = None
        self._dns = None
        self.created = None
        self.updated = None
        self._refresh_time = None
        self._retry_time = None
        self._expire_time = None
        self._minimum_cache_time = None
        self._ttl = None
        self._admin_address = None
        self._domain_type = None
        self._masters = []
        self._allow_transfer = []
        self._approved = None

    def commit(self):
        """
        Commit changes on Domain object to database
        """
        raise NotImplemented('TODO')

    def from_database(self):
        """
        Fetch Domain content from database
        """
        self._get_vhosts()
        raise NotImplemented('TODO')

    def _get_vhosts(self):
        """
        Internal method to fetch vhosts from database
        """
        raise NotImplemented('TODO')

    def delete(self):
        """
        Delete this object
        Marks object to be deleted from database at next commit
        """
        raise NotImplemented('TODO')


    # Domain values are properties

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
        if not isinstance(value, int):
            raise ValueError('A refresh_time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError('A refresh_time value must be between 1 and 999999')
        self._refresh_time = value

    @property
    def retry_time(self):
        return self.retry_time

    @retry_time.setter
    def retry_time(self, value):
        if not isinstance(value, int):
            raise ValueError('A retry_time value must be integer!')
        elif value < 1 or value > 999999:
            raise ValueError('A retry_time value must be between 1 and 999999')
        self._retry_time = value

    @property
    def expire_time(self):
        return self.expire_time

    @expire_time.setter
    def expire_time(self, value):
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
        if not isinstance(value, str):
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

    @masters.setter
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
        self._allow_transfer= values

