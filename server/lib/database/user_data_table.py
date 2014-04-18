from lib.database.connection import session as dbsession
from lib.history_meta import Versioned
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from lib.database.table import RenkiDataTable
from sqlalchemy.ext.declarative import declared_attr
from lib.communication.ticket_tables import TicketGroupDatabase
from lib.communication.ticket import create_ticket, create_delete_ticket
from lib.exceptions import Invalid, SoftLimitReached, HardLimitReached
from lib.auth.db import Limits, DefaultLimits

class RenkiUserDataTable(RenkiDataTable, Versioned):
    @declared_attr
    def user_id(cls):
        return Column('user_id', Integer, ForeignKey("users.id"), nullable=False)

    waiting = Column('waiting', Boolean, nullable=False, default=False)

    soft_limit = None
    hard_limit = None

    @declared_attr
    def ticket_group_id(cls):
        return Column(Integer, ForeignKey('ticket_group.id'))

    @declared_attr
    def ticket_group(cls):
        return relationship(TicketGroupDatabase)

    def real_save(self, commit=False):
        return RenkiDataTable.save(self, commit)

    def save(self, commit=False):
        create_ticket(self)
        return RenkiDataTable.save(self, commit)

    def delete(self):
        """
        Delete this object from database
        """
        create_delete_ticket(self)
        return RenkiDataTable.delete(self)

    # Needs to be overwritten for tables that don't have service_group_id
    def get_service_group_id(self):
        if 'service_group_id' in self.__table__.columns:
            return self.service_group_id

        raise Invalid("No service_group_id")

    @classmethod
    def get_limits_for_user(cls, user_id):
        limits = {'soft_limit' : cls.soft_limit, 'hard_limit' : cls.hard_limit}

        try:
            defaultLimit = DefaultLimits.query().filter(DefaultLimits.table == cls.__tablename__).one()
            limits = {'soft_limit' : defaultLimit.soft_limit, 'hard_limit' : defaultLimit.hard_limit}
        except NoResultFound:
            pass

        try:
            limit = Limits.query().filter(Limits.table == cls.__tablename__ and Limits.user_id == user_id).one()
            limits = {'soft_limit' : limit.soft_limit, 'hard_limit' : limit.hard_limit}
        except NoResultFound:
            pass

        return limits

    @classmethod
    def count_user_entries(cls, user_id):
        return cls.query().filter(cls.user_id == user_id).count()

    @classmethod
    def validate_add(cls, user, user_id):
        if (user.has_permission('pass_limits')):
            return

        limits = cls.get_limits_for_user(user_id)
        entries = cls.count_user_entries(user_id)
        if entries >= limits['hard_limit']:
            raise HardLimitReached("Hard limit for ports reached")
        elif entries >= limits['soft_limit']:
            raise SoftLimitReached("Soft limit for ports reached")
