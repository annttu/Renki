# encoding: utf-8

from lib.input import UserIDValidator, DomainValidator, InputParser, \
    IntegerValidator, StringValidator, ListValueValidator, IPv4Validator, \
    IPv6Validator, ConditionalInputParser
import string
from lib.exceptions import Invalid


class DNSRecordParser(ConditionalInputParser):
    """
    Selects correct parser for data
    """
    @classmethod
    def select_parser(cls, data):
        types = {'A':    ARecordValidator,
                 'AAAA': AAAARecordValidator,
                 'MX':   MXRecordValidator,
                 'NS':   NSRecordValidator
                 }

        if 'type' not in data:
            raise Invalid('DNS-record must have type')
        if data['type'] in types:
            return types[data['type']]
        raise Invalid('Unknown DNS record type %s' % data['type'])


class DNSRecordValidator(InputParser):
    # All common validators
    #user_id = UserIDValidator('user_id')
    #domain_id =  IntegerValidator('domain_id', positive=True, required=True)
    valid_characters = string.ascii_letters+'-.'+string.digits
    # Type is already validated at select_parser
    comment = StringValidator('comment', permit_empty=True, length=512,
                              required=False)
    type = StringValidator('type', permit_empty=False, length=5,
                           required=True, chars=valid_characters)
    key = StringValidator('key', permit_empty=False, length=5120,
                          required=True, chars=valid_characters)
    ttl = IntegerValidator('ttl', required=False, max=4294967295, min=1,
                           positive=True)
    priority = ListValueValidator('priority', allowed_values=['', None, 0],
                                  required=False)

class ARecordValidator(DNSRecordValidator):
    """
    Validate A-record
    """
    priority = ListValueValidator('priority', allowed_values=['', None],
                                 required=False)
    value = IPv4Validator('value', required=True)

class AAAARecordValidator(DNSRecordValidator):
    """
    Validate AAAA-record
    """
    priority = ListValueValidator('priority', allowed_values=['', None],
                                 required=False)
    value = IPv6Validator('value', required=True)

class MXRecordValidator(DNSRecordValidator):
    """
    Validate MX-record
    """
    priority = IntegerValidator('priority', positive=True, min=1, max=65535,
                                required=True)
    value = StringValidator('value', permit_empty=False, required=True)

class NSRecordValidator(DNSRecordValidator):
    """
    Validate NS-record
    """
    priority = ListValueValidator('priority', allowed_values=['', None],
                                 required=False)
    value = StringValidator('value', permit_empty=False, length=5120,
                            required=True,
                            chars=string.ascii_letters+'-.'+string.digits)

# Route validators

class DNSGetValidator(InputParser):
    user_id = UserIDValidator('user_id')
    domain_id =  IntegerValidator('domain_id', positive=True, required=True)
    limit = IntegerValidator('limit', positive=True, required=False)
    offset = IntegerValidator('offset', positive=True, required=False)


class DNSZoneValidator(InputParser):
    comment = StringValidator('comment', permit_empty=True, length=512,
                              required=False)
    refresh = IntegerValidator('refresh', positive=True, min=1, max=2419199,
                               required=False)
    retry = IntegerValidator('retry', positive=True, min=1, max=2419199,
                               required=False)
    expire = IntegerValidator('expire', positive=True, min=1, max=2419199,
                               required=False)
    ttl = IntegerValidator('ttl', positive=True, min=1, max=2419199,
                               required=False)
    rname = StringValidator('rname', permit_empty=False, length=256,
                            required=False,
                            chars=string.ascii_letters+'-.'+string.digits)
    record_ttl = IntegerValidator('record_ttl', positive=True, min=1,
                                  max=2419199, required=False)

class DNSQueryValidator(InputParser):
    user_id = UserIDValidator('user_id')
    domain_id =  IntegerValidator('domain_id', positive=True, required=True)

class DNSRecordQueryValidator(DNSQueryValidator):
    dns_record_id = IntegerValidator('dns_record_id', required=False,
                                     max=4294967295, min=1, positive=True)


