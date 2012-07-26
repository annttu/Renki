#!/usr/bin/env python
# encoding: utf-8
"""
vhost.py
"""

from services.exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError, InternalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import mapper, relationship

# TODO
# - add_alias()
# - del_alias()
# - add_redirect()
# - del_redirect()

class Vhosts(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.vhosts')
        self.database_loaded = False
        if not self.main.dynamic_load:
            self._load_database()

    def _load_database(self):
        """Dynamically load database when needed"""
        if self.database_loaded:
            return True
        vhosts = Table('vhosts', self.main.metadata,
                Column("t_vhosts_id", Integer, primary_key=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                Column("t_users_id", Integer, ForeignKey('users.t_users_id')),
                autoload=True)
        mapper(self.main.Vhosts, vhosts, properties={
            'customer': relationship(self.main.Customers, backref='vhosts'),
            'domain': relationship(self.main.Domains, backref='vhosts'),
            'user': relationship(self.main.Users, backref='vhosts')
            })
        vhost_aliases = Table('vhost_aliases', self.main.metadata,
            Column("t_vhosts_id", Integer, primary_key=True),
            Column("parent_id", Integer, ForeignKey('vhosts.t_vhosts_id')),
            autoload=True)
        mapper(self.main.Vhost_aliases, vhost_aliases, properties={
            'vhost': relationship(self.main.Vhosts, backref='vhost_aliases')
        })
        vhost_redirects = Table('vhost_redirects', self.main.metadata,
            Column("t_vhosts_id", Integer, primary_key=True),
            Column("parent_id", Integer, ForeignKey('vhosts.t_vhosts_id')),
            autoload=True)
        mapper(self.main.Vhost_redirects, vhost_redirects, properties={
            'vhost': relationship(self.main.Vhosts, backref='vhost_redirects')
        })
        self.database_loaded = True
        return True

    def valid_name(self,name):
        """Validate name"""
        for char in name:
            if char not in 'abcdefghijklmnopqrstuvwxyz0123456789._-*':
                return False
        return True

    def add(self,name,redirects=[], aliases=[], redirect_to=None):
        """Function to create vhost object
        name = vhost name (mandatory)
        aliases = vhost aliases
        redirect = addresses redirecting to this vhost
        redirect_to = vhost is redirect to given address
        Raises RuntimeError on error
        Returns vhost id
        """
        self._load_database()
        if not name:
            raise RuntimeError('Vhost name is mandatory argument!')
        if self.valid_name(name) is False:
            raise RuntimeError('Vhost name %s is not valid' % name)
        else:
            try:
                if self.main.admin_user:
                    self.main.domains.get(name,getall=True)
                else:
                    self.main.domains.get(name)
            except DoesNotExist:
                raise RuntimeError('Domain for vhost %s not found' % name)
            try:
                self.get(name)
                raise RuntimeError('Name %s already exist' % name)
            except DoesNotExist:
                pass

        if redirect_to:
            redirect_to = redirect_to.lower()
            if not redirect_to.startswith('http://') and not redirect_to.startswith('https://'):
                raise RuntimeError('Invalid redirect_to url %s given' % redirect_to)
        for alias in aliases:
            if self.valid_name(alias) is False:
                raise RuntimeError('Vhost alias name %s is not valid' % alias)
            try:
                if self.main.admin_user:
                    self.main.domains.get(alias,getall=True)
                else:
                    self.main.domains.get(alias)
            except DoesNotExist:
                raise RuntimeError('Domain for alias %s not found' % alias)
            try:
                self.get(alias)
                raise RuntimeError('Alias %s already exist' % name)
            except DoesNotExist:
                pass
        for redirect in redirects:
            if self.valid_name(redirect) is False:
                raise RuntimeError('Vhost alias name %s is not valid' % redirect)
            try:
                if self.main.admin_user:
                    self.main.domains.get(redirect,getall=True)
                else:
                    self.main.domains.get(redirect)
            except DoesNotExist:
                raise RuntimeError('Domain for redirect %s not found' % redirect)
            try:
                self.get(redirect)
                raise RuntimeError('Redirect %s already exist' % name)
            except DoesNotExist:
                pass
        if not self.main.username or self.main.username == '':
            raise RuntimeError('Select username first!')
        vhost = self.main.Vhosts()
        vhost.username = self.main.username
        vhost.aliases = aliases
        vhost.redirects = redirects
        vhost.name = name
        vhost.redirect_to = redirect_to
        self.main.session.add(vhost)
        try:
            self.main.session.commit()
        except IntegrityError or OperationalError as e:
            self.log.exception(e)
            self.main.reconnect()
            raise RuntimeError(e)
        except InternalError as e:
            self.main.session.rollback()
            self.log.exception(e)
            raise RuntimeError(e)
        return vhost.t_vhosts_id


    def create(self, addr, reverse=False):
        """"Function to add new vhosts
        addr = address to this domain.
        reverse = if name not specifield use domain as primary address and www.domain as redirect
        """
        self._load_database()
        if addr.startswith('www.') and not reverse:
            self.add(addr, redirects=[addr[4:]])
        elif reverse:
            if addr.startswith('www.'):
                addr = addr[4:]
            self.add(addr, redirects=['www.%s' % addr])
        else:
            self.add(addr)

    def delete(self,addr):
        """Delete vhost
        addr = vhost address to delete"""
        self._load_database()
        if addr is not None:
            try:
                vhost = self.get(addr)
                vhost.aliases = []
                vhost.redirects = []
                self.main.session.commit()
                self.main.session.delete(vhost)
                self.main.session.commit()
            except DoesNotExist:
                raise RuntimeError('Vhost %s not found' % addr)

    def get(self, addr, getall=True):
        """Get vhost object by address
        addr = address
        getall = don't limit results to current user vhosts
        """
        self._load_database()
        try:
            vhost = self.main.session.query(self.main.Vhosts).filter(self.main.Vhosts.name == addr)
            if self.main.customer_id and not getall:
                vhost = vhost.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
            if self.main.username and not getall:
                vhost = vhost.filter(self.main.Vhosts.username == self.main.username)
            retval = vhost.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            pass
        try:
            vhost = self.main.session.query(self.main.Vhosts).filter(':alias = ANY (aliases)').params(alias=addr)
            if self.main.customer_id and not getall:
                vhost = vhost.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
            if self.main.username and not getall:
                vhost = vhost.filter(self.main.Vhosts.username == self.main.username)
            retval = vhost.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            pass
        try:
            vhost = self.main.session.query(self.main.Vhosts).filter(':alias = ANY (redirects)').params(alias=addr)
            if self.main.customer_id and not getall:
                vhost = vhost.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
            if self.main.username and not getall:
                vhost = vhost.filter(self.main.Vhosts.username == self.main.username)
            retval = vhost.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Vhost %s not found' % addr)


    def list(self, domain=None):
            """Get all user vhost objects
            domain = (optional) limit search to this domain
            """
            self._load_database()
            vhosts = self.main.session.query(self.main.Vhosts)
            if self.main.customer_id:
                vhosts = vhosts.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
            if domain:
                try:
                    if self.main.admin_user:
                        dom = self.main.domains.get(domain,getall=True)
                    else:
                        dom = self.main.domains.get(domain)
                    vhosts = vhosts.filter(self.main.Vhosts.t_domains_id == dom.t_domains_id)
                except DoesNotExist as e:
                    raise RuntimeError(e)
            retval = vhosts.all()
            self.main.session.commit()
            return retval

    def add_logaccess(self, addr):
        """Enable vhost logaccess"""
        self._load_database()
        try:
            vhost = self.get(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = True
        self.main.session.commit()
        return True

    def del_logaccess(self, addr):
        """Disable vhost logaccess"""
        self._load_database()
        try:
            vhost = self.get(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = False
        self.main.session.commit()
        return True