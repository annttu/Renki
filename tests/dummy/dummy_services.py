# encoding: utf-8

"""
This file contains dummy implementatio of Services object to emulate real one.

"""


from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from services.services import Services
from services.libs.database import MySQL, PostgreSQL
from services.libs.domain import Domains
from services.libs.vhost import Vhosts
from services.libs.mail import Mailboxes
from services.libs.user_port import User_ports
from services.libs.host import Hosts
from services.libs.subnet import Subnets
from services.exceptions import DatabaseError, DoesNotExist, PermissionDenied

from dummy_db import *

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class DummyServices(Services):
    """
    Dummy services implementation for unittesting
    """
    def __init__(self, *args, **kwargs):
        super(DummyServices, self).__init__(*args, **kwargs)
        self.login_fail = False
        self.database_fail = False
        self.emulate_admin = False
        if "login_fail" in kwargs:
            self.login_fail = bool(kwargs["login_fail"])
            del kwargs["login_fail"]
        if "database_fail" in kwargs:
            self.database_fail = kwargs["database_fail"]
            del kwargs["database_fail"]
        if "emulate_admin" in kwargs:
            self.emulate_admin = kwargs["emulate_admin"]
            del kwargs["emulate_admin"]

    def login(self):
        """
        Emulate login
        """
        if self.login_fail:
            raise RuntimeError('Invalid login')
        if self.username:
            self.customer_id = self.get_user().t_customers_id

    #def load_modules(self):
    #    self.loaded = True

    def commit_session(self):
        if self.database_fail:
            raise OperationalError('Fake @ commit_session')
        self.session = None

    def connect(self, *args, **kwargs):
        if self.db:
            return
        if self.database_fail:
            raise OperationalError('Fake @ connect')
        self.db = DB()

    def map_objects(self):
        try:
            if self.metadata or self.loaded:
                return True
        except:
            pass
        if self.database_fail:
            return False
        return True

    def getSession(self):
        if self.database_fail:
            raise DatabaseError('Fake: Cannot get session')
        self.session = Session()
        return

    def reconnect(self):
        return

    def get_user(self, username=None):
        customer_id = None
        if not username:
            username = self.username
            customer_id = self.customer_id
            if customer_id != None or username != None:
                return UserView(username=username, admin=self.emulate_admin)
        else:
            return UserView(username=username, admin=False)

