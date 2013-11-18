#!/usr/lib/env python
# encoding: utf-8

from lib.input import UserIDValidator, DomainValidator, InputParser, \
    IntegerValidator, StringValidator


class DomainGetValidator(InputParser):
    user_id = UserIDValidator('user_id')
    limit = IntegerValidator('limit', positive=True, required=False)
    offset = IntegerValidator('offset', positive=True, required=False)


class UserDomainPutValidator(InputParser):
    user_id = UserIDValidator('user_id')
    name = DomainValidator('name')
    comment = StringValidator('comment', permit_empty=True, length=512)


class DomainIDValidator(InputParser):
    user_id = UserIDValidator('user_id')
    domain_id = IntegerValidator('domain_id', positive=True, required=True)
