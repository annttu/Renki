from .port_database import PortDatabase
from lib.exceptions import AlreadyExist, Invalid, DoesNotExist
from lib.validators import is_positive_numeric
from lib.database.basic_tables import ServerGroupDatabase
from lib.database.connection import session as dbsession
from lib.database.filters import do_limits
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

def get_ports(user_id = None, limit = None, offset = None):
    query = PortDatabase.query()
    if user_id is not None:
        if is_positive_numeric(user_id) is not True:
            raise Invalid('User id must be positive integer')
        query = query.filter(PortDatabase.user_id == user_id)
    query = do_limits(query, limit, offset)
    return query.all()

def get_user_ports(user_id, limit = None, offset = None):
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    return get_ports(user_id = user_id, limit = limit, offset = offset)

def get_port_by_id(port_id, user_id = None):
    query = PortDatabase.query()

    if user_id is not None:
        query = query.filter(PortDatabase.user_id == user_id)

    try:
        return query.filter(PortDatabase.id == port_id).one()
    except NoResultsFound:
        pass

    return DoesNotExist("Port id=%s does not exist" % port_id)

def add_user_port(user_id, server_group_id):
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    if is_positive_numeric(server_group_id) is not True:
        raise Invalid('Server group id must be positive integer')

    query = ServerGroupDatabase.query()
    try:
        query = query.filter(ServerGroupDatabase.id == server_group_id).one()
    except DoesNotExists:
        raise Invalid('Server group does not exist')

    try:
        query = dbsession.query(func.max(PortDatabase.port)).filter(PortDatabase.server_group_id == server_group_id).group_by(PortDatabase.server_group_id)
        portNumber = int(query.one()[0]) + 1
    except Exception as e:
        portNumber = 1337

    port = PortDatabase()
    port.user_id = int(user_id)
    port.server_group_id = int(server_group_id)
    port.port = int(portNumber)
    port.save()

    return port
