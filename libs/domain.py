#!/usr/bin/env python
# encoding: utf-8
"""
domain.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""

from services.exceptions import *
import logging
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import mapper

from services.libs.tools import is_int

class Domains(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.databases')


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
            if refresh_time >= 1 and refresh_time <= 9999999:
                new.refresh_time = refresh_time
            else:
                raise RuntimeError('Invalid refresh_time %s' % refresh_time)
        if retry_time:
            if retry_time >= 1 and retry_time <= 9999999:
                new.retry_time = retry_time
            else:
                raise RuntimeError('Invalid retry_time %s' % retry_time)
        if expire_time:
            if expire_time >= 1 and expire_time <= 9999999:
                new.expire_time = expire_time
            else:
                raise RuntimeError('Invalid expire_time %s' % expire_time)
        if minimum_cache_time:
            if minimum_cache_time >= 1 and minimum_cache_time <= 9999999:
                new.minimum_cache_time = minimum_cache_time
            else:
                raise RuntimeError('Invalid minimum_cache_time %s' % minimum_cache_time)
        if ttl:
            if ttl >= 1 and ttl <= 9999999:
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
    pass