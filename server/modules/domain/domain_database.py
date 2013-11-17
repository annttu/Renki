# encoding: utf-8

"""
Domain objects database module
"""

from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.validators import validate_user_id, validate_domain
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship


class DomainDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'domain'
    name = Column('name', String(1024), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey("users.id"),
                     nullable=False)
    dns_zone = relationship("DNSZoneDatabase", uselist=False,
                            backref="domain")
    user = relationship("Users", backref="domains")

    def validate(self):
        validate_user_id(self.user_id)
        validate_domain(self.name)


# Register table
register_table(DomainDatabase)
