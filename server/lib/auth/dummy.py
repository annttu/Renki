# encoding: utf-8

from lib.exceptions import AuthenticationFailed
from lib.utils import generate_key
from lib.auth.authentication import User, Key, AuthenticationModule,\
     PermissionGroup

import random
import string
from hashlib import sha512
from base64 import b64encode, b64decode

"""
Dummy authentication module
"""

dummyAdminGroup = PermissionGroup(name='admin', permissions=['domain_view_all',
                                  'domain_modify_all', 'vhost_view_all',
                                  'vhost_modify_all'])

dummyUserGroup = PermissionGroup(name='user', permissions=['domain_view_own',
                                 'domain_modify_own', 'vhost_view_own',
                                 'vhost_modify_own'])


class DummyUser(User):
    def set_password(self, passwd):
        """
        Generate SHA-512 hash for password and store it
        hash syntax b64encoded "$hash type$salt$hash"
        """
        size = 6
        chars=string.ascii_uppercase + string.digits + string.ascii_lowercase
        salt = ''.join(random.choice(chars) for x in range(size))
        pwhash = sha512(passwd.encode("utf-8"))
        pwhash.update(salt.encode("utf-8"))
        self.password = "$1$%s$%s" % (salt, pwhash.hexdigest())

    def check_password(self, passwd):
        """
        Check if password `passwd` match to user password
        """
        if self.password is None:
            return False
        crap, type_, salt, pwhash = self.password.split('$',3)
        guess = sha512(passwd.encode("utf-8"))
        guess.update(salt.encode("utf-8"))
        guess = guess.hexdigest()
        return guess == pwhash


class DummyAuthenticationModule(AuthenticationModule):
    NAME = "DUMMY"

    def __init__(self):
        self.keys = []

        testuser = DummyUser(user_id=2, username='test', firstnames='Teemu',
                             lastname='Testaaja', groups=[dummyUserGroup])
        testuser.set_password('test')
        adminuser = DummyUser(user_id=1, username='admin', firstnames='Antero',
                              lastname='Ylläpitäjä', groups=[dummyAdminGroup])
        adminuser.set_password('admin')
        self.users = [testuser, adminuser]


    def _find_key(self, key):
        """
        Find right key
        """
        for k in self.keys:
            if k.key == key:
                return k
        return None

    def authenticate(self, username, password):
        """
        Authenticate user using username and password
        returns api key if credentials are correct
        """
        user = self.get_by_username(username)
        if user:
            if user.check_password(password) is True:
                key = Key(generate_key(), user=user)
                self.keys.append(key)
                return key.key
        raise AuthenticationFailed("Invalid username or password")

    def get_user(self, key):
        """
        Get user related to key
        """
        keyObject = self._find_key(key)
        if keyObject is not None:
            return keyObject.get_user()
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

    def get_by_username(self, username):
        """
        Get user object by username
        """
        for user in self.users:
            if user.username == username:
                return user
        return None

    def get_by_user_id(self, user_id):
        """
        Get user object by user_id
        """



