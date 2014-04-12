# encoding: utf-8

from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class PortDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'port'
    server_group_id = Column('server_group_id', Integer, ForeignKey("server_group.id"), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey("users.id"), nullable=False)
    port = Column('port', Integer, nullable=False)
    __table_args__ = (UniqueConstraint('server_group_id', 'port'),)

    def validate(self):
        return True

# Register table
register_table(PortDatabase)
