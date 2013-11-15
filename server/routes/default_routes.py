#!/usr/bin/env python
# encoding: utf-8

from bottle import response, abort
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error, noauth as ret_noauth, \
    notfound as ret_notfound, notallowed as ret_notallowed, \
    denied as ret_denied, conflict as ret_conflict
from lib.database import connection
import json
from sqlalchemy import func

import logging
logger = logging.getLogger('default_routes')


@app.get('/')
def index_route():
    return ret_ok({'name': 'Renki service management system API'})


@app.get('/version')
def version_route():
    """
    Show version
    """
    return ret_ok({'version': str(version)})


@app.get('/error')
@app.post('/error')
@app.put('/error')
@app.delete('/error')
def error_route():
    """
    Dummy route to represent error response
    """
    abort(400, 'This route fails always')


##################
# Error handlers #
##################

def get_error_str(error):
    """
    Get error string from `error`
    """
    try:
        if error.body:
            error = error.body
    except AttributeError:
        try:
            error = error.msg
        except AttributeError:
            pass
    return str(error)

def rollback():
    """
    Do database rollback
    """
    sessio = connection.session.session()
    if sessio.transaction.is_active:
        try:
            xid = sessio.query(func.txid_current()).first()
            print("Transaction id: %s" % xid)
        except:
            pass
    logger.debug("Rollback due to error")
    sessio.rollback()

@app.error(400)
def error400(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_error('Request is invalid', data={'info': get_error_str(error)})
    return json.dumps(data)


@app.error(401)
def error401(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_noauth('Authentiation required',
                      data={'info': get_error_str(error)})
    return json.dumps(data)


@app.error(403)
def error403(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_denied('Permission denied',
                      data={'info': get_error_str(error)})
    return json.dumps(data)


@app.error(404)
def error404(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_notfound('Requested page not found',
                        data={'info': get_error_str(error)})
    return json.dumps(data)


@app.error(405)
def error405(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_notallowed('Method not allowed',
                          data={'info': get_error_str(error)})
    return json.dumps(data)

@app.error(409)
def error409(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_conflict('Conflict',
                          data={'info': get_error_str(error)})
    return json.dumps(data)

@app.error(500)
def error500(error):
    rollback()
    response.content_type = 'application/json'
    data = ret_error('Unexcepted error occured',
                     data={'info': get_error_str(error)})
    return json.dumps(data)
