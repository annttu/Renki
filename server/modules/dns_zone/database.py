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
    refresh     = Column('refresh',     Integer,    nullable=False)
    retry       = Column('retry',       Integer,    nullable=False)
    expire      = Column('expire',      Integer,    nullable=False)
    ttl         = Column('ttl',         Integer,    nullable=False)
    rname       = Column('rname',       String,     nullable=False)
    record_ttl  = Column('record_ttl',  Integer,    nullable=False)

# Register table
register_table(DNSZoneDatabase)
