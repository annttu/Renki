#!/usr/bin/env python
# encoding: utf-8

"""
mail.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""

from services.exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import mapper, relationship

class Mailboxes(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.mailboxes')
        self.database_loaded = False
        if not self.main.dynamic_load:
            self._load_database()

    def _load_database(self):
        if self.database_loaded:
            return True
        mailbox = Table('mailboxes', self.main.metadata,
            Column("t_mailboxes_id", Integer, primary_key=True),
            Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
            Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
            autoload=True)
        mapper(self.main.Mailboxes, mailbox, properties={
            'customer': relationship(self.main.Customers, backref='mailboxes'),
            'domain': relationship(self.main.Domains, backref='mailboxes')
        })
        mail_aliases = Table('mail_aliases', self.main.metadata,
            Column('t_mail_aliases_id', Integer, primary_key=True),
            Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
            Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
            Column("t_mailboxes_id", Integer, ForeignKey('mailboxes.t_mailboxes_id')),
            autoload=True)
        mapper(self.main.Mail_aliases, mail_aliases, properties={
            'customer': relationship(self.main.Customers, backref='mail_aliases'),
            'domain': relationship(self.main.Domains, backref='mail_aliases'),
            'mailbox': relationship(self.main.Mailboxes, backref='mail_aliases')
        })
        self.database_loaded = True

    def check_email_address(self, address):
        """Validates given address
        Returns False if address is not valid
        Returns True if address is valid
        """
        self._load_database()
        if '@' not in address or len(address) < 5 or len(address.split('@')) != 2:
            return False
        domain = address.split('@')[1]
        try:
            self.main.domains.get(domain)
        except DoesNotExist or RuntimeError:
            return False
        return True

    def list(self, domain=None):
        """List all user mailboxes
        domain = (optional) limit mailboxes to this domain
        Returns list of mailbox objects
        Returns RuntimeError if domain not found
        """
        self._load_database()
        query = self.main.session.query(self.main.Mailboxes)
        if self.main.customer_id:
            query = query.filter(self.main.Mailboxes.t_customers_id==self.main.customer_id)
        if domain:
            try:
                dom = self.main.domains.get(domain)
            except DoesNotExist as e:
                raise RuntimeError(e)
            query = query.filter(self.main.Mailboxes.t_domains_id == dom.t_domains_id)
        retval = query.all()
        self.main.session.commit()
        return retval

    def get(self, address):
        """Get one mailbox
        address = mailbox address
        """
        self._load_database()
        try:
            query = self.main.session.query(self.main.Mailboxes).filter(self.main.Mailboxes.name == address)
            if self.main.customer_id:
                query = query.filter(self.main.Mailboxes.t_customers_id == self.main.customer_id)
            retval = query.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Mailbox %s not found' % address)
        except MultipleResultsFound:
            self.main.session.rollback()
            raise RuntimeError('Multiple maiboxes found with name %s' % address)

    def add(self, address, aliases=[]):
        """add mailbox to user
        address = mailbox primary address and name
        aliases = additional email aliases
        Raises RuntimeError on error
        Return True on successful insert
        """
        self._load_database()
        domain = address.split('@')[1].encode('idna').decode()
        address = "%s@%s" % (address.split('@')[0], domain)
        if self.main.check_email_address(address) != True:
            RuntimeError('Invalid email address "%s" given' % address)
        try:
            self.get(address)
            raise RuntimeError('Mailbox %s already exist' % address)
        except DoesNotExist:
            pass
        _aliases = aliases
        aliases = []
        for alias in _aliases:
            domain = alias.split('@')[1].encode('idna').decode()
            alias = "%s@%s" % (alias.split('@')[0], domain)
            if self.check_email_address(alias):
                aliases.append(alias)
            else:
                raise RuntimeError('Invalid email alias "%s" given' % address)
        try:
            self.get(address)
            raise RuntimeError('Mailbox %s already exist' % address)
        except DoesNotExist:
            pass

        mailbox = self.main.Mailboxes()
        mailbox.name = address
        mailbox.t_customers_id = self.main.customer_id
        mailbox.aliases = aliases
        self.main.session.add(mailbox)
        try:
            self.main.session.commit()
        except IntegrityError as e:
            self.log.error('Cannot add mailbox %s' % alias)
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Cannot add mailbox')
        return True

    def delete(self,mailbox):
        """Deletes mailbox
        mailbox = mailbox address eg. test@dom.tld
        """
        self._load_database()
        try:
            mailbox = self.get(mailbox)
        except DoesNotExist:
            raise RuntimeError('Mailbox %s does not exist!' % mailbox)
        self.main.session.delete(mailbox)
        try:
            self.main.session.commit()
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.error('Cannot delete mailbox %s' % mailbox)
            self.log.exception(e)


    ### mail aliases ###

    def list_aliases(self, domain=None):
        """List all customers mail aliases
        optionally filter by <domain>
        """
        self._load_database()
        query = self.main.session.query(self.main.Mail_aliases)
        if self.main.customer_id:
            query = query.filter(self.main.Mail_aliases.t_customers_id == self.main.customer_id)
        if domain:
            try:
                dom = self.main.domains.get(domain)
            except DoesNotExist as e:
                raise RuntimeError(e)
            query = query.filter(self.main.Mail_aliases.t_domains_id == dom.t_domains_id)
        retval = query.all()
        self.main.session.commit()
        return retval

    def add_alias(self, mailbox, alias):
        """add email alias to mailbox
        mailbox = mailbox to add alias to
        alias = alias to add
        return True on successful insert
        raise RuntimeError on error
        """
        self._load_database()
        try:
            mailbox = self.get(mailbox)
        except DoesNotExist:
            raise RuntimeError('mailbox %s does not exist' % mailbox)
        if self.check_email_address(alias) != True:
            raise RuntimeError('Invalid email alias "%s" given')
        aliases = []
        for a in mailbox.aliases:
            if a:
                aliases.append(a)
        aliases.append(alias)
        mailbox.aliases = aliases
        #print("Aliases: %s" % mailbox.aliases)
        try:
            self.main.session.commit()
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.error('Cannot add mail_alias %s' % alias)
            self.log.exception(e)
            raise RuntimeError('Cannot add mail_alias %s' % alias)
        return True

    def delete_alias(self, mailbox, alias):
        """delete email alias from mailbox
        mailbox = mailbox address
        alias = alias to remove
        Return True on successful delete
        Raises RuntimeError on error
        """
        self._load_database()
        try:
            mailbox = self.get(mailbox)
        except DoesNotExist:
            raise RuntimeError('mailbox %s does not exist' % mailbox)
        aliases = []
        for i in aliases:
            if i and i != alias:
                aliases.append(i)
        mailbox.aliases = aliases
        try:
            self.main.session.commit()
        except IntegrityError as e:
            raise RuntimeError('Cannot delete mailbox %s, database error')
        return True