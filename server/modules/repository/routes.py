#!/usr/bin/env python
# encoding: utf-8

from bottle import response, abort
from lib.renki import app
from lib.utils import ok, error
from lib.auth.func import authenticated
import json


@app.get('/repositories')
@app.get('/repositories/')
@authenticated
def repositories_index():
    """
    GET /repositories
    """
    return ok({'svn': [], 'git': []})
