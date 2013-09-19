# encoding: utf-8

"""
Renki JSON API routes
"""

# Import all routes here to use in server

from .default_routes import index_route, error_route, version_route, \
    error400, error401, error403, error404, error405, error409, error500
from .login_routes import login_valid, login_route
