#!/usr/bin/env python
# encoding: utf-8

from lib.renki import app as renki
from lib.utils import ok, error
from lib.domain import Domain
from lib.exceptions import Invalid, DatabaseError, AlreadyExist
from routes.login_routes import authenticated

from bottle import request, abort
import logging

logger = logging.getLogger('routes')

EXAMPLE_DOMAIN = {
                    'id': 1,
                    'name': 'example.com',
                    'member': 1,
                    'dns_services': True
                 }


@renki.get('/domains')
@renki.get('/domains/')
@authenticated
def domains_route():
    return ok({'domains': [EXAMPLE_DOMAIN]})


@renki.put('/domains')
@renki.put('/domains/')
@authenticated
def domains_put_route():
    """
    Add domain route
    TODO:
    - user v.s. admin validation
    - user authentication
    """
    data = request.json
    if 'member' in data:
        del data['member']
    # TODO: fix this
    data['member'] = 0
    if not data:
        abort(400, 'Domain object is mandatory!')
    domain = Domain()
    try:
        domain.importJSON(data)
    except Invalid as e:
        abort(400, e.msg)
    try:
        domain.save()
    except (AlreadyExist, DatabaseError) as e:
        return error(e.msg)
    except Exception as e:
        logger.exception(e.msg)
        raise
    return ok(domain.as_json())
