# encoding: utf-8

"""
Dummy authentication module
"""

from .exceptions import AuthenticationFailed

import random
import string


keys = []


def generate_key(size=30):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for x in range(size))


def valid_key(key):
    """
    Dummy key validator
    """
    global keys
    if key in keys:
        return True
    return False


def authenticate(username, password):
    """
    Authenticate user using username and password
    returns api key if credentials are correct
    """
    global keys
    if username == 'test' and password == 'test':
        key = generate_key()
        keys.append(key)
        return key
    raise AuthenticationFailed("Invalid username or password")
