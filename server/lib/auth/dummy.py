# encoding: utf-8

from lib.exceptions import AuthenticationFailed
from lib.utils import generate_key
from lib.auth.authentication import User, Key, AuthenticationModule,\
     PermissionGroup

"""
Dummy authentication module
"""

dummyAdminGroup = PermissionGroup(name='admin', permissions=['domain_view_all',
                                  'domain_modify_all', 'vhost_view_all',
                                  'vhost_modify_all'])

dummyUserGroup = PermissionGroup(name='user', permissions=['domain_view_own',
                                 'domain_modify_own', 'vhost_view_own',
                                 'vhost_modify_own'])


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
            user = User(user_id=2, username=username, firstnames='Teemu',
                        lastname='Testaaja', groups=[dummyUserGroup])
            key = Key(generate_key(), user=user)
            self.keys.append(key)
            return key.key
        elif username == 'admin' and password == 'admin':
            user = User(user_id=1, username=username, firstnames='Antero',
                        lastname='Ylläpitäjä', groups=[dummyAdminGroup])
            key = Key(generate_key(), user=user)
            self.keys.append(key)
            return key.key
        raise AuthenticationFailed("Invalid username or password")
