# encoding: utf-8

from lib.exceptions import AuthenticationFailed


"""
Authentication related modules
"""

class PermissionGroup(object):
    def __init__(self, name, permissions=[]):
        self.name = name
        self.permissions = permissions

    def has_permission(self, perm):
        return perm in self.permissions

    def __str__(self):
        return "PermissionGroup: %s" % self.name

class User(object):
    def __init__(self, user_id, username, firstnames, lastname, groups=[]):
        self.user_id = user_id
        self.username = username
        self.firstnames = firstnames
        self.lastnames = lastname
        self.groups = groups
        self.superuser = False

    def get_full_name(self):
        return self.firstnames + " " + self.lastnames

    def has_permission(self, perm):
        if self.superuser:
            return True
        for group in self.groups:
            if group.has_permission(perm) is True:
                return True
        return False

class Key(object):
    def __init__(self, key, user):
        self.key = key
        self.user = user

    def has_permission(self, permission):
        return self.user.have_permission(permission)

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

    def has_permission(self, key, perm):
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
