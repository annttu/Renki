# encoding: utf-8

"""
Domain logic
"""


from .database import DomainDatabase
from lib.exceptions import AlreadyExist

from sqlalchemy.orm.exc import NoResultFound


def get_user_domains(userid):
    query =  DomainDatabase.query()
    return query.filter(DomainDatabase.userid==userid).all()


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

