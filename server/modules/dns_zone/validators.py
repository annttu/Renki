# encoding: utf-8

from lib.exceptions import AlreadyExist, Invalid
from lib.validators import is_positive_numeric, is_numeric_in_range, cast_ip4addr, cast_ip6addr
import string
import netaddr

class DNSRecordValidator(object):
    valid_characters = string.ascii_letters+'-.'+string.digits

    def __init__(self, key, value, ttl, priority=None):
        self.verify_key(key)
        self.verify_value(value)
        self.verify_ttl(ttl)
        self.verify_priority(priority)
    
    def verify_key(self, key):
        if not all(c in DNSRecordValidator.valid_characters for c in key) or len(key.strip()) == 0:
            raise Invalid("Invalid characters in key or zero-length of %s" % self.__class__.__name__)
    
    def verify_value(self, value):
        raise Invalid("Value check not implemented for %s" % self.__class__.__name__)
    
    def verify_ttl(self, ttl):
        # ttl is either None or in range of [1,86400]
        if ttl is not None:
            mi = 1
            ma = 86400
            if not is_numeric_in_range(ttl, 1, 86400):
                raise Invalid("Number out of required range for %s ([%i,%i])" % (self.__class__.__name__,mi,ma))
    
    def verify_priority(self, priority):
        if priority is not None:
            raise Invalid("Priority is invalid for %s" % self.__class__.__name__)

class DNSNamedRecordValidator(DNSRecordValidator):
    def verify_value(self, value):
        if len(value.strip()) == 0:
            raise Invalid("Cannot accept zero-length value")
        elif all(c in DNSRecordValidator.valid_characters for c in value):
            is_ip, addr = cast_ip4addr(value)
            if not is_ip: is_ip, addr = cast_ip6addr(value)

            if is_ip: raise Invalid("Cannot have IP address in value of %s" % self.__class__.__name__)
        else:
            raise Invalid("Invalid characters in value of %s" % self.__class__.__name__)

class DNSPriorizedRecordValidator(DNSRecordValidator):
    def verify_priority(self, priority):
        mi = 0
        mx = 1024
        if not is_numeric_in_range(priority, 0, 1024):
            raise Invalid("Invalid priority range [%i,%i] for %s" % (self.__class__.__name__,mi,mx))

class DNSPriorizedNamedRecordValidator(DNSNamedRecordValidator):
    def verify_priority(self, priority):
        mi = 0
        mx = 1024
        if not is_numeric_in_range(priority, 0, 1024):
            raise Invalid("Invalid priority range [%i,%i] for %s" % (self.__class__.__name__,mi,mx))

class DNSARecordValidator(DNSRecordValidator):
    def verify_value(self, value):
        res, ip = cast_ip4addr(value)
        if not res or ip.version != 4:
            raise Invalid("Invalid IPv4 Address for %s" % self.__class__.__name__)

class DNSAAAARecordValidator(DNSRecordValidator):
    def verify_value(self, value):
        res, ip = cast_ip6addr(value)
        if not res or ip.version != 6:
            raise Invalid("Invalid IPv6 Address for %s" % self.__class__.__name__)


class DNSCNAMEValidator(DNSNamedRecordValidator):
    pass

class DNSNSValidator(DNSNamedRecordValidator):
    pass

class DNSMXValidator(DNSPriorizedNamedRecordValidator):
    pass