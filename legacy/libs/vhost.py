#!/usr/bin/env python
# encoding: utf-8
"""
vhost.py
"""

from services.exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError, InternalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import mapper, relationship

from libs.tools import *

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
        if not self.main.dynamic_load and not self.main.loaded:
            self._load_database()

    def _load_database(self):
        """Dynamically load database when needed"""
        if self.database_loaded or (self.main.loaded and not self.main.dynamic_load):
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

    def add(self,name,redirects=[], aliases=[], redirect_to=None, username=None,
            t_services_id = None, server = None):
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
        if not username:
            if not self.main.username or self.main.username == '':
                raise RuntimeError('Select username first!')
            username = self.main.username
        if server:
            try:
                t_services_id = self.get_server(server).t_services_id
            except DoesNotExist as e:
                raise RuntimeError(e)
        vhost = self.main.Vhosts()
        vhost.username = username
        vhost.aliases = aliases
        vhost.redirects = redirects
        vhost.name = name
        vhost.redirect_to = redirect_to
        vhost.t_services_id = t_services_id
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
        except TypeError:
            # maybe sqlalchemy bug, if insert don't return anything, 
            # it causes TypeError
            self.main.session.rollback()
            raise RuntimeError('Insert didn\'t return anyting')
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

    def get(self, addr=None,vhost_id=None, getall=True):
        """Get vhost object by address
        addr = address
        vhost_id = vhosts id
        getall = don't limit results to current user vhosts
        """
        self._load_database()
        if not addr and not vhost_id:
            return None
        if vhost_id:
            try:
                vhost = self.main.session.query(self.main.Vhosts).filter(self.main.Vhosts.t_vhosts_id == vhost_id)
                if self.main.customer_id and not getall:
                    vhost = vhost.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
                if self.main.username and not getall:
                    vhost = vhost.filter(self.main.Vhosts.username == self.main.username)
                retval = vhost.one()
                self.main.session.commit()
                return retval
            except NoResultFound:
                self.main.session.rollback()
                raise DoesNotExist('Vhost %s does not found' % vhost_id)
        if addr:
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

    def get_server(self, server):
        """Get vhost_server object by name"""
        try:
            return self.main.session.query(self.main.Services
                    ).filter(self.main.Services.server == server,
                    self.main.Services.service_type == 'VHOST').one()
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Vhost server %s does not exist' % server)
        return

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

class Vhost(object):
    def _init__(self, main, database_object=None):
        if not main:
            raise ValueError("Missing main-object")
        self.main = main
        if database_object:
            self._database_object = database_object
        else:
            self._database_object = self.main.Vhosts()

    def commit(self):
        """
        Commit changes to database.
        """
        self.main.session.add(self._database_object)
        return self.main.safe_commit()

    def delete(self):
        """
        Delete this vhost from database
        """
        if self._database_object:
            self.main.session.delete(self._database_object)
            return self.main.safe_commit()
        else:
            return True

    def _get_server_by_name(self, server):
        """
        Get vhost server matching t_services_id
        Raise DoesNotExist if not found
        """
        try:
            retval = self.main.session.query(self.main.Services
                    ).filter(self.main.Services.server == server,
                    self.main.Services.service_type == 'VHOST').one()
            # Don't leave open transactions
            self.main.safe_commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Vhost server %s does not exist' % server)
        return

    def _get_server_by_name(self, t_services_id):
        """
        Get vhost server matching t_services_id
        Raise DoesNotExist if not found
        """
        try:
            retval = self.main.session.query(self.main.Services
                    ).filter(self.main.Services.t_services_id == t_services_id,
                    self.main.Services.service_type == 'VHOST').one()
            # Don't leave open transactions
            self.main.safe_commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Vhost server %s does not exist' % t_services_id)

    @property
    def t_customers_id(self):
        return self._database_object.t_customers_id

    @t_customers_id.setter
    def t_customers_id(self):
        if value == None:
            return
        value = to_int(value)
        if value != self.main.customer_id:
            self.main.require_admin()
        self._database_object.t_customers_id = value

    @property
    def username(self):
        return self._database_object.username

    @username.setter
    def username(self, value):
        if value == None:
            return
        value = to_int(value)
        if value != self.main.username:
            self.main.require_admin()
        self._database_object.username = value

    @property
    def name(self):
        return self._database_object.name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) and not isinstance(value, unicode):
            raise ValueError("Vhost name must be string")
        if not valid_fqdn(self._domain.name + value):
            raise ValueError("Vhost name is not valid")


    @property
    def aliases(self):
        if not self._database_object.aliases:
            return []
        return self._database_object.aliases

    @aliases.setter
    def aliases(self, value):
        values = []
        if value == None:
            self._database_objects.aliases = []
            return True
        if not isinstance(value, tuple) and not isinstance(value, list):
            raise ValueError("Aliases value must be list")
        for alias in value:
            if not isinstance(alias,str) and not isinstance(alias, unicode):
                raise ValueError("Aliases list contain invalid value \"%s\"")
            alias = alias.strip()
            if not valid_fqdn(alias) and not valid_ipv4_address(alias) and \
                not valid_ipv6_address(alias):
                raise ValueError("Aliases list contains invalid value \"%s\"")
            elif is_local_addr(alias):
                raise ValueError("Masters server address can't be localhost!")

            values.append(alias)
        self._database_object.aliases = values
        return True

    @property
    def redirects(self):
        if not self._database_object.redirects:
            return []
        return self._database_object.redirects

    @redirects.setter
    def redirects(self, value):
        values = []
        if value == None:
            self._database_objects.redirects = []
            return True
        if not isinstance(value, tuple) and not isinstance(value, list):
            raise ValueError("Aliases value must be list")
        for redirect in value:
            if not isinstance(redirect,str) and not isinstance(redirect, unicode):
                raise ValueError("Aliases list contain invalid value \"%s\"")
            redirect = redirect.strip()
            if not valid_fqdn(redirect) and not valid_ipv4_address(redirect) and \
                not valid_ipv6_address(redirect):
                raise ValueError("Aliases list contains invalid value \"%s\"")
            elif is_local_addr(redirect):
                raise ValueError("Masters server address can't be localhost!")
            values.append(redirect)
        self._database_object.redirects = values
        return True

    @property
    def t_services_id(self):
        return self._database_object.t_services_id

    @t_services_id.setter
    def t_services_id(self, value):
        try:
            self._server = self._get_server_by_id(value)
        except DoesNotExist as e:
            raise ValueError(e)
        self._database_object.t_services_id = value

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        if not isinstance(value, self.main.Services):
            raise ValueError("Vhost server value must be Services object")
        try:
            self._server = self._get_server_by_id(value.t_services_id)
        except DoesNotExist as e:
            raise ValueError(e)
        self._database_object.t_services_id = value
