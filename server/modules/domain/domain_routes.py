# encoding: utf-8

"""
Domain routes
"""

from bottle import response, request, abort
from lib.renki import app
from lib.utils import ok, error
from lib.database import connection as dbconn
from lib.auth.func import authenticated
from .domain_functions import get_user_domains, get_domains, add_user_domain
from .domain_validators import DomainGetValidator, UserDomainPutValidator
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, \
    PermissionDenied

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

    data = dict(request.params.items())
    if user.has_permission('domain_view_all'):
        pass
    elif user.has_permission('domain_view_own'):
        data['user_id'] = user.user_id
    else:
        raise PermissionDenied("You don't have permission to view domains")
    params = DomainGetValidator.parse(data)
    try:
        domains = get_user_domains(**params)
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    return ok({'domains': [x.as_dict() for x in domains]})


@app.put('/domains')
@app.put('/domains/')
@authenticated(inject_user=True)
def domains_put_route(user):
    """
    Add domain route
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    if user.has_perm('domain_modify_all'):
        pass
    elif user.has_perm('domain_modify_own'):
        data['user_id'] = user.user_id
    params = UserDomainPutValidator.parse(data)
    try:
        domain = add_user_domain(**params)
    except (AlreadyExist, DatabaseError) as e:
        return error(str(e))
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    dbconn.conn.safe_commit()
    return ok(domain.as_dict())
