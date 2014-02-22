#!/usr/bin/env python
# encoding: utf-8

from bottle import request, response, abort
from lib.renki import app
from lib.utils import ok, error
from lib.auth.func import authenticated
from lib.auth.func import require_perm
from .port_functions import get_user_ports
from .port_validators import PortGetValidator
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, DoesNotExist
import logging

logger = logging.getLogger('port_routes')

@app.get('/ports')
@app.get('/ports/')
@require_perm(permission="ports_view_own")
def ports_index(user):
    """
    GET /ports
    """
    ports = []
    
    data = dict(request.params.items())
    data['user_id'] = user.user_id
    params = PortGetValidator.parse(data)
    try:
        ports = get_user_ports(**params)
    except RenkiHTTPError:
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkitHTTPError('Unknown error occurred')
    return ok({'ports': [x.as_dict() for x in ports]})
    
