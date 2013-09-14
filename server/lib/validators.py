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


def is_boolean(value):
    """
    Test if value is boolean
    """
    return isinstance(value, bool)


def validate_boolean(value, name='Value'):
    """
    Validate value is boolean

    @param value: Value to test
    @type value: boolean
    @param name: Value name
    @type name: str
    """
    if not isinstance(value, bool):
        raise Invalid("%s must be <bool>, not %s" % (name), type(value))
    return True

def is_numeric(value):
    """
    Test if value is numeric.

    True-returned numerics are safe to be parsed with int(), float(), double()

    @param value: value to test
    @type value: any
    """
    try:
        int(value)
    except:
        return False
    return True

def validate_int(value, name="Value"):
    """
    Validate value is int
    """
    if isinstance(value, int):
        return True
    raise Invalid("%s must be <int>, not %s" % (name, type(value)))

def validate_positive_int(value, name="Value"):
    """
    Validate value is positive int
    """
    validate_int(value, name)
    if int(value) >= 0:
        return True
    raise Invalid("%s must be positive integer" % name)

def is_positive_numeric(value, zero_included=True):
    """
    Test if value is a positive numeric

    @param value: value to test
    @param zero_included: is zero included?
    @type value: any
    """
    try:
        value_parsed = int(value)
        if zero_included:
            if value_parsed >= 0:
                return True
        else:
            if value_parsed > 0:
                return True
  
        return False
    except:
        return False

def cast_as_int(value):
    """
    Cast as integer (discarding any decimals)

    @param value: value to cast as integer
    @type value: any
    @return: (True, successful-cast-result)|(False, None)
    """
    try:
        casted = int(value)
        return (True, casted)
    except:
        return (False, None)

def is_numeric_in_range(value, min, max):
    """
    Test if value is numeric and in range

    @param value: input value
    @param min: minimum
    @param max: maximum
    """
    try:
        value_parsed = int(value)
        if value_parsed in range(min,max):
            return True
        else:
            return False
    except:
        return False