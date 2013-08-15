#!/usr/bin/env python
# encoding: utf-8

from bottle import response, abort
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error, noauth as ret_noauth, \
    notfound as ret_notfound, notallowed as ret_notallowed, \
    denied as ret_denied
import json


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

@app.error(400)
def error400(error):
    response.content_type = 'application/json'
    data = ret_error('Request is invalid', data={'info': str(error.body)})
    return json.dumps(data)


@app.error(401)
def error401(error):
    response.content_type = 'application/json'
    data = ret_noauth('Authentiation required',
                      data={'info': str(error.body)})
    return json.dumps(data)


@app.error(403)
def error403(error):
    response.content_type = 'application/json'
    data = ret_denied('Permission denied',
                      data={'info': str(error.body)})
    return json.dumps(data)


@app.error(404)
def error404(error):
    response.content_type = 'application/json'
    data = ret_notfound('Requested page not found',
                        data={'info': str(error.body)})
    return json.dumps(data)


@app.error(405)
def error405(error):
    response.content_type = 'application/json'
    data = ret_notallowed(str(error.body))
    return json.dumps(data)


@app.error(500)
def error500(error):
    response.content_type = 'application/json'
    data = ret_error('Unexcepted error occured',
                     data={'info': str(error.body)})
    return json.dumps(data)
