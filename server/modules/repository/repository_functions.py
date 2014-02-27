from bottle import request, response, abort
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, DoesNotExist, Invalid
from lib.auth.db import Users
from lib.database.basic_tables import ServerGroupDatabase
from lib.database.filters import do_limits
from .repository_database import RepositoryDatabase

def get_user_repositories(user_id=None, limit=None, offset=None, repo_type=None):
    query = RepositoryDatabase.query()

    if user_id is not None:
        try:
            Users.get(user_id)
        except DoesNotExist:
            raise
        query.filter(RepositoryDatabase.user_id == user_id)

    if repo_type is not None:
        query.filter(RepositoryDatabase.repo_type == repo_type)

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

    print(repo_type)

    repository = RepositoryDatabase()
    repository.user_id = int(user_id)
    repository.server_group_id = int(server_group_id)
    repository.name = name
    repository.repo_type = repo_type
    repository.save()

    return repository