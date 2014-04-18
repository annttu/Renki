# encoding: utf-8

"""
Domain objects database module
"""

from lib.database.user_data_table import RenkiUserDataTable
from lib.database.table import RenkiBase
from lib.database.tables import register_table
from lib.validators import validate_user_id, validate_domain
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

class DomainDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'domain'
    name = Column('name', String(1024), nullable=False)
    dns_zone = relationship("DNSZoneDatabase", uselist=False,
                            backref="domain")
    user = relationship("Users", backref="domains")

    soft_limit = 5
    hard_limit = 10

    def validate(self):
        validate_user_id(self.user_id)
        validate_domain(self.name)

# Register table
register_table(DomainDatabase)
