# encoding: utf-8

"""
Type converters are necessary to handle JSON-querys
"""

from .exceptions import Invalid

def to_int(val):
    """
    Try convert val to int
    """
    try:
        return int(val)
    except ValueError:
        raise Invalid('"%s" is not integer!' % (str(val),))

def to_string(val):
    """
    Try convert val to string
    """
    try:
        return str(val)
    except ValueError:
        raise Invalid('"%s" is not string!' % (str(val),))

def to_boolean(val):
    """
    Try convert val to boolean
    """
    if isinstance(val, bool):
        return val
    elif isinstance(val, str):
        if val.lower() in ['true', '1']:
            return True
        elif val.lower() in ['false', '0']:
            return False
    elif isinstance(val, int):
        if val in [0,1]:
            return bool(val)
    raise Invalid('"%s" is not boolean' % (str(val),))

