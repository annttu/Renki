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

from services.libs.tools import idna_address, idna_domain

class Mailboxes(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.mailboxes')
        self.database_loaded = False
        if not self.main.dynamic_load and not self.main.loaded:
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

    def list(self, domain=None,domain_id=None):
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
        elif domain_id:
            query = query.filter(self.main.Mailboxes.t_domains_id == domain_id)
        retval = query.all()
        self.main.session.commit()
        return retval

    def get(self, address):
        """Get one mailbox
        address = mailbox address
        """
        self._load_database()
        mailbox = self.mailbox()
        mailbox.get(address=address)
        return mailbox.object

    """
    def add(self, address, aliases=[]):
        ""add mailbox to user
        address = mailbox primary address and name
        aliases = additional email aliases
        Raises RuntimeError on error
        Return True on successful insert
        ""
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
        ""Deletes mailbox
        mailbox = mailbox address eg. test@dom.tld
        ""
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

    """
    ### mail aliases ###

    def list_aliases(self, domain=None, domain_id=None):
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
        elif domain_id:
            query = query.filter(self.main.Mail_aliases.t_domains_id == domain_id)
        retval = query.all()
        self.main.session.commit()
        return retval
    """
    def add_alias(self, mailbox, alias):
        ""add email alias to mailbox
        mailbox = mailbox to add alias to
        alias = alias to add
        return True on successful insert
        raise RuntimeError on error
        ""
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
        ""delete email alias from mailbox
        mailbox = mailbox address
        alias = alias to remove
        Return True on successful delete
        Raises RuntimeError on error
        ""
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
    """

    def mailbox(self):
        self._load_database()
        return Mailbox(self)

class Mailbox(object):
    """Mailbox class
    """
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.mailbox')
        self.object = None
        self.address = None
        self.mailbox_id = None
        self.customer_id = self.main.customer_id
        self.aliases = []
        self.domain_id = None

    def validate_address(self, address):
        """Validates given address
        Returns False if address is not valid
        Returns True if address is valid
        """
        if '@' not in address or len(address) < 5 or len(address.split('@')) != 2:
            return False
        domain = address.split('@')[1]
        try:
            self.main.domains.get(domain)
        except DoesNotExist or RuntimeError:
            return False
        return True

    def add_alias(self,address):
        """Add alias to mailbox"""
        if self._validate_alias(address) is False:
                raise RuntimeError('Invalid alias address %s' % address)
        if address not in self.aliases:
            self.aliases.append(address)
        return True

    def del_alias(self,address):
        """Delete alias from mailbox"""
        newaliases = []
        for alias in self.aliases:
            if alias != address:
                newaliases.append(alias)
        if self.aliases == newaliases:
            raise RuntimeError('Alias %s does not found' % address)
        else:
            self.aliases = newaliases
        return True


    def get(self, address=None):
        """Get mailbox object by
        address
        name and domain
        name and domain_id
        """
        query = self.main.session.query(self.main.Mailboxes)
        """if domain is None and domain_id is None and name is not None:
            raise RuntimeError('Give either domain or domain_id')
        elif domain is not None and name is not None:
            domain = domain.encode('idna').decode()
            try:
                domain = self.main.domains.get(domain)
            except DoesNotExist:
                raise DoesNotExist('Mailbox %s@%s does not found' % (name, domain))
            query = query.filter(self.main.Mailboxes.name == name)
            query = query.filter(self.main.Mailboxes.t_domains_id == domain.t_domains_id)
        elif domain_id is not None and name is not None:
            query = query.filter(self.main.Mailboxes.name == name)
            query = query.filter(self.main.Mailboxes.t_domains_id == domain_id)"""
        if address is not None and '@' in address and is_int(address) is True:
            address = idna_address(address)
            query = query.filter(self.main.Mailboxes.address == address)
        else:
            raise RuntimeError('Invalid options given to mailbox.get')

        try:
            if self.main.customer_id:
                query = query.filter(self.main.Mailboxes.customer_id == self.main.customer_id)
            retval = query.one()
            self.object = retval
            self.address = retval.name
            self.mailbox_id = retval.t_mailboxes_id
            self.customer_id = retval.t_customers_id
            self.domain_id = retval.t_domains_id
            self.aliases = retval.aliases
            self.main.session.commit()
        except NoResultFound:
            if address is not None:
                raise DoesNotFound('Mailbox %s does not found' % address)
                """elif name is not None and domain is not None:
                raise DoesNotFound('Mailbox %s@%s does not found' % (name,domain.name))"""
            else:
                raise DoesNotFound('Mailbox does not found')
        except Exception as e:
            self.log.exception(e)
            raise RuntimeError('Cannot get mailbox')

    def _valid_name(self,name):
        """Validate mailbox name"""
        try:
            if len(name) < 2:
                return False
        except ValueError:
            return False
        for char in name:
            if char not in 'abcdefghijklmnopqrstuyvwxyz0123456789+-_!%&()[]=?':
                return False
        return True

    def _validate(self):
        """Validate object"""
        if self.address is None:
            raise RuntimeError('Mailbox must have address')
        if self.domain_id is not None:
            try:
                domain = self.main.domains.get(domain_id=self.domain_id)
            except DoesNotExist:
                raise RuntimeError('Domain %s does not exist')
        if len(self.name.split('@') != 2):
            raise RuntimeError('Mailbox address %s is not valid')
        name, domain = address.split('@',2)
        if not self._valid_name(name):
            raise RuntimeError('Mailbox name %s is not valid' % self.name)
        try:
            domain = self.main.domains.get(domain)
        except DoesNotExist:
            raise RuntimeError('Domain for mailbox %s does not found' % self.address)
        for alias in aliases:
            if self._validate_alias(alias) is False:
                raise RuntimeError('Invalid alias address %s' % alias)

    def _validate_alias(self,alias):
        """Validate mailbox alias"""
        if self.validate_address(address) is False:
            return False
        return True

    def commit(self):
        """Commit object to database"""
        if self.object is None:
            # new object
            self.object = self.main.Mailboxes()
            self.object.name = self.address
            if self.customer_id is None:
                self.object.t_customer_id = self.main.customer_id
            if len(self.aliases) != 0:
                self.object.aliases = self.aliases
            self.main.session.add(self.object)
        else:
            self.object.name = self.address
            self.object.customer_id = self.customer_id
            self.object.aliases = self.aliases
        try:

            self.main.session.commit()
            self.mailbox_id = self.object.t_mailboxes_id
        except Exception as e:
            self.log.exception(e)
            raise RuntimeError('Cannot commit mailbox to database')

    def delete(self):
        """Delete mailbox"""
        if self.mailbox_id is None or self.object is None:
            raise RuntimeError('Cannot delete mailbox before get')
        self.mail.session.delete(self.object)
        try:
            self.main.session.commit()
        except Exception as e:
            self.log.exception(e)
        return True