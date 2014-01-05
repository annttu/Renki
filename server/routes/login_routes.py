# encoding: utf-8

from bottle import request, abort
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error
from lib import renki_settings as settings
from lib.database import connection
from lib.exceptions import AuthenticationFailed


import logging
logger = logging.getLogger('login_routes')


@app.get('/login/valid')
def login_valid():
    """
    Test if api key is valid
    """
    key = request.GET.get('apikey', '')
    if not key and request.json:
        key = request.json.get('apikey', '')
    if not key:
        abort(401, "API key is mandatory")
    for mod in settings.AUTHENTICATION_MODULES:
        if mod.valid_key(key):
            return ret_ok({'message': 'API key is valid'})
    return ret_error('API key is not valid')


@app.post('/login')
def login_route():
    connection.session.rollback()
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    if not username or not password:
        username = request.json.get('username', '')
        password = request.json.get('password', '')
    for mod in settings.AUTHENTICATION_MODULES:
        try:

            key = mod.authenticate(username=username, password=password)
            connection.session.safe_commit()
            logger.info("User %s has successfully authenticated" % username)
            return ret_ok({'apikey': key})
        except AuthenticationFailed:
            pass
    return abort(401, 'Authentication failed')
