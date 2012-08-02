import sqlalchemy.types as types
from libs.tools import *
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.ext.compiler import compiles

def parse_inetlist(inetlist):
    if not inetlist:
        return None
    addresses = []
    address = ""
    for i in inetlist:
        if i in '1234567890.':
            address += i
        elif i in ',}':
            addresses.append(address)
            address = ''
    retval = []
    for inet in addresses:
        if valid_ipv4_address(inet) or valid_ipv6_address(inet):
            retval.append(inet)
        elif valid_ipv4_block(inet) or valid_ipv6_block(inet):
            retval.append(inet)
    return retval

def create_inetlist(inetlist):
    if not inetlist:
        return None
    if inetlist == [] or inetlist == ():
        return None
    retval = []
    for inet in inetlist:
        if valid_ipv4_address(inet) or valid_ipv6_address(inet):
            retval.append("%s" % inet)
        elif valid_ipv4_block(inet) or valid_ipv6_block(inet):
            retval.append(inet)
    return retval


## Create type INETARRAY   
class INETARRAY(types.TypeEngine):

    def __init__(self, *args):
        self._args = args

    def get_col_spec(self):
       
        return 'inet[]' % vals

    def convert_bind_param(self, value, engine):
        return value

    def convert_result_value(self, value, engine):
        return value

    def process_result_value(self, value, dialect):
        return parse_inetlist(value)

    def compile(element, compiler, **kw):
        vals = ''
        for arg in self._args:
            vals += '\'%s\'::inet,' % arg
        vals = vals.strip(',')
        print('asdf:ARRAY[%s]::inet[]' % vals)
        return "ARRAY[%s]::inet[]" % vals

@compiles(INETARRAY)
def compile_inetarray(element, compiler, **kw):
    vals = ''
    for arg in self._args:
        vals += '\'%s\'::inet,' % arg
    vals = vals.strip(',')
    print('asdf:ARRAY[%s]::inet[]' % vals)
    return "ARRAY[%s]::inet[]" % vals

"""class INETARRAY(types.TypeEngine):
    '''Decode inet array to array of strings.
    '''

    def get_col_spec(self):
        return "inet[]"

    def process_bind_param(self, value, dialect):
        return create_inetlist(value)

    def process_result_value(self, value, dialect):
        return parse_inetlist(value)

    def copy(self):
        return INETARRAY(self.impl)"""
