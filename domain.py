#!/usr/bin/env python
# encoding: utf-8
"""
domain.py
"""

from exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

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

    def get(self, name):
        """Get user domain matching name"""
        if not name:
            return
        name = name.split('.')
        domain = ''
        while len(name) > 0:
            if len(domain) > 0:
                domain = "%s.%s" % (name.pop(), domain)
            else:
                domain = name.pop()
            search = self.main.session.query(self.main.Domains).filter(self.main.Domains.name == domain)
            if self.main.customer_id:
                search = search.filter(self.main.Domains.t_customers_id==self.main.customer_id)
            search = search.all()
            if len(search) == 1:
                return search[0]
        self.log.warning('Domain %s not found' % domain)
        raise DoesNotExist('Domain %s not found' % domain)

    def add(self, domain, shared=False,dns=True, admin_address=None,
                    domain_type='master', refresh_time=None, retry_time=None,
                    expire_time=None, minimum_cache_time=None, ttl=None):
        """add domain for user"""
        new = self.main.Domains()
        new.t_customers_id = self.main.customer_id
        new.name = domain
        new.shared = shared
        new.dns = dns
        if domain_type.lower() in ['master', 'slave', 'none']:
            new.domain_type = domain_type.lower()
        elif domain_type:
            raise RuntimeError('Invalid domain type %s' % domain_type)
        if admin_address:
            new.admin_address = admin_address
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
            self.reconnect()
            raise RuntimeError('Operational error')
        except IntegrityError as e:
            self.log.exception(e)
            raise RuntimeError('Cannot add domain %s' % name)

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
        for mail_alias in self.main.mail.list_aliases(domain):
            self.main.session.delete(mail_alias)
        for mailbox in self.main.mail.list(domain):
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
