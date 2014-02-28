#!/usr/bin/env python
# encoding: utf-8

from bottle import request, response, abort
from lib.auth.func import authenticated
from lib.auth.func import require_perm
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, RenkiHTTPError, DoesNotExist, Invalid
from lib.renki import app
from lib.utils import ok, error
from .repository_validators import RepositoryGetValidator, RepositoryAddValidator, RepositoryIDValidator
from .repository_functions import get_user_repositories, add_user_repository, get_repository_by_id
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
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
    return ok({'svn': [x.as_dict() for x in repos if x.type == 'svn'], 'git': [x.as_dict() for x in repos if x.type == 'git']})


@app.get('/repositories/<type>/<repo_id:int>')
@app.get('/repositories/<type>/<repo_id:int>/')
@require_perm(permission = 'repositories_view_own')
def repositories_get_repository(user, type, repo_id):
    """
    GET /repositories/<type>/<id>
    """
    data = dict(request.params.items())
    data.update({'user_id': user.user_id, 'type': type, 'repo_id': repo_id})
    params = RepositoryIDValidator.parse(data)
    try:
        repo = get_repository_by_id(**params)
    except DoesNotExist:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')

    return ok(repo.as_dict())

@app.post('/repositories/<type>')
@app.post('/repositories/<type>/')
@require_perm(permission = 'repositories_modify_own')
def repositories_add_repository(user, type):
    """
    POST /repositories/<type>
    """
    data = dict(request.params.items())
    data['user_id'] = user.user_id
    data['type'] = type
    params = RepositoryAddValidator.parse(data)
    try:
        repo = add_user_repository(**params)
    except (DoesNotExist, AlreadyExist):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
    dbconn.session.safe_commit()
    return ok(repo.as_dict())

@app.delete('/repositories/<type>/<repo_id:int>')
@app.delete('/repositories/<type>/<repo_id:int>/')
@require_perm(permission = 'repositories_modify_own')
def repositories_delete_repository(user, type, repo_id):
    """
    DELETE /repositories/<type>/<id>
    """
    data = dict(request.params.items())
    data.update({'user_id': user.user_id, 'type': type, 'repo_id': repo_id})
    params = RepositoryIDValidator.parse(data)
    try:
        repo = get_repository_by_id(**params)
    except DoesNotExist:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
    repo.delete()
    dbconn.session.safe_commit()
    return ok()