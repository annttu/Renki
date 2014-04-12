from lib.exceptions import Invalid, DoesNotExist, DatabaseError
from lib.database.connection import session as dbsession
from lib.database.tables import metadata
from lib.history_meta import Versioned
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from lib.database.table import RenkiDataTable

class RenkiUserDataTable(RenkiDataTable, Versioned):
    # Every user data table contains waiting column
    waiting = Column("waiting", Boolean, nullable=False, default=False)
    ticketgroup = ForeignKey("TicketGroup", backref="ticket_group")
