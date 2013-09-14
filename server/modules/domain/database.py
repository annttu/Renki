# encoding: utf-8

"""
Domain objects database module
"""

from lib.database.table import RenkiUserTable, RenkiBase
from lib.database.tables import register_table
from lib.validators import validate_userid, validate_domain
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class DomainDatabase(RenkiBase, RenkiUserTable):
    __tablename__ = 'domain'
    name = Column('name', String(1024), nullable=False)
    dns_zone_id = relationship("DNSZoneDatabase", uselist=False,
                               backref="domain")


    def validate(self):
        validate_userid(self.userid)
        validate_domain(self.name)

    def save(self):
        super(DomainDatabase, self).save()
        self._conn.add(self)
        self._conn.commit()


# Register table
register_table(DomainDatabase)
