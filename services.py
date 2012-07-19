# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy.dialects.postgresql import *
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.orm import mapper, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging
from services import defaults

from services.libs.database import MySQL, PostgreSQL
from services.libs.domain import Domains
from services.libs.vhost import Vhosts
from services.libs.mail import Mailboxes
from services.libs.user_port import User_ports
from services.libs.host import Hosts
from services.libs.subnet import Subnets
from services.exceptions import DatabaseError, DoesNotExist, PermissionDenied

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)



def on_connect_listener(target, context):
    log = logging.getLogger('services')
    log.debug("Reconnecting to database...")

def on_first_connect_listener(target, context):
    log = logging.getLogger('services')
    log.info("Connecting to database...")

class Services():
    def __init__(self, username, password, server, verbose=False, database='services', dynamic_load=True):
        self.db = None
        self.dynamic_load = dynamic_load
        self.database = database
        self.db_username = username
        self.db_password = password
        self.server=server
        self.verbose = verbose
        self.defaults = defaults
        self.metadata = None
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
        self.postgresql = PostgreSQL(self)
        self.domains = Domains(self)
        self.vhosts = Vhosts(self)
        self.mailboxes = Mailboxes(self)
        self.user_ports = User_ports(self)
        if self.admin_user:
            self.hosts = Hosts(self)
            self.subnets = Subnets(self)


    def connect(self, database=None,user=None,password=None,server=None, port=None):
        self.db = create_engine('postgresql://%s:%s@%s/%s' % (self.db_username, self.db_password, self.server, self.database),
                                encoding='utf-8', echo=self.verbose, pool_recycle=60)

    def getSession(self):
        """Function to get session"""
        try:
            metadata = MetaData(self.db)
            self.metadata = metadata
            ## map tables to
            event.listen(Pool, 'first_connect', on_first_connect_listener)
            customers = Table('customers', metadata,
                Column("t_customers_id", Integer, primary_key=True),
                Column('name', String, nullable=False),
                Column('masters', ARRAY(TEXT())))
                #,
                #autoload=True)
            mapper(self.Customers, customers)
            domains = Table('domains', self.metadata,
                Column("t_domains_id", Integer, primary_key=True),
                Column("name", String,nullable=False),
                Column('shared', Boolean, nullable=False, default='false'),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id'), nullable=False),
                Column('dns', Boolean, nullable=False),
                Column('refresh_time', Integer, nullable=False, default=text('28800')),
                Column('retry_time', Integer, nullable=False, default=text('7200')),
                Column('expire_time', Integer, nullable=False, default=text('1209600')),
                Column('minimum_cache_time', Integer, nullable=False, default=text('21600')),
                Column('ttl', Integer, nullable=False, default=text('10800')),
                Column('admin_address', String, nullable=True),
                Column('domain_type', Enum('MASTER', 'SLAVE', 'NONE'), primary_key=False, nullable=False, default=text("'MASTER'::domain_type")),
                Column('masters', ARRAY(INET()), primary_key=False),
                Column('allow_transfer', ARRAY(INET()), primary_key=False))
                #autoload=True)
            mapper(self.Domains, domains, properties={
                'customer': relationship(self.Customers, backref='domains'),
            })
            users = Table('users', metadata,
                Column("t_users_id", Integer, primary_key=True),
                Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
                Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
                Column('name', String, nullable=False),
                Column('lastname', String, nullable=False),
                Column('firstnames', String, nullable=False),
                Column('phone', String, nullable=False),
                Column('unix_id', Integer, nullable=True),
                Column('admin', Boolean, nullable=True))
                #,autoload=True)
            mapper(self.Users, users, properties={
                'customer': relationship(self.Customers, backref='users'),
                'domain': relationship(self.Domains, backref='users')
                })
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
        alias_list = []
        query = self.session.query(self.Customers.aliases,self.Users.name).join(self.Users, self.Customers.t_customers_id == self.Users.t_customers_id)
        if user is not None:
            query = query.filter(self.Users.name == user)
        elif self.customer_id is not None:
            query = query.filter(self.Users.t_customers_id == self.customer_id)
        else:
            raise RuntimeError('Give either user or customer_id')
        try:
            retvals = query.all()
            if len(retvals) < 1:
                raise RuntimeError('Cannot get alias list')
            for retval in retvals:
                user = retval.name
                alias_list += [alias for alias in retval.aliases if alias is not None]
                alias_list += [user]
            self.session.commit()
            return alias_list
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


    class Users(object):
        """Users object
        mapped to users view
        self.customer contains Customers object"""


    class Customers(object):
        """Customers object
        mapped to customers view"""


    class Vhosts(object):
        """Vhost object
        object mapped to vhosts view"""


    class Vhost_aliases(object):
        """Vhost alias object
        object is mapped to the vhost_aliases view"""


    class Vhost_redirects(object):
        """Vhost redirect object
        object is mapped to the vhost_redirects view"""


    class Mailboxes(object):
        """Mailboxes object
        object is mapped to the mailboxes view"""


    class Mail_aliases(object):
        """Mail_aliases object
        object is mapped to the mail_aliases view"""


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


    class Database_servers(object):
        """Database_servers object
        mapped to database_servers view"""


    class Subnets(object):
        """Subnets object
        mapped to t_subnets table"""


    class Addresses(object):
        """Mapped to t_addresses table"""


    class Hosts(object):
        """Mapped to t_hosts table"""