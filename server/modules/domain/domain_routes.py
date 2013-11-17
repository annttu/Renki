# encoding: utf-8

"""
Domain routes
"""

from bottle import response, request, abort
from lib.renki import app
from lib.utils import ok, error
from lib.database import connection as dbconn
from lib.auth.func import authenticated, require_perm
from .domain_functions import get_user_domains, get_domains, add_user_domain
from .domain_validators import DomainGetValidator, UserDomainPutValidator
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, \
    PermissionDenied
import threading
import logging

logger = logging.getLogger('database/routes')


@app.get('/domains/')
@app.get('/domains')
@require_perm(permission="domain_view_own")
def get_domains_route(user):
    """
    GET /domains
    """
    domains = []

    data = dict(request.params.items())
    data['user_id'] = user.user_id
    params = DomainGetValidator.parse(data)
    try:
        domains = get_user_domains(**params)
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    return ok({'domains': [x.as_dict() for x in domains]})

@app.get('/<user_id:int>/domains')
@app.get('/<user_id:int>/domains/')
@require_perm(permission="domain_view_all")
def get_user_domains_route(user_id, user):
    """
    GET /user_id/domains

    TODO: Check that user_id exists!
    """
    domains = []

    data = dict(request.params.items())
    data['user_id'] = user_id
    params = DomainGetValidator.parse(data)
    try:
        domains = get_user_domains(**params)
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    return ok({'domains': [x.as_dict() for x in domains]})

@app.post('/domains')
@app.post('/domains/')
@require_perm(permission="domain_modify_own")
def domains_add_route(user):
    """
    Add domain route
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
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
    dbconn.session.safe_commit()
    return ok(domain.as_dict())


@app.post('/<user_id:int>/domains')
@app.post('/<user_id:int>/domains/')
@require_perm(permission="domain_modify_all")
def admin_domains_add_route(user):
    """
    Admins add domain route

    TODO: Check that user_id exists!
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
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
    dbconn.session.safe_commit()
    return ok(domain.as_dict())
