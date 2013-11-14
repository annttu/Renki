#!/usr/bin/env python
# encoding: utf-8

import unittest

from lib.database import connection
from lib.database.connection import session as dbsession
from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from sqlalchemy import Column, String
from time import sleep

from threading import Thread
import threading
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



class SimpleTable(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'test_table1'
    col_1 = Column('col_1', String(1024), nullable=False)

register_table(SimpleTable)


connection.initialize_connection(unittest=True, echo=False)

class Worker(Thread):
    def __init__(self, string, sleep, commit=True):
        Thread.__init__(self)
        self.string = string
        self.sleep = sleep
        self.commit = commit

    def run(self):
        print(vars(threading.local()))
        s = SimpleTable()
        s.col_1 = self.string
        dbsession.add(s)
        sleep(self.sleep)
        if self.commit:
            dbsession.commit()
        else:
            dbsession.rollback()

class TestThreadLocality(unittest.TestCase):
    def setUp(self):
        connection.conn.create_tables()

    def tearDown(self):
        dbsession.rollback()
        connection.conn.drop_tables()

    def test_rollback_commit(self):
        w1 = Worker('Worker_1', sleep=1, commit=True)
        w2 = Worker('Worker_2', sleep=0.5, commit=False)
        w1.start()
        w2.start()
        print("Joining threads")
        w2.join()
        print("W2 thread joined")
        w1.join()
        print("W1 thread joined")
        print("Query initialized")
        items = SimpleTable.query().all()
        self.assertTrue(len(items) == 1,
                        "Test produced wrong count (%s) of items to database" % len(items))
        for item in items:
            if item.col_1 != 'Worker_1':
                self.fail("Wrong/Unknown object inserted to database")


    def test_commit_rollback(self):
        w1 = Worker('Worker_1', sleep=0.5, commit=True)
        w2 = Worker('Worker_2', sleep=1, commit=False)
        w1.start()
        w2.start()
        print("Joining threads")
        w1.join()
        print("W1 thread joined")
        w2.join()
        print("W2 thread joined")
        items = SimpleTable.query().all()
        self.assertTrue(len(items) == 1,
                        "Test produced wrong count (%s) of items to database" % len(items))
        print("Length tested")
        for item in items:
            if item.col_1 != 'Worker_1':
                self.fail("Wrong/Unknown object inserted to database")
        print("Test done")

if __name__ == '__main__':
    unittest.main()
