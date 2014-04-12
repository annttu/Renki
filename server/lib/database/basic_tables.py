from lib.database.table import RenkiDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

class TicketGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'ticket_group'

register_table(TicketGroupDatabase)

class TicketDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'ticket'
    data = Column("data", String, nullable=False)
    created = Column("created", DateTime, nullable=False)
    done = Column("done", DateTime, nullable=True)
    ticket_group_id = Column(Integer, ForeignKey('ticket_group.id'))
    ticket_group = relationship(TicketGroupDatabase, backref="ticket_groups")

register_table(TicketDatabase)

class ServiceDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'service'
    name = Column("name", String, nullable=False)

    def validate(self):
        return True

register_table(ServiceDatabase)

class ServerGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'server_group'
    name = Column("name", String, nullable=False)
    service_id = Column(Integer, ForeignKey('service.id'))
    service = relationship(ServiceDatabase, backref="server_groups")
    
    def validate(self):
        return True
register_table(ServerGroupDatabase)