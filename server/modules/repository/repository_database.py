# encoding: utf-8

from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, types, ForeignKey, UniqueConstraint

class RepositoryDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'repository'

    name = Column('name', String(512), nullable=False)
    server_group_id = Column('server_group_id', Integer, ForeignKey('server_group.id'), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey('server_group.id'), nullable=False)
    type = Column('type', types.Enum('git', 'svn', name='repository_types', native_enum=True), nullable=False)

    __table_args__ = (UniqueConstraint('server_group_id', 'name', 'type'),)

    def validate(self):
        if len(self.name) > 50:
            raise Invalid('Repository name too long')
        return True

register_table(RepositoryDatabase)
