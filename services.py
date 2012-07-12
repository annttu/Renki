# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
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

def on_connect_listener(target, context):
    print("Reconnecting to database...")

def on_first_connect_listener(target, context):
    print("Connecting to database...")

class Services():
    def __init__(self, username, password, server, verbose=False):
        self.db = None
        self.username = username
        self.password = password
        self.server=server
        self.verbose = verbose
        if self.verbose:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        else:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
        self.connect()
        self.customer_id = None
        self.username = None
        self.session = None
        self.getSession()
        if not self.session:
            raise RuntimeError('Invalid login')
        self.log = logging.getLogger('services')

    def connect(self, database=None,user=None,password=None,server=None, port=None):
        self.db = create_engine('postgresql://%s:%s@%s' % (self.username, self.password, self.server),
                                encoding='utf-8', echo=self.verbose, pool_recycle=60)

    def getSession(self):
        """Function to get session"""
        try:
            metadata = MetaData(self.db)
            ## map tables to
            event.listen(Pool, 'first_connect', on_first_connect_listener)
            domains = Table('domains', metadata,
                Column("t_domains_id", Integer, primary_key=True), autoload=True)
            mapper(self.Domain, domains)
            #event.listen(self.Domain, 'load', on_load_listener)
            vhosts = Table('vhosts', metadata,
                Column("t_vhosts_id", Integer, primary_key=True), autoload=True)
            mapper(self.Vhost, vhosts)
            vhost_aliases = Table('vhost_aliases', metadata,
                Column("t_vhosts_id", Integer, primary_key=True), autoload=True)
            mapper(self.Vhost_aliases, vhost_aliases)
            vhost_redirects = Table('vhost_redirects', metadata,
                Column("t_vhosts_id", Integer, primary_key=True), autoload=True)
            mapper(self.Vhost_redirects, vhost_redirects)
            mailbox = Table('mailboxes', metadata,
                Column("t_mailboxes_id", Integer, primary_key=True), autoload=True)
            mapper(self.Mailbox, mailbox)
            mail_aliases = Table('mail_aliases', metadata,
                Column('t_mail_aliases_id', Integer, primary_key=True), autoload=True)
            mapper(self.Mail_aliases, mail_aliases)
            user_port = Table('user_ports', metadata,
                Column('t_user_ports_id', Integer, primary_key=True),
                Column('active', Boolean, default=True), autoload=True)
            mapper(self.User_port, user_port)
            host = Table('hosts', metadata,
                Column("hosts_id", Integer, primary_key=True), autoload=True)
            mapper(self.Host, host)
            Session = sessionmaker(bind=self.db)
            self.session = Session()
            event.listen(Pool, 'connect', on_connect_listener)
        except OperationalError:
            self.session = None

    def reconnect(self):
        self.session.rollback()

    #############
    ## domains ##
    #############

    def list_domains(self):
        """List user all domains"""
        try:
            res = self.session.query(self.Domain)
            if self.customer_id:
                res = res.filter(self.Domain.t_customers_id==self.customer_id)
                return res.all()
        except DatabaseError as e:
            raise RuntimeError(e)

    def get_domain(self, name):
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
            search = self.session.query(self.Domain).filter(self.Domain.name == domain)
            if self.customer_id:
                search = search.filter(self.Domain.t_customers_id==self.customer_id)
            search = search.all()
            if len(search) == 1:
                return search[0]
        self.log.warning('Domain %s not found' % domain)
        raise DoesNotExist('Domain %s not found' % domain)

    def add_domain(self, domain, shared=False,dns=True, admin_address=None,
                    domain_type='master', refresh_time=None, retry_time=None,
                    expire_time=None, minimum_cache_time=None, ttl=None):
        """add domain for user"""
        new = self.Domain()
        new.t_customers_id = self.customer_id
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
            self.session.add(new)
            self.session.commit()
        except OperationalError as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Operational error')
        except IntegrityError as e:
            self.log.exception(e)
            raise RuntimeError('Cannot add domain %s' % name)

        return True

    def del_domain(self, domain):
        """Delete given domain and it dependencies
        """
        # delete these before domain
        # - vhosts
        # - mail aliases
        # - mailboxes
        if not domain or domain == '':
            raise RuntimeError('No domain given to del_domain')
        try:
            dom = self.get_domain(domain)
        except DoesNotExist:
            raise RuntimeError('Domain %s does not found' % domain)
        for vhost in self.list_vhosts(domain):
            self.session.delete(vhost)
        for mail_alias in self.list_mail_aliases(domain):
            self.session.delete(mail_alias)
        for mailbox in self.list_mailboxes(domain):
            self.session.delete(mailbox)
        self.session.delete(dom)
        try:
            self.session.commit()
        except OperationalError as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Operational error')
        except IntegrityError as e:
            self.log.exception(e)
            self.reconnect()
            raise RuntimeError('Cannot delete domain %s' % domain)
        return True

    ############
    ## vhosts ##
    ############

    def add_vhost(self,name,redirects=[], aliases=[], redirect_to=None):
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
                self.get_domain(name)
            except DoesNotExist:
                raise RuntimeError('Domain for vhost %s not found' % name)
        if redirect_to:
            redirect_to = redirect_to.lower()
            if not redirect_to.startswith('http://') and not redirect_to.startswith('https://'):
                raise RuntimeError('Invalid redirect_to url %s given' % redirect_to)
        for alias in aliases:
            try:
                self.get_domain(alias)
            except DoesNotExist:
                raise RuntimeError('Domain for alias %s not found' % alias)
        for redirect in redirects:
            try:
                self.get_domain(redirect)
            except DoesNotExist:
                raise RuntimeError('Domain for redirect %s not found' % redirect)
        if not self.username or self.username == '':
            raise RuntimeError('Select username first!')
        vhost = self.Vhost()
        vhost.username = self.username
        vhost.aliases = aliases
        vhost.redirects = redirects
        vhost.name = name
        vhost.redirect_to = redirect_to
        self.session.add(vhost)
        try:
            self.session.commit()
        except IntegrityError or OperationalError as e:
            self.reconnect()
            raise RuntimeError(e)
        return vhost.t_vhosts_id


    def create_vhost(self, addr, reverse=False):
        """"Function to add new vhosts
        addr = address to this domain.
        reverse = if name not specifield use domain as primary address and www.domain as redirect
        """
        if addr.startswith('www.') and not reverse:
            self.add_vhost(addr, redirects=[addr[4:]])
        elif reverse:
            if addr.startswith('www.'):
                addr = addr[4:]
            self.add_vhost(addr, redirects=['www.%s' % addr])
        else:
            self.add_vhost(addr)

    def del_vhost(self,addr):
        """Delete vhost
        addr = vhost address to delete"""
        if addr is not None:
            try:
                vhost = self.get_vhost(addr)
                self.session.delete(vhost)
                self.session.commit()
            except DoesNotExist:
                raise RuntimeError('Vhost %s not found' % addr)

    def get_vhost(self, addr, getall=True):
        """Get vhost object by address
        addr = address
        all = don't limit results to current user vhosts
        """
        try:
            vhost = self.session.query(self.Vhost).filter(self.Vhost.name == addr)
            if self.customer_id and not getall:
                vhost = vhost.filter(self.Vhost.t_customers_id == self.customer_id)
            if self.username and not getall:
                vhost = vhost.filter(self.Vhost.username == self.username)
            retval = vhost.one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            pass
        try:
            vhost = self.session.query(self.Vhost).filter(':alias = ANY (aliases)').params(alias=addr)
            if self.customer_id and not getall:
                vhost = vhost.filter(self.Vhost.t_customers_id == self.customer_id)
            if self.username and not getall:
                vhost = vhost.filter(self.Vhost.username == self.username)
            retval = vhost.one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            pass
        try:
            vhost = self.session.query(self.Vhost).filter(':alias = ANY (redirects)').params(alias=addr)
            if self.customer_id and not getall:
                vhost = vhost.filter(self.Vhost.t_customers_id == self.customer_id)
            if self.username and not getall:
                vhost = vhost.filter(self.Vhost.username == self.username)
            retval = vhost.one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            raise DoesNotExist('Vhost %s not found' % addr)


    def list_vhosts(self, domain=None):
            """Get all user vhost objects
            domain = (optional) limit search to this domain
            """
            vhosts = self.session.query(self.Vhost)
            if self.customer_id:
                vhosts = vhosts.filter(self.Vhost.t_customers_id == self.customer_id)
            if domain:
                try:
                    dom = self.get_domain(domain)
                    vhosts = vhosts.filter(self.Vhost.t_domains_id == dom.t_domains_id)
                except DoesNotExist as e:
                    raise RuntimeError(e)
            retval = vhosts.all()
            self.session.commit()
            return retval

    def add_logaccess(self, addr):
        """Enable vhost logaccess"""
        try:
            vhost = self.get_vhost(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = True
        self.session.commit()
        return True

    def del_logaccess(self, addr):
        """Disable vhost logaccess"""
        try:
            vhost = self.get_vhost(addr)
        except DoesNotExist as e:
            raise RuntimeError(e)
        vhost.logaccess = False
        self.session.commit()
        return True


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

    def list_mailboxes(self, domain=None):
        """List all user mailboxes
        domain = (optional) limit mailboxes to this domain
        Returns list of mailbox objects
        Returns RuntimeError if domain not found"""
        query = self.session.query(self.Mailbox)
        if self.customer_id:
            query = query.filter(self.Mailbox.t_customers_id==self.customer_id)
        if domain:
            try:
                dom = self.get_domain(domain)
            except DoesNotExist as e:
                raise RuntimeError(e)
            query = query.filter(self.Mailbox.t_domains_id == dom.t_domains_id)
        retval = query.all()
        self.session.commit()
        return retval

    def get_mailbox(self, address):
        """Get one mailbox
        address = mailbox address"""
        try:
            query = self.session.query(self.Mailbox).filter(self.Mailbox.name == address)
            if self.customer_id:
                query = query.filter(self.Mailbox.t_customers_id == self.customer_id)
            retval = query.one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            raise DoesNotExist('Mailbox %s not found' % address)
        except MultipleResultsFound:
            self.session.rollback()
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
        except IntegrityError as e:
            self.log.error('Cannot add mailbox %s' % alias)
            self.log.exception(e)
            self.session.rollback()
            raise RuntimeError('Cannot add mailbox')
        return True



    ### mail aliases ###

    def list_mail_aliases(self, domain=None):
        query = self.session.query(self.Mail_aliases)
        if self.customer_id:
            query = query.filter(self.Mail_aliases.t_customers_id == self.customer_id)
        if domain:
            try:
                dom = self.get_domain(domain)
            except DoesNotExist as e:
                raise RuntimeError(e)
            query = query.filter(self.Mail_aliases.t_domains_id == dom.t_domains_id)
        retval = query.all()
        self.session.commit()
        return retval

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
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
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
            self.session.rollback()
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
            self.session.commit()
        except IntegrityError as e:
            raise RuntimeError('Cannot delete mailbox %s, database error')
        return True

    ## User ports ##

    def list_user_ports(self):
        ports = self.session.query(self.User_port)
        if self.customer_id:
            ports = ports.filter(self.User_port.t_customers_id==self.customer_id)
        retval = ports.all()
        self.session.commit()
        return retval

    def get_user_port(self, server, port):
        try:
            port = int(port)
        except ValueError:
            raise RuntimeError('Port must be integer!')
        port = self.session.query(self.User_port).filter(self.User_port.host == server, self.User_port.port == port)
        if self.customer_id:
            port = port.filter(self.User_port.t_customers_id == self.customer_id)
        try:
            retval = port.one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            raise RuntimeError('Port %d on server %s not found' % (port, server))

    def add_user_port(self, server):
        """Open port on given server (server)
        Raises RuntimeError if server not found
        Raises RuntimeError on error
        returns opened port
        """
        try:
           host = self.get_host(server)
        except DoesNotExist:
            raise RuntimeError('Server %s does not found!' % server)
        if not self.username or self.username == '':
            raise RuntimeError('Cannot add port without username')
        port = self.User_port()
        port.t_customers_id = self.customer_id
        port.username = self.username
        port.host = host.host
        self.session.add(port)
        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            self.log.error('Cannot commit to database %s' % e)
            self.log.exception(e)
            raise RuntimeError('Cannot commit to database %s' % e)
        #print("vars: %s" % vars(port))
        return port.port

    def del_user_port(self, server, port):
        port = self.get_user_port(server, port)
        try:
            self.session.delete(port)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            self.log.error('Cannot commit to database %s' % e)
            self.log.exception(e)
            raise RuntimeError('Cannot commit to database %s' % e)

    ### hosts ###

    def get_host(self,host):
        try:
            retval = self.session.query(self.Host).filter(self.Host.host==host).one()
            self.session.commit()
            return retval
        except NoResultFound:
            self.session.rollback()
            raise DoesNotExist('Host %s does not exist' % host)
        except OperationalError:
            self.reconnect()

    def __del__(self):
        try:
            self.session.close()
        except:
            pass


    class Host(object):
        """Host object
        object is mapped to the hosts view"""


    class Domain(object):
        """Domain object
       object is mapped to the domains view"""
        pass


    class Vhost(object):
        """Vhost object
        object mapped to vhosts view"""
        pass

        def __unicode__(self):
            return self.name


    class Vhost_aliases(object):
        """Vhost alias object
        object is mapped to the vhost_aliases view"""
        pass


    class Vhost_redirects(object):
        """Vhost redirect object
        object is mapped to the vhost_redirects view"""
        pass


    class Mailbox(object):
        """Mailbox object
        object is mapped to the mailboxes view"""
        pass


    class Mail_aliases(object):
        """Mail_aliases object
        object is mapped to the mail_aliases view"""
        pass


    class User_port(object):
        """User_port object
        object is mapped to the user_ports view"""
        pass
