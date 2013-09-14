# encoding: utf-8

"""
Database objects for dns_zone
"""

from lib.database.table import RenkiBase, RenkiTable
from sqlalchemy import Column,String,Boolean,Integer,ForeignKey
from lib.database.tables import register_table

class DNSZoneDatabase(RenkiBase, RenkiTable):
    __tablename__ = 'dns_zone'
    domain_id   = Column('domain_id',   Integer,    ForeignKey('domain.id'))

    # SOA Properties
    refresh     = Column('refresh',     Integer,    nullable=False)
    retry       = Column('retry',       Integer,    nullable=False)
    expire      = Column('expire',      Integer,    nullable=False)
    ttl         = Column('ttl',         Integer,    nullable=False)
    
    # EMail address field
    rname       = Column('rname',       String,     nullable=False)

    # This is default TTL for records
    record_ttl  = Column('record_ttl',  Integer,    nullable=False)
    
    records     = relationship('DNSEntryDatabase', uselist=True, backref='dns_zone')

class DNSEntryDatabase(RenkiBase, RenkiTable):
    __tablename__ = 'dns_record'
    dns_zone    = Column('dns_zone_id', Integer,    ForeignKey('dns_zone.id'))

    key         = Column('key',         String,     nullable=False)
    record_type = Column('record_type', String,     nullable=False)
    ttl         = Column('ttl',         Integer,    nullable=False)
    value       = Column('value',       String,     nullable=False)
    priority    = Column('priority',    Integer,    nullable=True,  default=None)

    def validate(self):


# Register tables
register_table(DNSZoneDatabase)
register_table(DNSEntryDatabase)