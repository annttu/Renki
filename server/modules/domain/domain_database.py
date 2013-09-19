# encoding: utf-8

"""
Domain objects database module
"""

from lib.database.table import RenkiUserTable, RenkiBase
from lib.database.tables import register_table
from lib.validators import validate_user_id, validate_domain
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class DomainDatabase(RenkiBase, RenkiUserTable):
    __tablename__ = 'domain'
    name = Column('name', String(1024), nullable=False)
    dns_zone = relationship("DNSZoneDatabase", uselist=False,
                            backref="domain")

    def validate(self):
        validate_user_id(self.user_id)
        validate_domain(self.name)

    def save(self):
        super(DomainDatabase, self).save()
        self._conn.add(self)
        self._conn.commit()


# Register table
register_table(DomainDatabase)
