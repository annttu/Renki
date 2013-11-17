# encoding: utf-8

from lib.utils import generate_key
from lib.auth.authentication import AuthenticationModule
from lib.auth import db
from lib.exceptions import DoesNotExist, AuthenticationFailed

from sqlalchemy.exc import SQLAlchemyError

import logging


logger = logging.getLogger('BasicAuthentication')

"""
Basic authentication module
"""


class BasicAuthenticationModule(AuthenticationModule):
    NAME = "BASIC"

    def __init__(self):
        pass


    def _find_key(self, key):
        """
        Find right key
        """
        try:
            return db.AuthKeys.get_key(key)
        except DoesNotExist:
            return None

    def register_user(self, user_id, username, password,
                      firstnames='', lastname=''):
        user = db.Users()
        user.id = user_id
        user.name = username
        user.set_password(password)
        user.firstnames = firstnames
        user.lastname = lastname
        user.save()

    def authenticate(self, username, password):
        """
        Authenticate user using username and password
        returns api key if credentials are correct
        """
        user = self.get_by_username(username)
        if user:
            if user.check_password(password) is True:
                apikey = generate_key()
                db.AuthKeys.add_key(user=user, key=apikey)
                return apikey
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
        try:
            user = db.Users.query().filter(db.Users.name == username).one()
        except SQLAlchemyError as e:
            logger.exception(e)
            raise AuthenticationFailed("User '%s' does not exist" % username)
        return user

    def get_by_user_id(self, user_id):
        """
        Get user object by user_id
        """
        try:
            user = db.Users.query().filter(db.Users.id == user_id).one()
        except SQLAlchemyError as e:
            logger.exception(e)
            raise AuthenticationFailed("User with id '%s' does not exist" %
                                       user_id)
        return user


