# encoding: utf-8


class RenkiException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class HTTPException(RenkiException):
    code = 200
    def __str__(self):
        return "HTTP %s: %s" % (self.code, self.msg)


class NotAuthenticated(HTTPException):
    code = 401
    """
    User haven't authenticated
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
