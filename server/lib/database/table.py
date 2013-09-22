# encoding: utf-8

from lib.exceptions import Invalid, DoesNotExist, DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

import logging
logger = logging.getLogger('modules.repository')


class RenkiTable(object):
    id = Column("id", Integer, primary_key=True, nullable=False)
    _conn = None

    @classmethod
    def query(cls):
        return cls._conn.query(cls)

    @classmethod
    def get(cls, id_):
        if id_:
            try:
                id_ = int(id_)
            except ValueError:
                logger.error("Get with invalid database id %s" % id_)
                raise Invalid('ID must be integer')
            try:
                c = cls._conn.query(cls).filter(
                    cls.id==id_).one()
            except NoResultFound:
                raise DoesNotExist('Object with id %d does not exist' %
                                   id_)
            except SQLAlchemyError as e:
                logger.exception(e)
                raise DatabaseError('Cannot get object with id %d' % id_)
            return c
        raise Invalid('ID must be integer')


    def validate(self):
        """
        Validate this object
        @returns true if object is valid
        @raises Invalid if object is invalid
        """
        raise Invalid("Dummy validator")

    def delete(self, *args, **kwargs):
        """
        Delete this object from database
        """
        self._conn.delete(self)
        return True

    def save(self):
        """
        Save this object to database by updating existing row or inserting
        new one.
        """
        self.validate()
        self._conn.add(self)
        return True

    def as_dict(self):
        """
        Return this object columns as dict object
        """
        ret = {}
        for i in self.__table__.columns.keys():
            if i in ['timestamp']:
                ret[i] = str(getattr(self, i))
            elif i not in ['deleted']:
                ret[i] = getattr(self, i)
        return ret


class RenkiDataTable(RenkiTable):
    # Every data table have comment, deleted and timestamp columns
    comment = Column("comment", String, nullable=False, default='')
    deleted = Column("deleted", Integer, nullable=True, default=None)
    timestamp =   Column("timestamp", DateTime, nullable=False,
                         default=datetime.now)


class RenkiUserDataTable(RenkiDataTable):
    # Every user data table contains waiting column
    waiting = Column("waiting", Boolean, nullable=False, default=False)


# RenkiUserTable contains userid
class RenkiUserTable(RenkiDataTable):
    user_id = Column('user_id', Integer, nullable=False)


metadata = MetaData()
RenkiBase = declarative_base(cls=RenkiTable, metadata=metadata)
