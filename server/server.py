#!/usr/bin/env python
# encoding: utf-8

from lib import renki, renki_settings as settings
from lib.database.connection import DBConnection
import routes
import modules

from bottle import run
import logging
import logging.config

if __name__ == '__main__':
    logger = logging.getLogger('server')
    # Run server
    logger.info("Starting server")
    conn = DBConnection(settings.DB_DATABASE, settings.DB_USER,
                        settings.DB_PASSWORD, settings.DB_SERVER,
                        settings.DB_PORT, echo=False)
    run(renki.app, host=settings.BIND_HOST, port=settings.BIND_PORT,
        debug=settings.DEBUG, reloader=True)
    logger.info("Server stopped")
