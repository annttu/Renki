# encoding: utf-8

"""
Domain logic
"""


from .database import DomainDatabase
from lib.exceptions import AlreadyExist, Invalid
from lib.validators import is_positive_int
from lib.database.filters import do_limits

from sqlalchemy.orm.exc import NoResultFound


def get_domains(user_id=None, limit=None, offset=None):
    query =  DomainDatabase.query()
    if user_id:
        if is_positive_int(user_id) is not True:
            raise Invalid('User id must be positive integer')
        query = query.filter(DomainDatabase.user_id==user_id)
    query = do_limits(query, limit, offset)
    return query.all()


def get_user_domains(user_id, limit=None, offset=None):
    """
    Get user `user_id` domains.
    @param user_id: user user_id
    @type user_id: positive integer
    @param limit: how many entries to return
    @type limit: positive integer
    @param offset: offset in limit
    @type offset: positive integer
    """
    if is_positive_int(user_id) is not True:
        raise Invalid('User id must be positive integer')
    return get_domains(user_id=user_id, limit=limit, offset=offset)


def get_domain(name):
    query = DomainDatabase.query()
    try:
        return query.filter(DomainDatabase.name == name).one()
    except NoResultFound:
        return None

def add_user_domain(userid, name, dns_service=True):
    if get_domain(name) is not None:
        raise AlreadyExist('Domain "%s" already exists' % name)
    domain = DomainDatabase()
    domain.userid = userid
    domain.name = name
    domain.dns_service = dns_service
    domain.save()
    return domain

