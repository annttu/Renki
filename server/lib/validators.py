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


def validate_mid(mid):
    """
    Validate member id

    @param mid: Member id
    @type mid: str
    """
    if not isinstance(mid, int):
        raise Invalid("Member id is always integer")
    if mid < 0:
        raise Invalid("Member id is always positive integer")
    return True
