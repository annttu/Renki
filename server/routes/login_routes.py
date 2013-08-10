#!/usr/bin/env python
# encoding: utf-8

from bottle import request, abort
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error
from lib import dummy_authentication as auth
from lib.exceptions import AuthenticationFailed

import logging
logger = logging.getLogger('routes')


# Authentication decorator
def authenticated(func):
    def wrapped(*args, **kwargs):
        key = request.GET.get('key')
        if not key and request.json:
            key = request.json.get('key')
        if auth.valid_key(key):
            return func(*args, **kwargs)
        else:
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
    if auth.valid_key(key):
        return ret_ok({'message': 'Key is valid'})
    return ret_error('Key is not valid')


@app.post('/login')
def login_route():
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    if not username or not password:
        username = request.json.get('username', '')
        password = request.json.get('password', '')
    try:
        key = auth.authenticate(username=username, password=password)
        logger.debug("Successfully authenticated user %s" % username)
        return ret_ok({'key': key})
    except AuthenticationFailed as e:
        return abort(401, e.msg)
