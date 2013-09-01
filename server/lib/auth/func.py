# encoding: utf-8

from bottle import request, abort
from lib import renki_settings as settings

import logging
from functools import wraps
logger = logging.getLogger('authentication')


# Authentication decorator
def authenticated(func=None, injectuser=False):
    """
    Ensure user has authenticated

    @param injectuser: If true, user information is given as request param
    """
    def outer_wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            key = get_apikey(request)
            for mod in settings.AUTHENTICATION_MODULES:
                if mod.valid_key(key):
                    if injectuser:
                        kwargs['user'] = mod.get_user(key)
                    return func(*args, **kwargs)
            abort(401, "Invalid API key")
        return wrapped
    if not func:
        def normal_wrapped(function):
            return outer_wrapper(function)
        return normal_wrapped
    else:
        return outer_wrapper(func)

auth = authenticated


def get_apikey(request):
    """
    Get apikey from request
    """
    key = request.GET.get('key')
    if not key and request.json:
        key = request.json.get('key')
    return key
