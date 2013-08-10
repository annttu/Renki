# encoding: utf-8

"""
Renki JSON API routes
"""

# Import all routes here to use in server

from .default_routes import index_route, error_route, version_route, \
    error400, error401, error404, error405, error500
from .domain_routes import domains_route, domains_put_route
