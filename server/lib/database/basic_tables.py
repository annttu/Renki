from lib.database.table import RenkiDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

class ServerDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'server'
    name = Column('name', String, nullable=False)
    __table_args__ = (UniqueConstraint('name'),)

    def validate(self):
        return True

register_table(ServerDatabase)

class ServiceGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'service_group'
    name = Column("name", String, nullable=False)
    type = Column("type", String, nullable=False)
    __table_args__ = (UniqueConstraint('name'),)
    
    def validate(self):
        return True

register_table(ServiceGroupDatabase)

class ServiceDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'service'
    name = Column("name", String, nullable=False)

    service_group_id = Column(Integer, ForeignKey('service_group.id'))
    service_group = relationship(ServiceGroupDatabase, backref="services")

    server_id = Column(Integer, ForeignKey('server.id'))
    server = relationship(ServerDatabase, backref="services")

    __table_args__ = (UniqueConstraint('name'),)

    def validate(self):
        return True

register_table(ServiceDatabase)

