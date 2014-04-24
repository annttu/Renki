#!/usr/bin/env python
# encoding: utf-8

from bottle import request, response, abort
from lib.auth.func import authenticated
from lib.auth.func import require_perm
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, RenkiHTTPError, DoesNotExist, Invalid
from lib.renki import app
from lib.utils import ok, error

import logging
logger = logging.getLogger('module_database')

@app.get('/databases')
@app.get('/databases/')
@require_perm(permission = 'databases_view_own')
def databases_index(user):
    """
    GET /databases
    """


@app.get('/databases/<type>/<repo_id:int>')
@app.get('/databases/<type>/<repo_id:int>/')
@require_perm(permission = 'databases_view_own')
def databases_get_database(user, type, repo_id):
    """
    GET /databases/<type>/<id>
    """

@app.post('/databases/<type>')
@app.post('/databases/<type>/')
@require_perm(permission = 'databases_modify_own')
def databases_add_database(user, type):
    """
    POST /databases/<type>
    """


@app.delete('/databases/<type>/<repo_id:int>')
@app.delete('/databases/<type>/<repo_id:int>/')
@require_perm(permission = 'databases_modify_own')
def databases_delete_database(user, type, repo_id):
    """
    DELETE /databases/<type>/<id>
    """
