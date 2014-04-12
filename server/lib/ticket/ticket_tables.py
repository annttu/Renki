from lib.database.table import RenkiDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

class TicketGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'ticket_group'
    def validate(self):
        return True

register_table(TicketGroupDatabase)

class TicketDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'ticket'
    data = Column("data", String, nullable=False)
    created = Column("created", DateTime, nullable=False)
    done = Column("done", DateTime, nullable=True)
    ticket_group_id = Column(Integer, ForeignKey('ticket_group.id'))
    ticket_group = relationship(TicketGroupDatabase, backref="ticket_groups")
    def validate(self):
        return True
        
register_table(TicketDatabase)
