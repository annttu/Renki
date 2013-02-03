#!/usr/bin/env python
# encoding: utf-8
import unittest
from services.tests.dummy.dummy_services import *

import sys
import os

import signal



# unittests_db contains rows
# username = "postgres_username"
# password = "secret"
# server   = "postgresql-server"
# database = "databaseforunittesting"

sys.path.append(os.path.join(os.environ['HOME'], "t"))

import unittests_db as u

class ServicesTestCase(unittest.TestCase):

    customer_id = 65535
    unix_id = 65535
    username = "unittests"

    def stop_handler(self, *args, **kwargs):
        print("Signal")
        f = open("/proc/self/stat", "r")
        pid = f.read().split()[7]
        print("Pid %s")
        c = subprocess.Popen(["kill", "-9", pid])


    def setUp(self):
        signal.signal(signal.SIGALRM, self.stop_handler)
        signal.alarm(10)
        self.srv = DummyServices(username=u.username, password=u.password,
                                 server=u.server, database=u.database)
        self.srv.metadata.create_all(self.srv.db)
        c = self.srv.Customers()
        c.t_customers_id=65535
        c.name="Unittest User"
        self.srv.session.add(c)
        self.srv.safe_commit()
        d = self.srv.Domains()
        d.t_customers_id = c.t_customers_id
        d.name = 'kapsi.fi'
        d.dns = True
        d.t_domains_id = 0
        self.srv.session.add(d)
        self.srv.safe_commit()
        a = self.srv.Users()
        a.t_customers_id = c.t_customers_id
        a.name=c.name
        a.lastname="Unittest"
        a.firstnames="User"
        a.phone=""
        a.unix_id=65535
        a.admin = False
        a.t_domains_id=0
        self.srv.session.add(a)
        self.srv.safe_commit()
        self.local_setup()

    def local_setup(self):
        pass

    def tearDown(self):
        self.srv.safe_commit()
        self.srv.metadata.drop_all(self.srv.db)
        self.local_teardown()
        signal.alarm(0)

    def local_teardown(self):
        pass
