# encoding: utf-8

from lib.exceptions import AuthenticationFailed


"""
Authentication related modules
"""


class User(object):
    def __init__(self, userid, username, firstnames, lastname, level='USER'):
        self.userid = userid
        self.username = username
        self.firstnames = firstnames
        self.lastnames = lastname
        self.level = level

    def get_full_name(self):
        return self.firstnames + " " + self.lastnames


class Key(object):
    def __init__(self, key, user):
        self.key = key
        self.user = user

    def has_permission(self, permission):
        if permission == 'USER':
            return self.user.level in ['USER', 'ADMIN']
        elif permission == 'ADMIN':
            return self.user.level == 'ADMIN'
        return False

    def get_user(self):
        return self.user

class AuthenticationModule(object):
    NAME = "NotNamed"

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

    def get_user(self, key):
        """
        Get user related to key
        """
        keyObject = self._find_key(key)
        if keyObject is not None:
            return keyObject.get_user()
        return None

    def authenticate(self, username, password):
        """
        Dummy authentication function
        """
        raise AuthenticationFailed("Invalid username or password")
