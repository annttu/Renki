# encoding: utf-8

from bottle import request, abort
from lib import renki_settings as settings
from lib.auth import permissions

import logging
from functools import wraps
logger = logging.getLogger('authentication')


# Authentication decorator
def authenticated(func=None, inject_user=False):
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
                    if inject_user:
                        kwargs['user'] = mod.get_user(key)
                    return func(*args, **kwargs)
            abort(401, "Invalid or missing API key")
        return wrapped
    if not func:
        def normal_wrapped(function):
            return outer_wrapper(function)
        return normal_wrapped
    else:
        return outer_wrapper(func)

auth = authenticated

def require_perm(func=None, permission=None):
    """
    Ensure user has permission `permission`

    Note: This method always injects user to function

    TODO: Read http://bottlepy.org/docs/dev/plugindev.html !!!
    """
    permissions.register_permission(permission)
    def outer_wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            key = get_apikey(request)
            for mod in settings.AUTHENTICATION_MODULES:
                if mod.valid_key(key):
                    user = mod.get_user(key)
                    if not user:
                        logger.error('Bug: Key exist but user not found!')
                        continue
                    if user.has_permission(permission) is not True:
                        abort(403, "Insufficient permissions")
                    kwargs['user'] = user
                    return func(*args, **kwargs)
            abort(401, "Invalid or missing API key")
        return wrapped
    if not func:
        def normal_wrapped(function):
            return outer_wrapper(function)
        return normal_wrapped
    else:
        return outer_wrapper(func)

def get_apikey(request):
    """
    Get apikey from request
    """
    key = request.GET.get('key')
    if not key and request.json:
        key = request.json.get('key')
    return key
