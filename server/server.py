#!/usr/bin/env python
# encoding: utf-8

from lib import check_settings
from lib import renki, renki_settings as settings
from lib.database.connection import initialize_connection, session
from lib.history_meta import versioned_session

# Importing routes and modules registers also tables
import lib.auth.db
import routes
import modules

from bottle import run
import logging

if __name__ == '__main__':
    check_settings.set_settings()
    logger = logging.getLogger('server')
    # Run server
    logger.info("Starting server")
    initialize_connection()
    versioned_session(session.session())
    run(renki.app, host=settings.BIND_HOST, port=settings.BIND_PORT,
        debug=settings.DEBUG, reloader=True)
    logger.info("Server stopped")
