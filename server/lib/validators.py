# encoding: utf-8

from .exceptions import Invalid
import netaddr
from datetime import datetime
import inspect


def get_var_name(default):
    """
    Try to fetch caller variable name
    """
    try:
        var = inspect.getframeinfo(inspect.stack()[2][0])[3][0].split('(')[-1].split(')')[0]
        var = var.replace('self.','').split(',')[0].strip()
        return var
    except:
        return default

def validate_domain(value, name="Value"):
    """
    Validate domain `value`

    @param domain: Domain name
    @type domain: str
    """
    if value is None:
        raise Invalid("Domain cannot be None")
    if not isinstance(value, str):
        raise Invalid("Domain name must be string, not %s" % type(value))
    elif len(value) < 3:
        raise Invalid("Domain must be at least 3 characters long")
    elif '.' not in value:
        raise Invalid("Domain must have at least one dot")
    elif value.startswith('.'):
        raise Invalid("Domain cannot begin with dot")
    elif value.endswith('.') and '.' not in value[:-1]:
        raise Invalid("Domain must have at least one dot in middle")
    try:
        return value.encode("idna").decode("utf-8")
    except:
        raise Invalid("Domain contains invalid characters")


def validate_user_id(value, name="user_id"):
    """
    Validate user_id

    @param userid: User id
    @type userid: int
    """
    if not isinstance(value, int):
        raise Invalid("User id is always integer")
    if value < 0:
        raise Invalid("User id is always positive integer")
    return value


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
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        if value.lower == 'true':
            return True
        elif value.lower ==  'false':
            return False
    raise Invalid("%s must be <bool>, not %s" % (name), type(value))

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
        return int(value)
    raise Invalid("%s must be <int>, not %s" % (name, type(value)))

def validate_positive_int(value, name="Value"):
    """
    Validate value is positive int
    """
    validate_int(value, name)
    if int(value) >= 0:
        return int(value)
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

def validate_string(value, name=None):
    """
    Test if value is string.

    @param value: value to test
    @type value: any
    """
    if not name:
        name = get_var_name('Value')
    if isinstance(value, str):
        return value
    raise Invalid("%s must be string, not %s" % (name, type(value)))


def validate_datetime(value, in_future=False):
    """
    Test if value is datetime object.
    If in_future is true, test also that datetime is in future
    """
    name = get_var_name('datetime')
    if not isinstance(value, datetime):
        raise Invalid("%s must be datetime, not %s" % (name, type(value)))
    if in_future is True:
        if value <= datetime.now():
            raise Invalid("%s must be in future" % (name))
    return value

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

def cast_ip4addr(ipaddr_str):
    if ipaddr_str.count('.') == 3:
        try:
            ip = netaddr.IPAddress(ipaddr_str)
            return (True, ip)
        except:
            return (False, None)
    else:
        return (False, None)

def cast_ip6addr(ipaddr_str):
    if ipaddr_str.count(':') >= 2:
        try:
            ip = netaddr.IPAddress(ipaddr_str)
            return (True, ip)
        except:
            return (False, None)
    else:
        return (False, None)
