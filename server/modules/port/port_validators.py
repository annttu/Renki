# encoding: utf-8

from lib.input import UserIDValidator, InputParser, IntegerValidator

class PortGetValidator(InputParser):
    user_id = UserIDValidator('user_id')
    limit = IntegerValidator('limit', positive = True, required = False)
    offset = IntegerValidator('offset', positive = True, required = False)

class PortAddValidator(InputParser):
    user_id = UserIDValidator('user_id')
    server_group_id = IntegerValidator('server_group_id', positive = True, required = True)

class PortIDValidator(InputParser):
    user_id = UserIDValidator('user_id')
    port_id = IntegerValidator('port_id', positive = True, required = True)
