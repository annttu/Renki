#!/usr/bin/env python
# encoding: utf-8

import modules
from lib.database import tables
from lib import renki, renki_settings as settings
from lib.database import connection
#from lib.database.connection import DBConnection
# Import modules to get all tables registered


import logging
import logging.config

logger = logging.getLogger('create_tables')

if __name__ == '__main__':

    # Run server
    conn = connection.DBConnection(settings.DB_DATABASE, settings.DB_USER,
                                   settings.DB_PASSWORD, settings.DB_SERVER,
                                   settings.DB_PORT, echo=True)
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("Creating tables")
    for table in tables.TABLES:
        logger.info("Table: %s" % table.__tablename__)
    conn.create_tables()
    logger.info("All tables created")
