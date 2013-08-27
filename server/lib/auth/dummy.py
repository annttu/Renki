# encoding: utf-8

"""
Dummy authentication module
"""

from lib.exceptions import AuthenticationFailed
from lib.utils import generate_key


class Key(object):
    def __init__(self, key, level='USER'):
        self.key = key
        self.level = level

    def has_permission(self, permission):
        if permission == 'USER':
            return self.level in ['USER', 'ADMIN']
        elif permission == 'ADMIN':
            return self.level == 'ADMIN'
        return False


class AuthenticationModule(object):
    NAME = "DUMMY"

    def __init__(self):
        self.keys = []

    def _find_key(self, key):
        """
        Find right key
        """
        for k in self.keys:
            if k.key == key:
                return k
        return None

    def has_perm(self, key, perm):
        """
        Returns True if user has permission perm
        else returns False
        """
        k = self._find_key(key)
        if k:
            return k.has_permission(perm)
        return False

    def valid_key(self, key):
        """
        Dummy key validator
        """
        if self._find_key(key) is not None:
            return True
        return False

    def authenticate(self, username, password):
        """
        Authenticate user using username and password
        returns api key if credentials are correct
        """
        global keys
        if username == 'test' and password == 'test':
            key = Key(generate_key(), level='USER')
            self.keys.append(key)
            return key.key
        elif username == 'admin' and password == 'admin':
            key = Key(generate_key(), level='ADMIN')
            self.keys.append(key)
            return key.key
        raise AuthenticationFailed("Invalid username or password")
