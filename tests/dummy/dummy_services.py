# encoding: utf-8

"""
This file contains dummy implementatio of Services object to emulate real one.

"""


from sqlalchemy import *
from sqlalchemy.dialects.postgresql import *
from sqlalchemy import event
from sqlalchemy.orm import mapper, sessionmaker, relationship, clear_mappers
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from services import services
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


class DummyServices(services.Services):
    """
    Dummy services implementation for unittesting
    """
    def __init__(self, *args, **kwargs):
        self.login_fail = False
        self.database_fail = False
        self.emulate_admin = False
        # dynamic load fails on dummy mode
        kwargs['dynamic_load'] = False
        if "login_fail" in kwargs:
            self.login_fail = bool(kwargs["login_fail"])
            del kwargs["login_fail"]
        if "database_fail" in kwargs:
            self.database_fail = kwargs["database_fail"]
            del kwargs["database_fail"]
        if "emulate_admin" in kwargs:
            self.emulate_admin = kwargs["emulate_admin"]
            del kwargs["emulate_admin"]
        super(DummyServices, self).__init__(*args, **kwargs)
        self.login()
        self.metadata.create_all(self.db)


    def load_modules(self):
        """
        Load all submodules
        """
        if self.loaded:
            return
        #self.mysql = MySQL(self)
        #self.postgresql = PostgreSQL(self)
        self.domains = Domains(self)
        #self.vhosts = Vhosts(self)
        #self.mailboxes = Mailboxes(self)
        #self.user_ports = User_ports(self)
        #if self.admin_user:
        #    self.subnets = Subnets(self)
        #    self.hosts = Hosts(self)
        self.loaded = True

    def get_user(self, username=None):
        customer_id = None
        if not username:
            username = self.username
            customer_id = self.customer_id
            if customer_id != None or username != None:
                return UserView(username=username, admin=self.emulate_admin)
        else:
            return UserView(username=username, admin=False)

