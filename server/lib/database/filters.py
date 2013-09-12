# encoding: utf-8

"""
Some commonly used filters
"""

from lib.validators import is_positive_int
from lib.exceptions import Invalid

def do_limits(query, limit, offset=None):
    """
    Apply limit and offset to query

    @raises Invalid: if limit is not None of positive integer
    """
    if limit:
        if is_positive_int(limit) is not True:
            raise Invalid('Limit must be positive integer')
        query = query.limit(int(limit))
        if offset:
            if is_positive_int(offset) is not True:
                raise Invalid('Lower limit must be positive integer')
            query = query.offset(int(offset))
    return query
