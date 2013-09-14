# encoding: utf-8

"""
This file is part of Renki project
"""

from .tables import TABLES
from .table import metadata
from lib import renki_settings as settings, renki


from sqlalchemy import create_engine
from sqlalchemy.engine import url
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import sessionmaker

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
        self.__session = None
        self.__metadata = None
        self.__base = None
        self._echo = echo
        logger.info("Connecting to database")
        self.connect()
        self._engine.connect()
        logger.info("Database connection initialized")
        self._register_tables()

    @property
    def _session(self):
        if not self.__session:
            self._create_session()
        return self.__session

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

    @property
    def query(self):
        return self._session.query

    @property
    def add(self):
        return self._session.add

    @property
    def commit(self):
        return self._session.commit

    @property
    def rollback(self):
        """
        Rollback session
        """
        return self._session.rollback

    def _create_metadata(self):
        """
        Create SQLAlchemy metadata using same metadata object as with tables.
        """
        self.__metadata = metadata
        # Bind engine to this connection
        self.__metadata._bind_to(self._engine)

    def _create_session(self):
        """
        Initialize session
        """
        Session = sessionmaker(bind=self._engine, autocommit=False)
        self.__session = Session()

    def _create_engine(self):
        """
        Initialize engine
        """
        dburl = url.URL('postgres',
                        username=self._username, password=self._password,
                        host=self._host, database=self._database,
                        port=self._port)
        self.__engine = create_engine(dburl, echo=self._echo, pool_timeout=10)

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
        self._create_session()


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

def initialize_connection():
    """
    Create global database connection
    """
    global conn
    conn = DBConnection(settings.DB_DATABASE, settings.DB_USER,
                        settings.DB_PASSWORD, settings.DB_SERVER,
                        settings.DB_PORT, echo=False)
    # Add forced commit hook
    @renki.app.hook('after_request')
    def force_commit():
        conn.commit()
