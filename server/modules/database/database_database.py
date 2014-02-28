# encoding: utf-8

from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, types, ForeignKey, UniqueConstraint

class DatabaseDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'database'

    name = Column('name', String(512), nullable=False)
    server_group_id = Column('server_group_id', Integer, ForeignKey('server_group.id'), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey('server_group.id'), nullable=False)
    type = Column('type', types.Enum('mysql', 'postgresql', name='database_types', native_enum=True), nullable=False)

    __table_args__ = (UniqueConstraint('server_group_id', 'name', 'type'),)

    def validate(self):
        if len(self.name) > 50:
            raise Invalid('Database name too long')
        return True

register_table(DatabaseDatabase)
