# encoding: utf-8

"""
Easy user input parser and validator
"""

# Some of code here is ispired by django.forms

from lib.exceptions import Invalid
import string
import copy


class Validator(object):
    def __init__(self, name, required=True, default=None):
        self.name = name
        self.default = default
        self.required = required

    def cast(self, value):
        """
        Check and convert value to proper type or raise Invalid
        """
        return value

    def check(self, value):
        """
        Check that all requirement are met
        """
        return value

    def validate(self, value):
        return self.check(self.cast(value))

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
            field = self.validators[name]
        except KeyError:
            raise KeyError('Key %r not found in Parser' % name)
        return

    @classmethod
    def parse(cls, data):
        out = {}
        iterated = []
        for k, v in data.items():
            if k == 'key':
                # Key is always ignored
                continue
            elif k not in cls.base_validators:
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
            out[validator.name] = validator.default
        return out


class InputParser(BaseParser, metaclass=DeclarativeParserMetaclass):
    pass


class IntegerValidator(Validator):
    def __init__(self, *args, positive=False, max=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.positive = positive
        self.max = max

    def check(self, value):
        if self.positive and value < 0:
            raise Invalid("Integer %s is not positive" % value)
        if self.max is not None:
            if value > self.max:
                raise Invalid("Integer %s is too big" % value)
        return value

    def cast(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            if value.isnumeric():
                return int(value)
        raise Invalid("%s is not valid integer" % value)


class StringValidator(Validator):
    def __init__(self, *args, permit_empty=False, length=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.permit_empty = permit_empty
        self.length = length

    def check(self, value):
        if not value:
            if not self.permit_empty:
                raise Invalid('String cannot be empty!')
        elif self.length != None and len(value) > self.length:
            raise Invalid("String is too long!")
        return value

    def cast(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        raise Invalid('"%s" is not valid string' % value)


class LimitedParser(InputParser):
    limit = IntegerValidator('limit', default=None, required=False)
    offset = IntegerValidator('offset', default=None, required=False)


class DomainValidator(StringValidator):
    def __init__(self, *args, **kwargs):
        if not 'length' in kwargs:
            kwargs['length'] = 256
        kwargs['permit_empty'] = False
        super().__init__(*args, **kwargs)

    def check(self, value):
        value = super().check(value)
        value = value.lower()
        if len(value) < 3:
            raise Invalid("Domain must be at least 3 characters long")
        elif '.' not in value:
            raise Invalid("Domain must have at least one dot")
        elif value.startswith('.'):
            raise Invalid("Domain cannot begin with dot")
        elif value.endswith('.') and '.' not in value[:-1]:
            raise Invalid("Domain must have at least one dot in middle")
        try:
            value = value.encode("idna").decode("utf-8")
        except:
            raise Invalid("Domain contains invalid characters")
        allowed = string.ascii_lowercase + string.digits + '-_.'
        if value != ''.join([i for i in value if i in allowed]):
            raise Invalid("Domain contains invalid characters")
        return value


class UserIDValidator(IntegerValidator):
    def __init__(self, name):
        kwargs = {
            'max': 999999,
            'positive': True,
            'default': None
        }
        super().__init__(name, **kwargs)
