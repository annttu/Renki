# encoding: utf-8

from .exceptions import Invalid


def validate_domain(domain):
    """
    Validate domain

    @param domain: Domain name
    @type domain: str
    """
    if not domain:
        raise Invalid("Domain cannot be None")
    if not isinstance(domain, str):
        raise Invalid("Domain name must be string")
    elif len(domain) < 3:
        raise Invalid("Domain must be at least 3 characters long")
    elif '.' not in domain:
        raise Invalid("Domain must have at least one dot")
    elif domain.startswith('.'):
        raise Invalid("Domain cannot begin with dot")
    elif domain.endswith('.') and '.' not in domain[:-1]:
        raise Invalid("Domain must have at least one dot in middle")
    return True


def validate_userid(mid):
    """
    Validate userid

    @param userid: User id
    @type userid: int
    """
    if not isinstance(mid, int):
        raise Invalid("Member id is always integer")
    if mid < 0:
        raise Invalid("Member id is always positive integer")
    return True


def validate_boolean(value, name='Value'):
    """
    Validate value is boolean

    @param value: Value to test
    @type value: boolean
    @param name: Value name
    @type name: str
    """
    if not isinstance(value, bool):
        raise Invalid("%s must be boolean" % name)
    return True
