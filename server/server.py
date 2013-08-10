#!/usr/bin/env python
# encoding: utf-8

from lib import renki
import settings
import routes

from bottle import run
import logging
import logging.config

if __name__ == '__main__':
    logging.config.dictConfig(settings.LOGGING)
    logger = logging.getLogger('server')
    # Run server
    logger.info("Starting server")
    run(renki.app, host=settings.HOST, port=settings.PORT,
        debug=settings.DEBUG, reloader=True)
    logger.info("Server stopped")
