# encoding: utf-8


class RenkiException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Invalid(RenkiException):
    pass


class DatabaseError(RenkiException):
    pass


class AlreadyExist(RenkiException):
    pass


class DoesNotExist(RenkiException):
    pass

class AuthenticationFailed(RenkiException):
    pass


class SettingError(RenkiException):
    pass
