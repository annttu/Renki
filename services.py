# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class DatabaseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value

class DoesNotExist(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return "%s" % self.value

class Services():
    def __init__(self, username, password, verbose=False):
        self.db = None
        self.username = username
        self.password = password
        self.verbose = verbose
        self.connect()
        self.customer_id = None
        self.session = None
        self.getSession()
        self.log = logging.getLogger('services')

    def connect(self, database=None,user=None,password=None,server=None, port=None):
        self.db = create_engine('postgresql://%s:%s@renki.n.kapsi.fi:5432/services' % (self.username, self.password), 
                                encoding='utf-8', echo=self.verbose)

    def getSession(self):
        """Function to get session"""
        metadata = MetaData(self.db)
        ## map tables to
        domains = Table('domains', metadata,
            Column("t_domains_id", Integer, primary_key=True), autoload=True)
        mapper(self.Domain, domains)
        vhosts = Table('vhosts', metadata,
            Column("t_vhosts_id", Integer, primary_key=True), autoload=True)
        mapper(self.Vhost, vhosts)
        mailbox = Table('mailboxes', metadata,
            Column("t_mailboxes_id", Integer, primary_key=True), autoload=True)
        mapper(self.Mailbox, mailbox)
        user_port = Table('user_ports', metadata,
            Column('t_user_ports_id', Integer, primary_key=True), 
            Column('active', Boolean, default=True), autoload=True)
        mapper(self.User_port, user_port)

        Session = sessionmaker(bind=self.db)
        self.session = Session()

    def reconnect(self):
        self.session.rollback()

    #############
    ## domains ##
    #############

    def list_domains(self):
        """List user domains"""
        res = self.session.query(self.Domain).all()
        return res

    def get_domain(self, name):
        """Get users all domain objects
        Returns list of Domain objects"""
        if not name:
            return
        name = name.split('.')
        domain = ''
        while len(name) > 0:
            if len(domain) > 0:
                domain = "%s.%s" % (name.pop(), domain)
            else:
                domain = name.pop()
            search = self.session.query(self.Domain).filter(self.Domain.name == domain).all()
            if len(search) == 1:
                return search[0]
        self.log.warning('Domain %s not found' % domain)
        raise DoesNotExist('Domain %s not found' % domain)

    def add_domain(self, domain, shared=False,dns=True, admin_address=None,
                    domain_type='master', refresh_time=None, retry_time=None,
                    expire_time=None, minimum_cache_time=None, ttl=None):
        """add domain for user"""
        if domain_type not in ('master', 'slave', 'none'):
            return False
        new = self.Domain()
        new.name = domain
        new.shared = shared
        new.dns = dns
        if admin_address:
            new.admin_address = admin_address

        new.domain_type = domain_type
        self.session.add(new)
        self.session.commit()
        return True

    def del_domain(self, domain):
        raise NotImplementedError('Not created yet')
        # delete vhosts and mailboxes before that

    ############
    ## vhosts ##
    ############

    def create_vhost(self, aliases, reverse=False, redirect=None):
        """Function to create vhost objects
        aliases = list of aliases
        redirect = address to redirect must start with http:// or https://
        """

        if aliases == []:
            raise RuntimeError('aliases cannot be empty array')

        vhost = self.Vhost()
        vhost.aliases = aliases
        if redirect:
            if redirect.startswith('http://') or redirect.startswith('https://'):
                vhost.redirect_to = redirect
            else:
                raise RuntimeError ('Invalid redirect address. Address must start with http:// or https://')
        try:
            self.session.add(vhost)
            self.session.commit()
        except IntegrityError as e:
            self.log.exception(e)
            raise RuntimeError('Vhost is already exist on database')
        except Exception as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Cannot commit data to database')
        return vhost.t_vhosts_id

    def add_vhost(self, addr, reverse=False):
        """Function to add new vhosts
        addr = address to this domain.
        reverse = if name not specifield use domain as primary address and www.domain as redirect
        """
        if addr.startswith('www.') and not reverse:
            self.create_vhost([addr])
            self.create_vhost([addr[4:]], redirect='http://%s' % addr)
        elif reverse:
            if addr.startswith('www.'):
                addr = addr[4:]
            self.create_vhost([addr])
            self.create_vhost(['www.%s' % addr], redirect='http://%s' % addr)
        else:
            print('%s' % addr)
            self.create_vhost([addr])

    def del_vhost(self,addr):
        """Delete vhost
        addr = vhost address to delete"""
        if addr is not None:
            try:
                vhost = self.session.query(self.Vhost).filter(':alias = ANY (aliases)').params(alias=addr).one()
                print(dir(vhost))
                self.session.delete(vhost)
                self.session.flush()
            except NoResultFound:
                raise DoesNotExist('Vhost %s not found' % addr)

    ###############
    ## mailboxes ##
    ###############

    def check_email_address(self, address):
        """Validates given address
        Returns False if address is not valid
        Returns True if address is valid
        """
        if '@' not in address or len(address) < 5 or len(address.split('@')) != 2:
            return False
        domain = address.split('@')[1]
        try:
            self.get_domain(domain)
        except DoesNotExist or RuntimeError:
            return False
        return True

    def list_mailboxes(self):
        """List all user mailboxes
        Returns list of mailbox objects"""
        query = self.session.query(self.Mailbox)
        if self.customer_id:
            query = query.filter(self.Mailbox.t_customers_id==self.customer_id)
        return query.all()

    def get_mailbox(self, address):
        """Get one mailbox 
        address = mailbox address"""
        try:
            query = self.session.query(self.Mailbox).filter(self.Mailbox.name == address)
            if self.customer_id:
                query = query.filter(self.Mailbox.t_customer_id == self.customer_id)
            return query.one()
                
        except NoResultFound:
            raise DoesNotExist('Mailbox %s not found' % address)
        except MultipleResultsFound:
            raise RuntimeError('Multiple maiboxes found with name %s' % address)

    def add_mailbox(self, address, aliases=[]):
        """add mailbox to user
        address = mailbox primary address and name
        aliases = additional email aliases
        Raises RuntimeError on error
        Return True on successful insert
        """
        domain = address.split('@')[1].encode('idna').decode()
        address = "%s@%s" % (address.split('@')[0], domain)
        if self.check_email_address(address) != True:
            RuntimeError('Invalid email address "%s" given' % address)
        try:
            print ("get_mailbox: %s" % self.get_mailbox(address))
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
            self.get_mailbox(address)
            raise RuntimeError('Mailbox %s already exist' % address)
        except DoesNotExist:
            pass
            
        mailbox = self.Mailbox()
        mailbox.name = address
        mailbox.t_customers_id = self.customer_id
        mailbox.aliases = aliases
        self.session.add(mailbox)
        try:
            self.session.commit()
        except IntegrityError:
            self.log.error('Cannot add mailbox %s' % alias)
            self.log.exception(e)
            raise RuntimeError('Cannot add mailbox')
        return True
      
    def del_mailbox(self,mailbox):
        """Deletes mailbox
        mailbox = mailbox address eg. test@dom.tld
        """
        try:
            mailbox = self.get_mailbox(mailbox)
        except DoesNotExist:
            raise RuntimeError('Mailbox %s does not exist!' % mailbox)
        self.session.delete(mailbox)
        try:
            self.commit()
        except IntegrityError as e:
            self.log.error('Cannot delete mailbox %s' % mailbox)
            self.log.exception(e)
      
    def add_mail_alias(self, mailbox, alias):
        """add email alias to mailbox
        mailbox = mailbox to add alias to
        alias = alias to add
        return True on successful insert
        raise RuntimeError on error"""
        try:
            mailbox = self.get_mailbox(mailbox)
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
        print("Aliases: %s" % mailbox.aliases)
        try:
            self.session.commit()
        except IntegrityError as e:
            self.log.error('Cannot add mail_alias %s' % alias)
            self.log.exception(e)
            raise RuntimeError('Cannot add mail_alias %s' % alias)
        return True

    def del_mail_alias(self, mailbox, alias):
        """delete email alias from mailbox
        mailbox = mailbox address
        alias = alias to remove
        Return True on successful delete 
        Raises RuntimeError on error
        """
        try:
            mailbox = self.get_mailbox(mailbox)
        except DoesNotExist:
            raise RuntimeError('mailbox %s does not exist' % mailbox)
        aliases = []
        for i in aliases:
            if i and i != alias:
                aliases.append(i)
        mailbox.aliases = aliases
        try:
            session.commit()
        except IntegrityError as e:
            raise RuntimeError('Cannot delete mailbox %s, database error')
        return True

    def __del__(self):
        try:
            self.session.close()
        except:
            pass


    class Domain(object):
        """Domain objects
        object mapped to domains view"""
        pass


    class Vhost(object):
        """Vhost objects
        object mapped to vhosts view"""
        pass

    
    class Mailbox(object):
        """Mailbox objects
        object mapped to mailboxes view"""
        pass


    class User_port(object):
        """User_port objects
        object mapped to user_ports view"""
        pass
