# encoding: utf-8

import traceback
from bottle import HTTPError
from lib import renki_settings

class RenkiException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class RenkiHTTPError(HTTPError):
    STATUS = 500
    def __init__(self, msg):
        if renki_settings.DEBUG is True:
            traceback.print_stack()
            print(msg)
        exception = RenkiException(msg)
        super(RenkiHTTPError, self).__init__(status=self.STATUS,
                                             exception=exception)

class Stopped(RenkiException):
    pass

class Invalid(RenkiHTTPError):
    STATUS = 400
    pass


class DatabaseError(RenkiHTTPError):
    STATUS = 400
    pass


class AlreadyExist(RenkiHTTPError):
    STATUS = 409
    pass


class DoesNotExist(RenkiHTTPError):
    STATUS = 404
    pass


class AuthenticationFailed(RenkiHTTPError):
    STATUS = 401
    pass

class PermissionDenied(RenkiHTTPError):
    STATUS = 403
    pass

class SoftLimitReached(RenkiException):
    pass

class HardLimitReached(RenkiException):
    pass

class RenkiSocketError(RenkiException):
    pass

class RenkiSocketTimeout(RenkiException):
    pass

class RenkiSocketClosed(RenkiException):
    pass