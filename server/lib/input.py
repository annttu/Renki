# encoding: utf-8

"""
Easy user input parser and validator
"""

# Some of code here is ispired by django.forms

from lib.exceptions import Invalid

class Validator(object):
    def __init__(self, name, required=True, default=None):
        self.name = name
        self.default = default
        self.required = required

    def validate(self, value):
        return value

def get_name(obj, default):
    if hasattr(obj, 'name'):
        return obj.name
    return default

def get_validators(bases, attrs):
    """
    Create list of validators instances from the passed in 'attrs', plus any
    similar validators on the base classes in 'bases'.
    """
    validators = [(get_name(obj, validators_name), attrs.pop(validators_name)) for validators_name, obj in
    list(attrs.items()) if isinstance(obj, Validator)]

    # Get parser also from parent classes
    for base in bases[::-1]:
        if hasattr(base, 'base_validators'):
            validators = list(base.base_validators.items()) + validators
    return dict(validators)


class DeclarativeParserMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_validators'] = get_validators(bases, attrs)
        new_class = super(DeclarativeParserMetaclass,
            cls).__new__(cls, name, bases, attrs)
        return new_class


class BaseParser(object):
    # Parser logic implementation

    def __init__(self):


        # Because base_fields can be modifed
        self.validators = copy.deepcopy(self.base_validators)

    def __getitem__(self, name):
        try:
            field = sef.validators[name]
        except KeyError:
            raise KeyError('Key %r not found in Parser' % name)
        return

    @classmethod
    def parse(cls, data):
        out = {}
        iterated = []
        for k, v in data.items():
            if k not in cls.base_validators:
                raise Invalid('Unknown parameter "%s"' % k)
            else:
                error = None
                try:
                    validator = cls.base_validators[k]
                except Invalid as e:
                    error = str(e)
                if error is not None:
                    raise Invalid('Invalid value for "%s": %s' % (
                        validator.name, error))
                out[validator.name] = validator.validate(v)
                iterated.append(k)
        for k in [i for i in cls.base_validators if i not in iterated]:
            validator = cls.base_validators[k]
            if validator.required:
                raise Invalid('"%s" is required parameter!' % validator.name)
            validator.validate(validator.default)
            out[validator.name] = validator.default
        return out



class InputParser(BaseParser, metaclass=DeclarativeParserMetaclass):
    pass


class IntegerValidator(Validator):

    def validate(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            if value.isnumeric():
                return int(value)
        raise Invalid("%s is not valid integer" % value)


class StringValidator(Validator):
    def __init__(self, *args, permit_empty=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.permit_empty = permit_empty

    def not_empty(self, value):
        if value:
            return True

    def validate(self, value):
        if self.permit_empty:
            if value == '' or value is None:
                return ''
        if isinstance(value, str):
            if self.not_empty(value) or self.permit_empty:
                return value
        raise Invalid('"%s" is not valid string' % value)

class LimitedParser(InputParser):
    pass


class DomainValidator(Validator):
    pass


if __name__ == '__main__':
    class DomainGetInput(InputParser):
        name = StringValidator('name')
        id_ = IntegerValidator('id')

    d = DomainGetInput.parse({'name': 'Veijo', 'id': '1'})
    print(d)

