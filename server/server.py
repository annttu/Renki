#!/usr/bin/env python
# encoding: utf-8

from lib import renki, renki_settings as settings
from lib.database.connection import initialize_connection
import routes
import modules

from bottle import run
import logging

if __name__ == '__main__':
    logger = logging.getLogger('server')
    # Run server
    logger.info("Starting server")
    initialize_connection()
    run(renki.app, host=settings.BIND_HOST, port=settings.BIND_PORT,
        debug=settings.DEBUG, reloader=True)
    logger.info("Server stopped")
