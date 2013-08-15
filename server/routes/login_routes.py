#!/usr/bin/env python
# encoding: utf-8

from bottle import request, abort
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error
from lib import renki_settings as settings
from lib.exceptions import AuthenticationFailed


import logging
from functools import wraps
logger = logging.getLogger('routes')


# Authentication decorator
def authenticated(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        key = request.GET.get('key')
        if not key and request.json:
            key = request.json.get('key')
        for mod in settings.AUTHENTICATION_MODULES:
            if mod.valid_key(key):
                return func(*args, **kwargs)
        abort(401, "Invalid API key")
    return wrapped


@app.get('/login/valid')
def login_valid():
    """
    Test if api key is valid
    """
    key = request.GET.get('key', '')
    if not key:
        key = request.json.get('key', '')
    if not key:
        abort(401, "key is mandatory")
    for mod in settings.AUTHENTICATION_MODULES:
        if mod.valid_key(key):
            return ret_ok({'message': 'Key is valid'})
    return ret_error('Key is not valid')


@app.post('/login')
def login_route():
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    if not username or not password:
        username = request.json.get('username', '')
        password = request.json.get('password', '')
    for mod in settings.AUTHENTICATION_MODULES:
        try:
            key = mod.authenticate(username=username, password=password)
            logger.debug("Successfully authenticated user %s" % username)
            return ret_ok({'key': key})
        except AuthenticationFailed:
            pass
    return abort(401, 'Authentication failed')
