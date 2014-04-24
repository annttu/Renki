# encoding: utf-8

"""
Domain routes
"""

from bottle import request
from lib.renki import app
from lib.utils import ok, error, request_data
from lib.database import connection as dbconn
from lib.auth.func import require_perm
from .domain_functions import get_user_domains, add_user_domain, \
    get_domain_by_id
from .domain_validators import DomainGetValidator, UserDomainPutValidator, \
    DomainIDValidator, DomainEditValidator
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, \
    DoesNotExist

import logging
logger = logging.getLogger('module_domain')


@app.get('/domains/')
@app.get('/domains')
@require_perm(permission="domains_view_own")
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
        raise RenkiHTTPError('Unknown error occurred')
    return ok({'domains': [x.as_dict() for x in domains]})

@app.get('/<user_id:int>/domains')
@app.get('/<user_id:int>/domains/')
@require_perm(permission="domains_view_all")
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
        raise RenkiHTTPError('Unknown error occurred')
    return ok({'domains': [x.as_dict() for x in domains]})

@app.post('/domains')
@app.post('/domains/')
@require_perm(permission="domains_modify_own")
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
        raise RenkiHTTPError('Unknown error occurred')
    dbconn.session.safe_commit()
    return ok(domain.as_dict())


@app.post('/<user_id:int>/domains')
@app.post('/<user_id:int>/domains/')
@require_perm(permission="domains_modify_all")
def admin_domains_add_route(user):
    """
    Administrators add domain route

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
        raise RenkiHTTPError('Unknown error occurred')
    dbconn.session.safe_commit()
    return ok(domain.as_dict())

@app.get('/domains/<domain_id:int>')
@app.get('/domains/<domain_id:int>/')
@require_perm(permission="domains_view_own")
def domains_get_domain(user, domain_id):
    """
    GET /domains/domain_id route
    """
    data = {'user_id' : user.id, 'domain_id': domain_id}
    data = DomainIDValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user.id))
    return ok(domain.as_dict())

@app.get('/<user_id:int>/domains/<domain_id:int>')
@app.get('/<user_id:int>/domains/<domain_id:int>/')
@require_perm(permission="domains_view_all")
def domains_get_domain_admin(user, user_id, domain_id):
    """
    GET /domains/domain_id route
    """
    data = {'user_id' : user_id, 'domain_id': domain_id}
    data = DomainIDValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user_id))
    return ok(domain.as_dict())

@app.delete('/domains/<domain_id:int>')
@app.delete('/domains/<domain_id:int>/')
@require_perm(permission="domains_modify_own")
def domains_delete_domain(user, domain_id):
    """
    DELETE /domains/domain_id route
    """
    data = {'user_id' : user.id, 'domain_id': domain_id}
    data = DomainIDValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user.id))
    domain.delete()
    dbconn.session.safe_commit()
    return ok({})

@app.delete('/<user_id:int>/domains/<domain_id:int>')
@app.delete('/<user_id:int>/domains/<domain_id:int>/')
@require_perm(permission="domains_modify_all")
def domains_delete_domain_admin(user, user_id, domain_id):
    """
    DELETE /domains/domain_id route
    """
    data = {'user_id' : user_id, 'domain_id': domain_id}
    data = DomainIDValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user.id))
    domain.delete()
    dbconn.session.safe_commit()
    return ok({})

# Post /domains/<domain_id>/ to update parts of domain, e.g. comment
@app.post('/domains/<domain_id:int>')
@app.post('/domains/<domain_id:int>/')
@require_perm(permission="domains_modify_own")
def domains_modify_domain(user, domain_id):
    """
    POST /domains/domain_id route
    """
    data = request_data()
    data['user_id'] = user.id
    data['domain_id'] = domain_id
    data = DomainEditValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user.id))
    if 'comment' in data and data['comment'] is not None:
        print("Updating comment")
        domain.comment = data['comment']
    domain.save()
    dbconn.session.safe_commit()
    return ok({})

@app.post('/<user_id:int>/domains/<domain_id:int>')
@app.post('/<user_id:int>/domains/<domain_id:int>/')
@require_perm(permission="domains_modify_all")
def domains_modify_domain_admin(user, user_id, domain_id):
    """
    POST /domains/domain_id route
    """
    data = request_data()
    data['user_id'] = user_id
    data['domain_id'] = domain_id
    data = DomainEditValidator.parse(data)
    domain = get_domain_by_id(int(domain_id), user_id=int(user.id))
    if 'comment' in data and data['comment'] is not None:
        domain.comment = data['comment']
    domain.save()
    dbconn.session.safe_commit()
    return ok({})
