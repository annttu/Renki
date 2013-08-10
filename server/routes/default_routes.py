#!/usr/bin/env python
# encoding: utf-8

from bottle import response
from lib.renki import app, __version__ as version
from lib.utils import ok as ret_ok, error as ret_error
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
def error_route():
    """
    Dummy route to represent error response
    """
    return ret_error('This route fails always, use only for testing')


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
    data = ret_error('Authentiation required',
                     data={'info': str(error.body)})
    return json.dumps(data)


@app.error(404)
def error404(error):
    response.content_type = 'application/json'
    data = ret_error('Requested page not found',
                     data={'info': str(error.body)})
    return json.dumps(data)


@app.error(405)
def error405(error):
    response.content_type = 'application/json'
    data = ret_error(str(error.body))
    return json.dumps(data)


@app.error(500)
def error500(error):
    response.content_type = 'application/json'
    data = ret_error('Unexcepted error occured',
                     data={'info': str(error.body)})
    return json.dumps(data)
