# encoding: utf-8

from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, types, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from lib.database.basic_tables import ServiceGroupDatabase

class DatabaseDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'database'

    name = Column('name', String(512), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey("users.id"), nullable=False)
    type = Column('type', types.Enum('mysql', 'postgresql', name='database_types', native_enum=True), nullable=False)
    service_group_id = Column(Integer, ForeignKey('service_group.id'))
    service_group = relationship(ServiceGroupDatabase, backref="databasis")
    __table_args__ = (UniqueConstraint('service_group_id', 'name', 'type'),)

    def validate(self):
        if len(self.name) > 50:
            raise Invalid('Database name too long')
        return True

register_table(DatabaseDatabase)
