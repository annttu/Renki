#!/usr/bin/env python
# encoding: utf-8
"""
vhost.py
"""

from exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# TODO
# - add_alias()
# - del_alias()
# - add_redirect()
# - del_redirect()

class Vhosts(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.vhosts')

    def add(self,name,redirects=[], aliases=[], redirect_to=None):
        """Function to create vhost object
        name = vhost name (mandatory)
        aliases = vhost aliases
        redirect = addresses redirecting to this vhost
        redirect_to = vhost is redirect to given address
        Raises RuntimeError on error
        Returns vhost id
        """
        if not name:
            raise RuntimeError('Vhost name is mandatory argument!')
        else:
            try:
                self.main.domains.get(name)
            except DoesNotExist:
                raise RuntimeError('Domain for vhost %s not found' % name)
        if redirect_to:
            redirect_to = redirect_to.lower()
            if not redirect_to.startswith('http://') and not redirect_to.startswith('https://'):
                raise RuntimeError('Invalid redirect_to url %s given' % redirect_to)
        for alias in aliases:
            try:
                self.main.domains.get(alias)
            except DoesNotExist:
                raise RuntimeError('Domain for alias %s not found' % alias)
        for redirect in redirects:
            try:
                self.main.domains.get(redirect)
            except DoesNotExist:
                raise RuntimeError('Domain for redirect %s not found' % redirect)
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
            self.main.reconnect()
            raise RuntimeError(e)
        return vhost.t_vhosts_id


    def create(self, addr, reverse=False):
        """"Function to add new vhosts
        addr = address to this domain.
        reverse = if name not specifield use domain as primary address and www.domain as redirect
        """
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
        if addr is not None:
            try:
                vhost = self.get(addr)
                self.main.session.delete(vhost)
                self.main.session.commit()
            except DoesNotExist:
                raise RuntimeError('Vhost %s not found' % addr)

    def get(self, addr, getall=True):
        """Get vhost object by address
        addr = address
        all = don't limit results to current user vhosts
        """
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
            vhosts = self.main.session.query(self.main.Vhosts)
            if self.main.customer_id:
                vhosts = vhosts.filter(self.main.Vhosts.t_customers_id == self.main.customer_id)
            if domain:
                try:
                    dom = self.main.domains.get(domain)
                    vhosts = vhosts.filter(self.main.Vhosts.t_domains_id == dom.t_domains_id)
                except DoesNotExist as e:
                    raise RuntimeError(e)
            retval = vhosts.all()
            self.main.session.commit()
            return retval

    def add_logaccess(self, addr):
        """Enable vhost logaccess"""
        try:
            vhost = self.get(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = True
        self.main.session.commit()
        return True

    def del_logaccess(self, addr):
        """Disable vhost logaccess"""
        try:
            vhost = self.get(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = False
        self.main.session.commit()
        return True