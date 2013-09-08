# encoding: utf-8

from lib.exceptions import Invalid, DoesNotExist, DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy import Column, Integer
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

import logging
logger = logging.getLogger('modules.repository')


class RenkiTable(object):
    id = Column(Integer(), primary_key=True, nullable=False)
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
        return True

    def save(self):
        """
        Save this object to database by updating existing row or inserting
        new one.
        """
        self.validate()
        return True

    def as_dict(self):
        """
        Return this object columns as dict object
        """
        ret = {}
        for i in self.__table__.columns.keys():
            ret[i] = getattr(self, i)
        return ret

# RenkiUserTable contains userid

class RenkiUserTable(RenkiTable):
    userid = Column('userid', Integer, nullable=False)


metadata = MetaData()
RenkiBase = declarative_base(cls=RenkiTable, metadata=metadata)
