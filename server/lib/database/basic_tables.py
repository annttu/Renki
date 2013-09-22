from lib.database.table import RenkiDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship



class ServiceDatabase(RenkiBase, RenkiDataTable):
    """
    """
    __tablename__ = 'service'
    name = Column("name", String, nullable=False)


class ServerGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'server_group'
    name = Column("name", String, nullable=False)
    service = relationship("ServiceDatabase", backref="server_group")


class UserDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'user'
    user_id = Column('user_id', Integer, nullable=False)
    #username = Column('username', String, nullable=False)
    #firstnames = Column('firstnames', String, nullable=False)
    #lastname = Column('lastname', String, nullable=False)
