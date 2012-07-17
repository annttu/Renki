# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.orm import mapper, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging


from database import MySQL, PostgreSQL
from domain import Domains
from vhost import Vhosts
from mailbox import Mailboxes
from user_port import User_ports
from host import Hosts

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from exceptions import DatabaseError, DoesNotExist, PermissionDenied

def on_connect_listener(target, context):
    log = logging.getLogger('services')
    log.debug("Reconnecting to database...")

def on_first_connect_listener(target, context):
    log = logging.getLogger('services')
    log.info("Connecting to database...")

class Services():
    def __init__(self, username, password, server, verbose=False, database='services'):
        self.db = None
        self.database = database
        self.db_username = username
        self.db_password = password
        self.server=server
        self.verbose = verbose
        if self.verbose:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        else:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
        self.log = logging.getLogger('services')
        self.connect()
        self.customer_id = None
        self.username = None
        self.session = None
        self.admin_user = False
        self.getSession()
        if not self.session:
            raise RuntimeError('Invalid login')
        self.db_password = None
        self.mysql = MySQL(self)
        self.domains = Domains(self)
        self.vhosts = Vhosts(self)
        self.mailboxes = Mailboxes(self)
        self.user_ports = User_ports(self)
        self.hosts = Hosts(self)

    def connect(self, database=None,user=None,password=None,server=None, port=None):
        self.db = create_engine('postgresql://%s:%s@%s/%s' % (self.db_username, self.db_password, self.server, self.database),
                                encoding='utf-8', echo=self.verbose, pool_recycle=60)

    def getSession(self):
        """Function to get session"""
        try:
            metadata = MetaData(self.db)
            ## map tables to
            event.listen(Pool, 'first_connect', on_first_connect_listener)
            domains = Table('domains', metadata,
                Column("t_domains_id", Integer, primary_key=True), autoload=True)
            mapper(self.Domains, domains)
            customers = Table('customers', metadata,
                Column("t_customers_id", Integer, primary_key=True), autoload=True)
            mapper(self.Customers, customers)
            users = Table('users', metadata,
                Column("t_users_id", Integer, primary_key=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                autoload=True)
            mapper(self.Users, users, properties={
                'customer': relationship(self.Customers, backref='users'),
                'domain': relationship(self.Domains, backref='users')
                })
            vhosts = Table('vhosts', metadata,
                Column("t_vhosts_id", Integer, primary_key=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                Column("t_users_id", Integer, ForeignKey('users.t_users_id')),
                autoload=True)
            mapper(self.Vhosts, vhosts, properties={
                'customer': relationship(self.Customers, backref='vhosts'),
                'domain': relationship(self.Domains, backref='vhosts'),
                'user': relationship(self.Users, backref='vhosts')
                })
            vhost_aliases = Table('vhost_aliases', metadata,
                Column("t_vhosts_id", Integer, primary_key=True),
                Column("parent_id", Integer, ForeignKey('vhosts.t_vhosts_id')),
                autoload=True)
            mapper(self.Vhost_aliases, vhost_aliases, properties={
                'vhost': relationship(self.Vhosts, backref='vhost_aliases')
            })
            vhost_redirects = Table('vhost_redirects', metadata,
                Column("t_vhosts_id", Integer, primary_key=True),
                Column("parent_id", Integer, ForeignKey('vhosts.t_vhosts_id')),
                autoload=True)
            mapper(self.Vhost_redirects, vhost_redirects, properties={
                'vhost': relationship(self.Vhosts, backref='vhost_redirects')
            })
            mailbox = Table('mailboxes', metadata,
                Column("t_mailboxes_id", Integer, primary_key=True),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                autoload=True)
            mapper(self.Mailboxes, mailbox, properties={
                'customer': relationship(self.Customers, backref='mailboxes'),
                'domain': relationship(self.Domains, backref='mailboxes')
            })
            mail_aliases = Table('mail_aliases', metadata,
                Column('t_mail_aliases_id', Integer, primary_key=True),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_mailboxes_id", Integer, ForeignKey('mailboxes.t_mailboxes_id')),
                autoload=True)
            mapper(self.Mail_aliases, mail_aliases, properties={
                'customer': relationship(self.Customers, backref='mail_aliases'),
                'domain': relationship(self.Domains, backref='mail_aliases'),
                'mailbox': relationship(self.Mailboxes, backref='mail_aliases')
            })
            user_ports = Table('user_ports', metadata,
                Column('t_user_ports_id', Integer, primary_key=True),
                Column('active', Boolean, default=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_users_id", Integer, ForeignKey('users.t_users_id')),
                autoload=True)
            mapper(self.User_ports, user_ports, properties={
                'customer': relationship(self.Customers, backref='user_ports'),
                'user': relationship(self.Users, backref='user_ports'),
            })
            user_port_servers = Table('user_port_servers', metadata,
                Column("t_services_id", Integer, primary_key=True), autoload=True)
            mapper(self.User_port_servers, user_port_servers)
            databases = Table('databases', metadata,
                Column("t_databases_id", Integer, primary_key=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                autoload=True)
            mapper(self.Databases, databases, properties={
                'customer': relationship(self.Customers, backref='databases')
            })
            database_servers = Table('database_servers', metadata,
                Column("t_services_id", Integer, primary_key=True), autoload=True)
            mapper(self.Database_servers, database_servers)
            Session = sessionmaker(bind=self.db)
            self.session = Session()
            self.admin_user = self.is_admin(self.username)
            event.listen(Pool, 'connect', on_connect_listener)
        except OperationalError as e:
            self.log.exception(e)
            self.session = None

    def reconnect(self):
        self.session.rollback()

    ###########
    ## Users ##
    ###########

    def require_admin(self):
        if self.is_admin(self.db_username) is False:
            raise PermissionDenied('Insufficient permissions')
        return True

    def list_users(self):
        """List all users"""
        users = self.session.query(self.Users)
        try:
            users = users.all()
            self.session.commit()
            return users
        except Exception as e:
            self.log.exception(e)
            self.session.rollback()
            raise RuntimeError('Cannot get users')
        except:
            self.session.rollback()
            raise RuntimeError('Cannot get users')

    def get_current_user(self):
        """Get current selected user
        Raises DoesNotExist if no user found
        Raises RuntimeError on error"""
        if self.customer_id != None and self.username != None:
            user = self.session.query(self.Users).filter(self.Users.customers_id == self.customer_id)
            user = user.filter(self.Users.name == self.username)
            try:
                user = user.one()
                self.session.commit()
                return user
            except NoResultsFound:
                raise DoesNotExist('No user %s found' % self.username)
            except Exception as e:
                self.log.exception(e)
                self.session.rollback()
                raise RuntimeError('Cannot get current user, database error')
            except:
                self.session.rollback()
                raise RuntimeError('Cannot get current user, database error')
        else:
            raise RuntimeError('Select user first')

    def is_admin(self,username=None):
        """Test if user is admin user"""
        if username is None:
            username = self.db_username
        try:
            retval = self.session.query(self.Users).filter(self.Users.name == username).one()
            self.session.commit()
            return retval.admin
        except NoResultFound:
            self.session.rollback()
            raise DoesNotExist('User %s does not exist' % username)
        except:
            self.session.rollback()
            self.reconnect()
        try:
            retval = self.session.query(self.Users).filter(self.Users.name == username).one()
            self.session.commit()
            return retval.admin
        except Exception as e:
            self.log.exception(e)
        except:
            pass
        raise RuntimeError('Cannot get user %s, database error' % username)
        return False

    def list_aliases(self,user=None):
        """List <username> aliases"""
        query = self.session.query(self.Customers.aliases,self.Users.name).join(self.Users, self.Customers.t_customers_id == self.Users.t_customers_id)
        if user is not None:
            query = query.filter(self.Users.name == user)
        elif self.customer_id is not None:
            query = query.filter(self.Users.t_customers_id == self.customer_id)
        else:
            raise RuntimeError('Give either user or customer_id')
        try:
            retval = query.one()
            user = retval.name
            retval = [alias for alias in retval.aliases if alias is not None]
            retval += [user]
            self.session.commit()
            return retval
        except NoResultFound:
            if user is not None:
                return DoesNotExist('User %s does not exist' % user)
            else:
                return DoesNotExist('Customer %s does not exist' % self.customer_id)
        except Exception as e:
            self.log.exception(e)
            self.session.rollback()
            raise RuntimeError('Cannot get aliass list')
        except:
            self.session.rollback(e)
            self.log.error('Unknown error while getting aliases list')
            raise RuntimeError('Cannot get aliass list')

    def get_username(self):
        """Get username by t_customers_id"""
        if not self.customer_id:
            raise RuntimeError('Select user first')
        try:
            query = self.session.query(self.Users.name).filter(self.Users.t_customers_id == self.customer_id).one()
        except NoResultFound:
            raise DoesNotExist('User for customer_id %s does not found' % self.customer_id)

    def require_alias(self,alias):
        """Check if there is alias row for <alias>"""
        if self.customer_id is None:
            raise RuntimeError('Select user first')
        aliases = self.list_aliases()
        if alias in aliases:
            return True
        raise RuntimeError('Alias %s not found' % alias)

    def __del__(self):
        try:
            self.session.close()
        except:
            pass


    class Domains(object):
        """Domain object
        object is mapped to the domains view"""
        pass


    class Users(object):
        """Users object
        mapped to users view
        self.customer contains Customers object"""
        pass

    class Customers(object):
        """Customers object
        mapped to customers view"""
        pass

    class Vhosts(object):
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


    class Mailboxes(object):
        """Mailboxes object
        object is mapped to the mailboxes view"""
        pass


    class Mail_aliases(object):
        """Mail_aliases object
        object is mapped to the mail_aliases view"""
        pass


    class User_port_servers(object):
        """User_port_servers object
        object is mapped to the user_port_server view"""


    class User_ports(object):
        """User_port object
        object is mapped to the user_ports view"""
        pass

    class Databases(object):
        """Databases object
        mapped to databases view"""
        pass


    class Database_servers(object):
        """Database_servers object
        mapped to database_servers view"""
        pass