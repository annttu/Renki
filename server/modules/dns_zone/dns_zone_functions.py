# encoding: utf-8

from .dns_zone_database import DNSZoneDatabase, DNSRecordDatabase
from modules.domain.domain_database import DomainDatabase

from lib.exceptions import AlreadyExist, Invalid, DoesNotExist
from lib.validators import is_positive_numeric
from lib.database.filters import do_limits

from modules.domain.domain_database import DomainDatabase

from sqlalchemy.orm.exc import NoResultFound

from lib.validators import is_positive_numeric
from lib.database.filters import do_limits

def get_dns_zone(user_id, domain_id, limit=None, offset=None):
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    elif is_positive_numeric(domain_id) is not True:
        raise Invalid('User id must be positive integer')
    zonequery = DNSZoneDatabase.query()
    zonequery = zonequery.filter(DNSZoneDatabase.domain_id==domain_id)
    zonequery = zonequery.filter(DNSZoneDatabase.domain.has(
                                DomainDatabase.user_id==user_id))
    zonequery = do_limits(zonequery, limit, offset)
    try:
        return zonequery.one()
    except NoResultFound:
        pass
    raise DoesNotExist("DNS entry for domain %s does not exist" % domain_id)


def add_user_dns_zone(user_id, domain_id, ttl, retry, refresh, rname, expire,
                      record_ttl, comment=''):
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    elif is_positive_numeric(domain_id) is not True:
        raise Invalid('User id must be positive integer')
    domain_q = DomainDatabase.query()
    domain_q = domain_q.filter(DomainDatabase.user_id == user_id)
    domain_q = domain_q.filter(DomainDatabase.id == domain_id)
    try:
        domain = domain_q.one()
    except NoResultFound:
        raise DoesNotExist("Domain id=%s does not exist" % domain_id)
    try:
        get_dns_zone(user_id, domain_id)
        raise AlreadyExist("DNS zone already added for domain id=%s" % domain_id)
    except DoesNotExist:
        pass
    zone = DNSZoneDatabase()
    zone.domain_id = domain.id
    zone.refresh = refresh
    zone.retry = retry
    zone.expire = expire
    zone.ttl = ttl
    zone.rname = rname
    zone.record_ttl = record_ttl
    zone.comment = comment
    zone.save()
    return zone

def delete_dns_zone(user_id, domain_id):
    """
    Delete dns zone and all it's records
    """
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    elif is_positive_numeric(domain_id) is not True:
        raise Invalid('User id must be positive integer')
    zone = get_dns_zone(user_id, domain_id)
    records = DNSRecordDatabase.query().filter(
                DNSRecordDatabase.dns_zone_id == zone.id).all()
    for record in records:
        record.delete()
    zone.delete()
    return

def get_dns_records(user_id, domain_id, offset=None, limit=None):
    zone = get_dns_zone(user_id, domain_id)
    q = DNSRecordDatabase.query().filter(
            DNSRecordDatabase.dns_zone_id==zone.id)
    q = do_limits(q, limit, offset)
    return q.all()

def get_dns_record(user_id, dns_record_id):
    record = DNSRecordDatabase.query().filter(
        DNSRecordDatabase.id==dns_record_id,
        DNSRecordDatabase.dns_zone.has(
        DNSZoneDatabase.domain.has(
            DomainDatabase.user_id==user_id)
        )
    )
    try:
        return record.one()
    except NoResultFound:
        pass
    raise DoesNotExist("DNS record %d does not exist" % dns_record_id)

def add_dns_record(user_id, domain_id, key, type, ttl, value, priority=None,
                   comment=''):
    """
    Add dns record to dns_zone
    TODO: Check that this value is not already added
    """
    zone = get_dns_zone(user_id, domain_id)
    record = DNSRecordDatabase()
    record.dns_zone_id = zone.id
    record.key = key
    record.type = type
    record.ttl = ttl
    record.value = value
    record.priority = priority
    record.comment = comment
    record.save()
    return record

def delete_dns_record(user_id, dns_record_id):
    record = get_dns_record(user_id, dns_record_id)
    record.delete()
    return

def modify_dns_record(user_id, dns_record_id, domain_id, key, type, ttl, value,
                      priority=None, comment=''):
    record = get_dns_record(user_id, dns_record_id)
    record.key = key
    record.type = type
    record.ttl = ttl
    record.value = value
    record.priority = priority
    record.comment = comment
    record.save()
    return record
