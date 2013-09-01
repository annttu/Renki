# encoding: utf-8

from lib.exceptions import AuthenticationFailed
from lib.utils import generate_key
from lib.auth.authentication import User, Key, AuthenticationModule

"""
Dummy authentication module
"""

class DummyAuthenticationModule(AuthenticationModule):
    NAME = "DUMMY"

    def __init__(self):
        self.keys = []

    def authenticate(self, username, password):
        """
        Authenticate user using username and password
        returns api key if credentials are correct
        """
        if username == 'test' and password == 'test':
            user = User(userid=2, username=username, firstnames='Teemu',
                        lastname='Testaaja', level='USER')
            key = Key(generate_key(), user=user)
            self.keys.append(key)
            return key.key
        elif username == 'admin' and password == 'admin':
            user = User(userid=1, username=username, firstnames='Antero',
                        lastname='Ylläpitäjä', level='ADMIN')
            key = Key(generate_key(), user=user)
            self.keys.append(key)
            return key.key
        raise AuthenticationFailed("Invalid username or password")
