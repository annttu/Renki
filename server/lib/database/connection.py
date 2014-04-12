# encoding: utf-8

"""
This file is part of Renki project
"""

from lib.database.tables import TABLES, metadata
from lib.exceptions import DatabaseError
from lib import renki_settings as settings, renki
from lib.history_meta import versioned_session
from lib.utils import thread_local

from sqlalchemy import create_engine
from sqlalchemy.engine import url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

import logging
logger = logging.getLogger('dbconnection')

conn = None

class DBConnection(object):
    def __init__(self, database, username, password, host, port=5432,
                 echo=False):
        """
        Initialize object
        """
        self._database = database
        self._password = password
        self._username = username
        self._host = host
        self._port = port
        self.tables = {}
        self.__engine = None
        self.__metadata = None
        self.__base = None
        self._echo = echo
        logger.info("Connecting to database")
        self._engine.connect()
        self._sessionmaker = None
        self.connect()
        logger.info("Database connection initialized")
        self._register_tables()

    @property
    def _metadata(self):
        if not self.__metadata:
            self._create_metadata()
        return self.__metadata

    @property
    def _base(self):
        if not self.__base:
            self._create_base()
        return self.__base

    @property
    def _engine(self):
        if not self.__engine:
            self._create_engine()
        return self.__engine

    def _create_metadata(self):
        """
        Create SQLAlchemy metadata using same metadata object as with tables.
        """
        self.__metadata = metadata
        # Bind engine to this connection
        self.__metadata._bind_to(self._engine)

    def create_session(self):
        """
        Initialize session
        """
        if self._sessionmaker is None:
            self._sessionmaker = sessionmaker(bind=self._engine,
                                              autocommit=False)
            versioned_session(self._sessionmaker)
        return self._sessionmaker()

    def _create_engine(self):
        """
        Initialize engine
        """
        dburl = url.URL('postgres',
                        username=self._username, password=self._password,
                        host=self._host, database=self._database,
                        port=self._port)
        # Note: pool_size defines the number of connections to keep open
        # inside the connection pool.
        self.__engine = create_engine(dburl, echo=self._echo, pool_timeout=10,
                                      pool_size=5)


    def _register_tables(self):
        """
        Register this connection to all databases
        """
        for table in TABLES:
            table._conn = self

    def connect(self):
        """
        Connect to database
        """
        self._create_engine()
        self._create_metadata()

    def create_tables(self):
        """
        Create all tables
        """
        self._metadata.create_all()

    def drop_tables(self):
        """
        Drop all tables
        """
        self._metadata.drop_all()

    def register_table(self, table, name=None):
        """
        Initialize and add table to this database connection

        @param table: Table to add
        @type table: object
        @param initializer: TableInitializer
        @type initializer: Class or function
        """
        if not name:
            name = str(table.__name__)
        table.parent = self
        self.tables[name] = table
        if name not in vars(self):
            logger.debug('Registering table %s' % name)
            setattr(DBConnection, name, table)

    def __str__(self):
        return 'DBConnection <%s@%s/%s>' % (self._username, self._host,
                                              self._database)

    def __repr__(self):
        return self.__str__()


class LocalDBSession(object):
    """
    Thread-local session object.
    """
    _session = thread_local(name="session")

    def query(self, *args, **kwargs):
        ses = self.session()
        return ses.query(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self.session().add(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.session().delete(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return self.session().flush(*args, **kwargs)

    def session(self):
        try:
            return self._session
        except RuntimeError:
            ses = conn.create_session()
            self._session = ses
        return self._session

    def commit(self, *args, **kwargs):
        ses = self.session()
        try:
           xid = ses.query(func.txid_current()).first()
           logger.info("Transaction id: %s" % xid)
           logger.debug("Commit")
        except Exception as e:
            logger.exception(e)
        return ses.commit(*args, **kwargs)

    def safe_commit(self, *args, **kwargs):
        try:
            self.commit(*args, **kwargs)
            return True
        except Exception as e:
            logger.error(e)
            logger.debug("Rollback")
            self.rollback()
        raise DatabaseError("Cannot save changes")

    def rollback(self, *args, **kwargs):
        """
        Rollback session
        """
        return self.session().rollback(*args, **kwargs)

session = LocalDBSession()

def initialize_connection(unittest=False, echo=False):
    """
    Create global database connection
    """
    global conn
    if unittest:
        logger.info("Using unittest database credentials")
        conn = DBConnection(settings.DB_TEST_DATABASE, settings.DB_TEST_USER,
                            settings.DB_TEST_PASSWORD, settings.DB_TEST_SERVER,
                            settings.DB_TEST_PORT, echo=echo)
    else:
        conn = DBConnection(settings.DB_DATABASE, settings.DB_USER,
                            settings.DB_PASSWORD, settings.DB_SERVER,
                            settings.DB_PORT, echo=echo)
    # Add forced commit hook
    @renki.app.hook('after_request')
    def force_commit():
        # Note: this isn't probably good idea
        # If commit fails, data already sent to user, is lost.
        try:
            session.safe_commit()
        except Exception as e:
            logger.exception(e)
