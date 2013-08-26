#!/usr/bin/env python
# encoding: utf-8

from bottle import response, abort
from lib.renki import app
from lib.utils import ok as ret_ok, error as ret_error
from routes.login_routes import authenticated
import json


@app.get('/repositories')
@authenticated
def repositories_index():
    """
    GET /repositories
    """
    return ret_ok({'svn': [], 'git': []})
