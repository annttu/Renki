# encoding: utf-8

from lib.exceptions import AuthenticationFailed
from hashlib import sha512


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
        self.password = None

    def get_full_name(self):
        return self.firstnames + " " + self.lastnames

    def has_permission(self, perm):
        if self.superuser:
            return True
        for group in self.groups:
            if group.has_permission(perm) is True:
                return True
        return False
    has_perm = has_permission

    def check_password(self, passwd):
        """
        Check if password match to user password
        """
        return False

    def set_password(self, passwd):
        """
        Set user password to password
        """
        pass

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

    def register_user(self, user_id, username, password,
                      firstnames='', lastname=''):
        """
        Create user `username` with user id `user_id` and password `password`
        """
        pass

    def has_permission(self, key, perm):
        """
        Returns True if user has permission perm
        else returns False
        """
        return False

    def valid_key(self, key):
        """
        Dummy key validator
        """
        return False

    def get_user(self, key):
        """
        Get user by authentication key
        """
        return None

    def get_by_user_id(self, user_id):
        """
        Get user object by user_id
        """
        return None

    def get_by_username(self, username):
        """
        Get user object by username
        """
        return None

    def authenticate(self, username, password):
        """
        Dummy authentication function
        """
        raise AuthenticationFailed("Invalid username or password")
