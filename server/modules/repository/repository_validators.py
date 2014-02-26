# encoding: utf-8

from lib.input import UserIDValidator, InputParser, IntegerValidator, ListValueValidator,StringValidator

class RepositoryGetValidator(InputParser):
    user_id = UserIDValidator('user_id')
    repo_type = ListValueValidator('repo_type', allowed_values=['svn', 'git'], required = False)
    limit = IntegerValidator('limit', positive = True, required = False)
    offset = IntegerValidator('offset', positive = True, required = False)

class RepositoryAddValidator(InputParser):
    user_id = UserIDValidator('user_id')
    server_group_id = IntegerValidator('server_group_id', positive = True, required = True)
    name = StringValidator('name', required = True)
    repo_type = ListValueValidator('repo_type', allowed_values=['svn', 'git'], required = True)

class RepositoryIDValidator(InputParser):
    user_id = UserIDValidator('user_id')
    port_id = IntegerValidator('port_id', positive = True, required = True)
