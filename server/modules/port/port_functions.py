from .port_database import PortDatabase
from lib.exceptions import AlreadyExist, Invalid, DoesNotExist
from lib.validators import is_positive_numeric
from lib.database.basic_tables import ServiceGroupDatabase
from lib.database.connection import session as dbsession
from lib.database.filters import do_limits
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from lib.auth.db import Users

def get_ports(user_id=None, limit=None, offset=None):
    query = PortDatabase.query()

    if user_id is not None:
        try:
            Users.get(user_id)
        except DoesNotExist:
            raise
        query = query.filter(PortDatabase.user_id == user_id)

    query = query.filter(PortDatabase.user_id == user_id)
    query = do_limits(query, limit, offset)
    return query.all()

def get_user_ports(user_id, limit=None, offset=None):
    return get_ports(user_id = user_id, limit = limit, offset = offset)

def get_port_by_id(port_id, user_id=None):
    query = PortDatabase.query()

    if user_id is not None:
        try:
            Users.get(user_id)
        except DoesNotExist:
            raise
        query = query.filter(PortDatabase.user_id == user_id)

    try:
        return query.filter(PortDatabase.id == port_id).one()
    except NoResultFound:
        pass

    raise DoesNotExist("Port id=%s does not exist" % port_id)

def add_user_port(user_id, service_group_id):
    try:
        Users.get(user_id)
    except DoesNotExist:
        raise

    try:
        ServiceGroupDatabase.get(service_group_id)
    except DoesNotExist:
        raise

    try:
        query = dbsession.query(func.max(PortDatabase.port)).filter(PortDatabase.service_group_id == service_group_id).group_by(PortDatabase.service_group_id)
        portNumber = int(query.one()[0]) + 1
    except NoResultFound:
        portNumber = 1337

    port = PortDatabase()
    port.user_id = int(user_id)
    port.service_group_id = int(service_group_id)
    port.port = int(portNumber)
    port.save()

    return port
