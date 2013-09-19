# encoding: utf-8

"""
Domain routes
"""

from bottle import response, request, abort
from lib.renki import app
from lib.utils import ok, error
from lib.auth.func import authenticated
from .domain_functions import get_user_domains, get_domains, add_user_domain
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError
from lib.validators import is_positive_numeric, validate_user_id, \
                           validate_domain, is_numeric
from lib import input_field

import json
import logging

logger = logging.getLogger('database/routes')


@app.get('/domains/')
@app.get('/domains')
@authenticated(inject_user=True)
def get_domains_route(user):
    """
    GET /domains
    """
    domains = []
    params = {'limit': None, 'offset': None}
    user_id = None
    data = dict(request.params.items())
    if data:
        if 'limit' in data:
            if is_positive_numeric(data['limit']) is True:
                params['limit'] = int(data['limit'])
            else:
                try:
                    a,b = data['limit'].split(',')
                    if is_positive_numeric(a) is not True \
                       or is_positive_numeric(b) is not True:
                        abort(400, 'Invalid "limit" parameter')
                    else:
                        params['limit'] = int(b)
                        params['offset'] = int(a)
                except (IndexError or ValueError):
                    abort(400, 'Invalid "limit" parameter')
        if 'user_id' in data:
            user_id = data['user_id']
    if user.has_permission('domain_view_all'):
        if user_id:
            domains = get_user_domains(user_id, **params)
        else:
            domains = get_domains(**params)
    elif user.has_permission('domain_view_own'):
        domains = get_user_domains(user.user_id, **params)
    else:
        abort(403, "Access denied")
    return ok({'domains': [x.as_dict() for x in domains]})


@app.put('/domains')
@app.put('/domains/')
@authenticated(inject_user=True)
def domains_put_route(user):
    """
    Add domain route
    """
    modify_all = False
    data = request.json
    if not data:
        data = dict(request.params.items())
    fields = [input_field.InputField(key='name', validator=validate_domain)]
    if user.has_perm('domain_modify_all'):
        fields.append(input_field.InputField(key='user_id',
                                             validator=validate_user_id))
        modify_all = True
        if 'user_id' in data and is_numeric(data['user_id']):
            data['user_id'] = int(data['user_id'] )
    data = input_field.verify_input(data, fields=fields)
    try:
        if modify_all:
            domain = add_user_domain(user_id=int(data['user_id']),
                                     name=data['name'])
        else:
            domain = add_user_domain(user.user_id, data['name'])
    except (AlreadyExist, DatabaseError) as e:
        return error(str(e))
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise
    return ok(domain.as_dict())
