from lib.database.table import RenkiDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship



class ServiceDatabase(RenkiBase, RenkiDataTable):
    """
    """
    __tablename__ = 'service'
    name = Column("name", String, nullable=False)

    def validate(self):
        return True

register_table(ServiceDatabase)

class ServerGroupDatabase(RenkiBase, RenkiDataTable):
    __tablename__ = 'server_group'
    name = Column("name", String, nullable=False)
    service = ForeignKey("ServiceDatabase", backref="server_group")
    
    def validate(self):
        return True
register_table(ServerGroupDatabase)

