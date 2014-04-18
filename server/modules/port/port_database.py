# encoding: utf-8

from lib.database.user_data_table import RenkiUserDataTable
from lib.database.table import RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from lib.database.basic_tables import ServiceGroupDatabase

class PortDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'port'
    port = Column('port', Integer, nullable=False)
    service_group_id = Column(Integer, ForeignKey('service_group.id'))
    service_group = relationship(ServiceGroupDatabase, backref="ports")
    __table_args__ = (UniqueConstraint('service_group_id', 'port'),)

    soft_limit = 5
    hard_limit = 10
    
    def validate(self):
        return True

# Register table
register_table(PortDatabase)
