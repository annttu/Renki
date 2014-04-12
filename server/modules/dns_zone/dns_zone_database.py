# encoding: utf-8

"""
Database objects for dns_zone
"""

from lib.database.user_data_table import RenkiUserDataTable
from lib.database.table import RenkiBase
from lib.validators import validate_user_id
from lib import renki_settings as settings

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from lib.database.tables import register_table

class DNSRecordDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'dns_record'

    dns_zone_id = Column('dns_zone_id', Integer, ForeignKey('dns_zone.id'))

    key = Column('key', String, nullable=False)
    type = Column('type', String, nullable=False)
    ttl = Column('ttl', Integer, nullable=True, default=lambda: settings.DNS_ZONE_RECORD_TTL)
    value = Column('value', String, nullable=False)
    priority = Column('priority', Integer, nullable=True, default=None)

    def validate(self):
        # TODO: add validators
        pass

class DNSZoneDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'dns_zone'
    domain_id   = Column('domain_id', Integer, ForeignKey('domain.id'))

    # SOA Properties
    refresh = Column('refresh', Integer, nullable=False,
                     default=lambda: settings.DNS_ZONE_REFRESH)
    retry = Column('retry', Integer, nullable=False,
                   default=lambda: settings.DNS_ZONE_RETRY)
    expire = Column('expire', Integer, nullable=False,
                    default=lambda: settings.DNS_ZONE_EXPIRE)
    ttl = Column('ttl', Integer, nullable=False,
                 default=lambda: settings.DNS_ZONE_TTL)

    # EMail address field
    rname = Column('rname', String, nullable=False,
                   default=lambda: settings.DNS_ZONE_RNAME)

    # This is default TTL for records
    record_ttl  = Column('record_ttl', Integer, nullable=False,
                         default=lambda: settings.DNS_ZONE_RECORD_TTL)

    records = relationship('DNSRecordDatabase', uselist=True,
                           backref='dns_zone')

    def validate(self):
        # TODO: add validators
        pass

# Register tables
register_table(DNSZoneDatabase)
register_table(DNSRecordDatabase)
