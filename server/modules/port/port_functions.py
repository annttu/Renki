from .port_database import PortDatabase

from lib.exceptions import AlreadyExist, Invalid, DoesNotExist
from lib.validators import is_positive_numeric
from lib.database.filters import do_limits

from sqlalchemy.orm.exc import NoResultFound

def get_ports(user_id=None, limit=None, offset=None):
    query = PortDatabase.query()
    if user_id is not None:
        if is_positive_numeric(user_id) is not True:
            raise Invalid('User id must be positive integer')
        query = query.filter(PortDatabase.user_id == user_id)
    query = do_limits(query, limit, offset)
    return query.all()

def get_user_ports(user_id, limit=None, offset=None):
    if is_positive_numeric(user_id) is not True:
        raise Invalid('User id must be positive integer')
    return get_ports(user_id = user_id, limit = limit, offset = offset)
