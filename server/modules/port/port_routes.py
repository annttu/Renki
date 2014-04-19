#!/usr/bin/env python
# encoding: utf-8

from bottle import request
from lib.auth.func import require_perm
from lib.database import connection as dbconn
from lib.exceptions import DatabaseError, RenkiHTTPError, DoesNotExist, Invalid, SoftLimitReached, HardLimitReached, PermissionDenied
from lib.renki import app
from lib.utils import ok, error
from .port_functions import get_user_ports, add_user_port, get_port_by_id, get_user_port_history
from .port_validators import PortGetValidator, PortAddValidator, PortIDValidator
from .port_database import PortDatabase

import logging
logger = logging.getLogger('module_port')

@app.get('/ports')
@app.get('/ports/')
@require_perm(permission="ports_view_own")
def ports_index(user):
    """
    GET /ports
    """
    data = dict(request.params.items())
    data.update({'user_id': user.user_id})
    params = PortGetValidator.parse(data)
    try:
        ports = get_user_ports(**params)
    except (RenkiHTTPError, Invalid):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
    return ok({'ports': [x.as_dict() for x in ports]})

@app.get('/<user_id:int>/ports')
@app.get('/<user_id:int>/ports/')
@require_perm(permission='ports_view_all')
def admin_ports_index(user, user_id):
    """
    GET /<id>/ports
    """
    data = dict(request.params.items())
    data.update({'user_id': user_id})
    params = PortGetValidator.parse(data)
    try:
        ports = get_user_ports(**params)
    except (RenkiHTTPError, Invalid, DoesNotExist):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
    return ok({'ports': [x.as_dict() for x in ports]})

@app.post('/ports')
@app.post('/ports/')
@require_perm(permission="ports_modify_own")
def ports_add(user):
    """
    POST /ports
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    data.update({'user_id': user.user_id})
    params = PortAddValidator.parse(data)
    try:
        port = add_user_port(**params)
    except (RenkiHTTPError, Invalid, DoesNotExist):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')

    try:
        PortDatabase.validate_add(user, user.user_id)
    except SoftLimitReached as e:
        port.waiting = True
        pass
    except HardLimitReached as e:
        logger.exception(e)
        raise PermissionDenied('Not allowed to create more ports')
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    
    dbconn.session.safe_commit()
    return ok(port.as_dict())

@app.post('/<user_id:int>/ports')
@app.post('/<user_id:int>/ports/')
@require_perm(permission="ports_modify_all")
def admin_ports_add(user, user_id):
    """
    POST /<user_id>/ports
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    data.update({'user_id': user_id})
    params = PortAddValidator.parse(data)
    try:
        port = add_user_port(**params)
    except (Invalid, DatabaseError, RenkiHTTPError, DoesNotExist):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occured')
    dbconn.session.safe_commit()
    return ok(port.as_dict())

@app.delete('/ports/<port_id:int>')
@app.delete('/ports/<port_id:int>/')
@require_perm(permission="ports_delete_own")
def ports_delete(user, port_id):
    """
    DELETE /ports/port_id route
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    data.update({'user_id' : user.id, 'port_id': port_id})
    params = PortIDValidator.parse(data)
    try:
        port = get_port_by_id(**params)
    except DoesNotExist:
        raise
    port.delete()
    dbconn.session.safe_commit()
    return ok()

@app.delete('/<user_id:int>/ports/<port_id:int>')
@app.delete('/<user_id:int>/ports/<port_id:int>/')
@require_perm(permission="ports_delete_all")
def admin_ports_delete(user, user_id, port_id):
    """
    DELETE /ports/port_id route
    """
    data = request.json
    if not data:
        data = dict(request.params.items())
    data.update({'user_id' : user_id, 'port_id': port_id})
    params = PortIDValidator.parse(data)
    try:
        port = get_port_by_id(**params)
    except DoesNotExist:
        raise
    port.delete()
    dbconn.session.safe_commit()
    return ok()

@app.get('/ports/history')
@app.get('/ports/history/')
@require_perm(permission="ports_history_own")
def ports_history(user):
    """
    GET /ports/history
    """
    data = dict(request.params.items())
    data.update({'user_id': user.user_id})
    params = PortGetValidator.parse(data)
    try:
        ports = get_user_port_history(**params)
    except (RenkiHTTPError, Invalid):
        raise
    except Exception as e:
        logger.exception(e)
        raise RenkiHTTPError('Unknown error occurred')
        
    return ok({'ports': [x.to_dict() for x in ports]})
    #return ok({'ports': [str(x) + str(vars(ports)[x]) for x in vars(ports)]})#[x.as_dict() for x in ports]})