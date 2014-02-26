#!/usr/bin/env python
# encoding: utf-8

from bottle import request, response, abort
from lib.auth.func import authenticated
from lib.auth.func import require_perm
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, DoesNotExist, Invalid
from lib.renki import app
from lib.utils import ok, error
from .repository_validators import RepositoryGetValidator, RepositoryAddValidator
from .repository_functions import get_user_repositories, add_user_repository
from collections import defaultdict

import logging

logger = logging.getLogger('repository_routes')

@app.get('/repositories')
@app.get('/repositories/')
@require_perm(permission = 'repositories_view_own')
def repositories_index(user):
    """
    GET /repositories
    """
    repos = {}
    data = dict(request.params.items())
    data['user_id'] = user.user_id
    params = RepositoryGetValidator.parse(data)
    try:
        repos = get_user_repositories(**params)
    except (RenkiHTTPError, Invalid):
        raise
    except Exception as e:
        print(e)
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')

    return ok({'svn': [x.as_dict() for x in repos if x.repo_type == 'svn'], 'git': [x.as_dict() for x in repos if x.repo_type == 'git']})

@app.get('/repositories/svn')
@app.get('/repositories/svn/')
@require_perm(permission = 'repositories_view_own')
def repositories_svn(user):
    """
    GET /repositories/svn
    """
    return

@app.post('/repositories')
@app.post('/repositories/')
@require_perm(permission = 'repositories_modify_own')
def repository_add(user):
    """
    POST /repositories/svn
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    data['user_id'] = user.user_id
    params = RepositoryAddValidator.parse(data)

    try:
        repo = add_user_repository(**params)
    except (RenkiHTTPError, Invalid, DoesNotExist):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    dbconn.session.safe_commit()
    return ok(repo.as_dict())

@app.get('/<user_id:int>/repositories')
@app.get('/<user_id:int>/repositories/')
@require_perm(permission = 'repositories_view_all')
def repositories_admin_index(user_id, user):
    """
    GET /<user_id:int>/repositories
    """
    return