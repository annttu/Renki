# encoding: utf-8

"""
DNS zone routes
"""

from bottle import request
from lib.renki import app
from lib.utils import ok, error, request_data, sandbox
from lib.database import connection as dbconn
from lib.auth.func import require_perm
from .dns_zone_validators import DNSGetValidator, \
    DNSZoneValidator, DNSRecordParser, DNSRecordQueryValidator, \
    DNSQueryValidator
from .dns_zone_functions import get_dns_zone, add_user_dns_zone, \
    get_dns_records, add_dns_record, delete_dns_record, get_dns_record, \
    modify_dns_record, delete_dns_zone
from lib.exceptions import RenkiHTTPError

import logging
logger = logging.getLogger('database')


def get_dns_route(user_id, domain_id):
    """
    GET /domains/<domain_id>/dns route
    """
    data = dict(request.params.items())
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    params = DNSGetValidator.parse(data)
    zone = sandbox(get_dns_zone, **params)
    dbconn.session.safe_commit()
    return ok(zone.as_dict())

@app.get('/domains/<domain_id:int>/dns')
@app.get('/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_view_own")
def dns_zone_user_get(domain_id, user):
    """
    GET /domains/<domain_id>/dns/
    """
    return get_dns_route(user.user_id, domain_id)

@app.get('/<user_id:int>/domains/<domain_id:int>/dns')
@app.get('/<user_id:int>/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_view_all")
def get_user_dns_route(user_id, domain_id, user):
    """
    GET /<user_id>/domains/<domain_id>/dns/
    """
    return get_dns_route(user_id, domain_id)


def dns_zone_add_route(user_id, domain_id):
    """
    PUT /domains/<domain_id>/dns
    """
    data = dict(request.json)
    qdata = {}
    qdata['user_id'] = user_id
    qdata['domain_id'] = domain_id
    params = DNSZoneValidator.parse(data)
    qparams = DNSQueryValidator.parse(qdata)
    params.update(qparams)
    zone = sandbox(add_user_dns_zone, **params)
    dbconn.session.safe_commit()
    return ok(zone.as_dict())

@app.put('/domains/<domain_id:int>/dns')
@app.put('/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_modify_own")
def dns_zone_user_add_route(domain_id, user):
    """
    PUT /domains/<domain_id>/dns
    """
    return dns_zone_add_route(user.user_id, domain_id)

@app.put('/<user_id:int>/domains/<domain_id:int>/dns')
@app.put('/<user_id:int>/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_modify_all")
def dns_zone_admin_add_route(user_id, domain_id, user):
    """
    PUT /<user_id:int>/domains/<domain_id>/dns
    """
    return dns_zone_add_route(user_id, domain_id)


def dns_zone_delete_route(user_id, domain_id):
    data = dict(request.params.items())
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    params = DNSQueryValidator.parse(data)
    sandbox(delete_dns_zone, **params)
    dbconn.session.safe_commit()
    return ok({})


@app.delete('/domains/<domain_id:int>/dns')
@app.delete('/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_modify_own")
def dns_zone_user_delete_route(domain_id, user):
    """
    DELETE /domains/<domain_id>/dns
    """
    return dns_zone_delete_route(user.user_id, domain_id)


@app.delete('/<user_id:int>/domains/<domain_id:int>/dns')
@app.delete('/<user_id:int>/domains/<domain_id:int>/dns/')
@require_perm(permission="dns_zone_modify_all")
def dns_zone_admin_delete_route(user_id, domain_id, user):
    """
    DELETE /<user_id>/domains/<domain_id>/dns
    """
    return dns_zone_delete_route(user_id, domain_id)


def dns_zone_get_records(user_id, domain_id):
    """
    GET /domains/<domain_id>/dns/records
    """
    data = dict(request.params.items())
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    params = DNSGetValidator.parse(data)
    records = sandbox(get_dns_records, **params)
    return ok({'records': [x.as_dict() for x in records]})


@app.get('/domains/<domain_id:int>/dns/records')
@app.get('/domains/<domain_id:int>/dns/records/')
@require_perm(permission="dns_zone_view_own")
def dns_zone_user_get_records(domain_id, user):
    """
    GET /domains/<domain_id>/dns/records
    """
    return dns_zone_get_records(user.user_id, domain_id)


@app.get('/<user_id:int>/domains/<domain_id:int>/dns/records')
@app.get('/<user_id:int>/domains/<domain_id:int>/dns/records/')
@require_perm(permission="dns_zone_view_all")
def dns_zone_admin_get_records(user_id, domain_id, user):
    """
    GET /<user_id>/domains/<domain_id>/dns/records
    """
    return dns_zone_get_records(user_id, domain_id)


def dns_zone_add_records(user_id, domain_id):
    """
    Add new DNS record to DNS zone
    """
    data = dict(request.params.items())
    qdata = {}
    qdata['user_id'] = user_id
    qdata['domain_id'] = domain_id
    qparams = DNSQueryValidator.parse(qdata)
    params = DNSRecordParser.parse(data)
    params.update(qparams)
    record = sandbox(add_dns_record, **params)
    dbconn.session.safe_commit()
    return ok(record.as_dict())

@app.post('/domains/<domain_id:int>/dns/records/')
@app.post('/domains/<domain_id:int>/dns/records')
@require_perm(permission="dns_zone_modify_own")
def dns_zone_user_add_records(domain_id, user):
    """
    POST /domains/<domain_id>/dns/records
    """
    return dns_zone_add_records(user.user_id, domain_id)


@app.post('/<user_id:int>/domains/<domain_id:int>/dns/records/')
@app.post('/<user_id:int>/domains/<domain_id:int>/dns/records')
@require_perm(permission="dns_zone_modify_all")
def dns_zone_admin_add_records(user_id, domain_id, user):
    """
    POST /<user_id>/domains/<domain_id>/dns/records
    """
    return dns_zone_add_records(user_id, domain_id)


def dns_zone_get_record(user_id, domain_id, dns_record_id):
    """
    GET /domains/<domain_id>/dns/records/<dns_record_id>
    """
    data = dict(request.params.items())
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    data['dns_record_id'] = dns_record_id
    params = DNSRecordQueryValidator.parse(data)
    record = sandbox(get_dns_record, user_id=params['user_id'],
                          dns_record_id=params['dns_record_id'])
    return ok(record.as_dict())

@app.get('/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.get('/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_view_own")
def dns_zone_user_get_record(domain_id, dns_record_id, user):
    """
    GET /domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_get_record(user.user_id, domain_id, dns_record_id)


@app.get('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.get('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_view_own")
def dns_zone_admin_get_record(user_id, domain_id, dns_record_id, user):
    """
    GET /domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_get_record(user_id, domain_id, dns_record_id)


def dns_zone_modify_record(user_id, domain_id, dns_record_id):
    """
    PUT/POST /domains/<domain_id>/dns/records/<dns_record_id>
    """

    qdata = {}
    qdata['user_id'] = user_id
    qdata['domain_id'] = domain_id
    qdata['dns_record_id'] = dns_record_id
    qparams = DNSRecordQueryValidator.parse(qdata)
    params = DNSRecordParser.parse(data)
    params.update(qparams)
    record = sandbox(modify_dns_record, **params)
    dbconn.session.safe_commit()
    return ok(record.as_dict())



@app.put('/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.put('/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@app.post('/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.post('/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_modify_own")
def dns_zone_user_modify_record(domain_id, dns_record_id, user):
    """
    PUT/POST /domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_modify_record(user.user_id, domain_id, dns_record_id)

@app.put('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.put('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@app.post('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.post('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_modify_all")
def dns_zone_admin_modify_record(user_id, domain_id, dns_record_id, user):
    """
    PUT/POST /<user_id>/domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_modify_record(user_id, domain_id, dns_record_id)

def dns_zone_delete_record(user_id, domain_id, dns_record_id):
    """
    DELETE /domains/<domain_id>/dns/records/<dns_record_id>
    """
    data = dict(request.params.items())
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    data['dns_record_id'] = dns_record_id
    params = DNSRecordQueryValidator.parse(data)
    sandbox(delete_dns_record, user_id=params['user_id'],
            dns_record_id=params['dns_record_id'])
    dbconn.session.safe_commit()
    return ok({})

@app.delete('/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.delete('/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_modify_own")
def dns_zone_user_delete_record(domain_id, dns_record_id, user):
    """
    DELETE /domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_delete_record(user.user_id, domain_id, dns_record_id)

@app.delete('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>')
@app.delete('/<user_id:int>/domains/<domain_id:int>/dns/records/<dns_record_id:int>/')
@require_perm(permission="dns_zone_modify_all")
def dns_zone_admin_delete_record(user_id, domain_id, dns_record_id, user):
    """
    DELETE /<user_id>/domains/<domain_id>/dns/records/<dns_record_id>
    """
    return dns_zone_delete_record(user_id, domain_id, dns_record_id)
