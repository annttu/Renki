from bottle import request, response, abort
from lib.database import connection as dbconn
from lib.exceptions import AlreadyExist, DatabaseError, RenkiHTTPError, DoesNotExist, Invalid
from lib.auth.db import Users
from lib.database.basic_tables import ServerGroupDatabase
from lib.database.filters import do_limits
from .repository_database import RepositoryDatabase
from sqlalchemy.orm.exc import NoResultFound

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

def get_repository_by_id(user_id, type, repo_id):
    query = RepositoryDatabase.query()
    if user_id is not None:
        try:
            Users.get(user_id)
        except DoesNotExist:
            raise
        query = query.filter(RepositoryDatabase.user_id == user_id)

    if type is not None:
        query = query.filter(RepositoryDatabase.type == type)

    try:
        return query.filter(RepositoryDatabase.id == repo_id).one()
    except NoResultFound:
        pass

    raise DoesNotExist("Repository id=%s does not exist" % repo_id)


def add_user_repository(user_id, server_group_id, name, type):
    try:
        Users.get(user_id)
    except DoesNotExist:
        raise

    try:
        ServerGroupDatabase.get(server_group_id)
    except DoesNotExist:
        raise

    try:
        RepositoryDatabase.query().filter(RepositoryDatabase.server_group_id == server_group_id and RepositoryDatabase.name == name and RepositoryDatabase.type == type).one()
    except NoResultFound:
        pass
    except Exception as e:
        raise AlreadyExist("Repository name=%s type=%s server_group_id=%s already exists" % (name, type, server_group_id))

    repository = RepositoryDatabase()
    repository.user_id = int(user_id)
    repository.server_group_id = int(server_group_id)
    repository.name = name
    repository.type = type
    repository.save()

    return repository