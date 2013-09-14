# encoding: utf-8

from .exceptions import Invalid
from .validators import *


def verify_input(data, fields=[], ignore_unknown=False):
    """
    Cast and validate input
    @param data: data to validate:
    @type data: dict
    @param fields: list of fields
    @type fields: list of field objects
    """
    validated = {}
    if not data and len(fields) == 0:
        return {}
    # Remove api key
    if 'key' in data:
        del data['key']
    keys = []
    for field in fields:
        if field.key not in data:
            raise Invalid('%s is mandatory value!' % field.key)
        validated[field.key] = field.cast(data[field.key])
        keys.append(field.key)
    if not ignore_unknown:
        for value in data:
            if value not in keys:
               raise Invalid('%s is an unknown value!' % value)
    return validated


class InputField(object):
    def __init__(self, key, validator):
        self.key = key
        self.validator = validator

    def cast(self, value):
        return self.validator(value, name=self.key)


class SpecialField(InputField):
    def __init__(self, key):
        self.key = key

    def cast(self, value):
        raise Invalid('Not validated')


class IntField(SpecialField):
    """
    Integer field validator
    """
    def cast(self, value):
        """
        Cast to int
        """
        return validate_int(value, name=self.key)


class StringField(SpecialField):
    """
    String field validator
    """
    def cast(self, value):
        """
        Cast to string
        """
        return validate_string(value, name=self.key)


class BooleanField(SpecialField):
    """
    Boolean field validator
    """
    def cast(self, value):
        """
        Cast to boolean
        """
        return validate_boolean(value, name=self.key)


