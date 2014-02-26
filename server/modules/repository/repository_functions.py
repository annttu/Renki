from bottle import request, response, abort
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, DoesNotExist, Invalid
from lib.auth.db import Users
from lib.database.filters import do_limits
from .repository_database import RepositoryDatabase

def get_user_repositories(user_id=None, limit=None, offset=None):
    query = RepositoryDatabase.query()

    if user_id is not None:
        try:
            Users.get(user_id)
        except DoesNotExist:
            raise
        query.filter(RepositoryDatabase.user_id == user_id)

    query = do_limits(query, limit, offset)
    return query.all()

def add_user_repository(user_id, server_group_id, name, repo_type):
    try:
        Users.get(user_id)
    except DoesNotExist:
        raise

    try:
        ServerGroupDatabase.get(server_group_id)
    except DoesNotExist:
        raise