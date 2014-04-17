from lib.database.connection import session as dbsession
from lib.database.tables import metadata
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

class RenkiUserDataTable(RenkiDataTable, Versioned):
    # Every user data table contains waiting column
    waiting = Column("waiting", Boolean, nullable=False, default=False)

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
