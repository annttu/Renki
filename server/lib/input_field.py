# encoding: utf-8

from .exceptions import Invalid
from lib import convert
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
    if 'apikey' in data:
        del data['apikey']
    keys = []
    for field in fields:
        if field.key not in data:
            raise Invalid('%s is mandatory value!' % field.key)
        validated[field.key] = field.validate(data[field.key])
        keys.append(field.key)
    if not ignore_unknown:
        for value in data:
            if value not in keys:
               raise Invalid('%s is an unknown value!' % value)
    return validated


class InputField(object):
    def __init__(self, key, validator, cast=None):
        """
        Input field for user input
        @param key: value name
        @type key: string
        @param validator: validator which is used to validate value
        @type validator: function
        @param cast: cast function to convert value to right type
        @type cast: function
        """
        self.key = key
        self.validator = validator
        self.cast = cast

    def validate(self, value):
        if self.cast:
            value = self.cast(value)
        return self.validator(value, name=self.key)


class SpecialField(InputField):
    cast = None

    def __init__(self, key, strict=False):
        """
        Input field for user input
        @param key: value name
        @type key: string
        @param strict: is cast used?
        @type strict: boolean
        """
        self.key = key
        self.strict = strict

    def validate(self, value):
        if self.cast and self.strict is False:
            value = self.cast(value)
        return self.validator(value=value, name=str(self.key))

class IntField(SpecialField):
    """
    Integer field validator
    """
    def validator(self, value, name):
        return validate_int(value, name=name)
    def cast(self, value):
        return convert.to_int


class StringField(SpecialField):
    """
    String field validator
    """
    def validator(self, value, name):
        return validate_string(value, name=name)
    # Necessary?
    #cast = convert.to_str


class BooleanField(SpecialField):
    """
    Boolean field validator
    """
    def cast(self, value):
        return convert.to_boolean(value)
    def validator(self, value, name):
        return validate_boolean(value, name=name)


class UserIdField(SpecialField):
    """
    User id field validator
    """
    def cast(self, value):
        return convert.to_int(value)
    def validator(self, value, name):
        return validate_user_id(value, name=name)


class DomainField(SpecialField):
    """
    Domain field validator
    """
    def validator(self, value, name):
        return validate_domain(value, name=name)

