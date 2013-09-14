# encoding: utf-8


class RenkiException(Exception):
    def __init__(self, msg, info=None):
        self.msg = msg
        self.info = info

    def __str__(self):
        if self.info:
            return "%s, %s" % (self.msg, self.info)
        return self.msg


class HTTPException(RenkiException):
    code = 200
    def __str__(self):
        if self.info:
            return "HTTP %s: %s, %s" % (self.code, self.msg, self.info)
        return "HTTP %s: %s" % (self.code, self.msg)

class InvalidRequest(HTTPException):
    code = 400
    """
    User has submitted invalid request
    """
    pass

class NotAuthenticated(HTTPException):
    code = 401
    """
    User haven't authenticated
    """
    pass

class AuthenticationFailed(HTTPException):
    code = 401
    """
    User authentication failed
    """
    pass


class NotAuthorized(HTTPException):
    code = 403
    """
    User haven't access to requested routine
    """
    pass


class NotFound(HTTPException):
    code = 404
    """
    Requested page not found
    """
    pass


class MethodNotAllowed(HTTPException):
    code = 405
    """
    Method not allowed
    """
    pass


class Conflict(HTTPException):
    code = 409
    """
    Request conflicts with previous changes
    """
    pass


class ServerError(HTTPException):
    code = 500
    """
    Server cannot process request properly.
    Always bug!
    """
    pass


class InvalidResponse(RenkiException):
    """
    Server response was invalid
    """
    pass
