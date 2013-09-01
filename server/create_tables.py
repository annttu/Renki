#!/usr/bin/env python
# encoding: utf-8

import modules

from lib import renki, renki_settings as settings
from lib.database.connection import DBConnection
# Import modules to get all tables registered


import logging
import logging.config

logger = logging.getLogger('create_tables')

if __name__ == '__main__':

    # Run server
    conn = DBConnection(settings.DB_DATABASE, settings.DB_USER,
                        settings.DB_PASSWORD, settings.DB_SERVER,
                        settings.DB_PORT, echo=True)
    logger.info("Creating tables")
    conn.create_tables()
    logger.info("All tables created")
