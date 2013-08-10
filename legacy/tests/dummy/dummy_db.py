# encoding: utf-8

"""
Dummy database implementation
"""

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError, OperationalError, InvalidRequestError

import logging

logger = logging.getLogger('dummy_db')

class DB(object):
    pass

class Query(object):
    def all(self):
        return []

    def one(self):
        raise NoResultFound('Fake at dummy_db.Query')

    def filter(self, *args, **kwargs):
        pass

class Session(object):
    """
    Dummy sql session object
    """
    def __init__(self):
        self.in_transaction = False

    def query(self, *args, **kwargs):
        """
        Ignore all queries
        """
        if self.in_trasaction:
            InvalidRequestError('Fake: Already on transaction, rollback!')
        self.in_transaction = True
        return Query()

    def add(self, *args, **kwargs):
        return True

    def delete(self, *args, **kwargs):
        return True

    def commit(self):
        if self.in_transaction:
            self.in_transaction = False
        return

    def rollback(self):
        self.in_transaction = False


class UserView(object):
    def __init__(self, username, admin=False):
        self.t_customers_id = 65535
        self.name = u"Unittest User"
        self.lastname = u"Unittest"
        self.firstnames = u"User"
        self.phone = u""
        self.unix_id = 65535
        self.t_users_id = 65535
        self.t_domains_id = 0
        self.admin = admin
