#!/usr/bin/env python
# encoding: utf-8

from .exceptions import Invalid, RenkiHTTPError
from .enums import JSON_STATUS

import threading
from bottle import request


import random
import string

import logging
logger = logging.getLogger('utils')

OK_STATUS = 'OK'
ERROR_STATUS = 'ERROR'
STATUS_CODES = [OK_STATUS, ERROR_STATUS]


def ok(data={}):
    """
    Creates uniform return values for bottle routes

    @param data: Data fields
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.OK
    return data


def error(error, data={}):
    """
    Creates uniform return values for failed api querys

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.ERROR
    data['error'] = error
    return data


def noauth(error="Not Authenticated", data={}):
    """
    Creates uniform return values when user is not authenticated

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.NOAUTH
    data['error'] = error
    return data


def notfound(error="Requested page not found", data={}):
    """
    Creates uniform return values when requested page is not found

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.NOTFOUND
    data['error'] = error
    return data


def notallowed(error="Requested method not allowed", data={}):
    """
    Creates uniform return values when requested method is not allowed

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.NOTALLOWED
    data['error'] = error
    return data


def denied(error="Permission denied", data={}):
    """
    Creates uniform return values when requested method is not allowed

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.DENIED
    data['error'] = error
    return data


def conflict(error="Conflict", data={}):
    """
    Creates uniform return values when requested method is not allowed

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = JSON_STATUS.CONFLICT
    data['error'] = error
    return data


def generate_key(size=30):
    """
    Generate random key
    """
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for x in range(size))

def request_data():
    """
    Get data given by post of put request.
    request variable points always to right context (thread local magic).
    """
    try:
        data = request.json
        if not data:
            if len(request.params) > 100:
                raise Invalid("Too many parameters on input")
            data = dict(request.params.items())
        return data
    except Invalid:
        raise
    except Exception as e:
        logger.exception(e)
    raise Invalid("Invalid input")

def thread_local(name):
    _lctx = threading.local()
    def fget(self):
        try:
            return getattr(_lctx, name)
        except AttributeError:
            raise RuntimeError("Thread context not initialized.")
    def fset(self, value): setattr(_lctx, name, value)
    def fdel(self): delattr(_lctx, name)
    return property(fget, fset, fdel, 'Thread-local property %s' % name)

def sandbox(function, *args, **kwargs):
    """
    Run function with arguments *args **kwargs safely inside try execpt.
    Useful with routes
    """
    try:
        return function(*args, **kwargs)
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
