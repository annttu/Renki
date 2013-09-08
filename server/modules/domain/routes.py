# encoding: utf-8

"""
Domain routes
"""

from bottle import response, request, abort
from lib.renki import app
from lib.utils import ok, error
from lib.auth.func import authenticated
from .domain import get_user_domains, add_user_domain
from lib.exceptions import AlreadyExist, DatabaseError
import json
import logging

logger = logging.getLogger('database/routes')


@app.get('/domains/')
@app.get('/domains')
@authenticated(inject_user=True)
def get_domains(user):
    """
    GET /domains
    """
    domains = [x.as_dict() for x in get_user_domains(user.userid)]
    return ok({'domains': domains})


@app.put('/domains')
@app.put('/domains/')
@authenticated(inject_user=True)
def domains_put_route(user):
    """
    Add domain route
    TODO:
    - user v.s. admin validation
    - user authentication
    """
    print("sdf: %s" %  dict(request.params.items()))
    data = request.json
    if not data:
        data = dict(request.params.items())
    if 'key' in data:
        del data['key']
    if not data:
        abort(400, 'Domain object is mandatory!')
    for value in ['name', 'dns_service']:
        if value not in data:
            abort(400, '%s is mandatory value!')
    try:
        data['dns_service'] = bool('dns_service')
    except ValueError:
        abort(400, 'dns_service must be boolean!')
    try:
        domain = add_user_domain(user.userid, data['name'],
                                 data['dns_service'])
    except (AlreadyExist, DatabaseError) as e:
        return error(e.msg)
    except Exception as e:
        logger.exception(e.msg)
        raise
    return ok(domain.as_dict())
