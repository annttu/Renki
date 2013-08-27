# encoding: utf-8


class JSON_STATUS:
    """
    Json status codes
    """
    OK = 'OK'
    OK_INFO = 'Query executed successfully'
    ERROR = 'ERROR'
    ERROR_INFO = 'Query is invalid'
    SERVFAIL = 'SERVFAIL'
    SERVFAIL_INFO = 'Server error occured'
    NOAUTH = 'NOAUTH'
    NOAUTH_INFO = 'Authentication required'
    DENIED = 'DENIED'
    DENIED_INFO = "User don't have permission to do this"
    NOTFOUND = 'NOTFOUND'
    NOTFOUND_INFO = 'URL not found'
    NOTALLOWED = 'NOTALLOWED'
    NOTALLOWED_INFO = "Requested method not allowed"

    ALL = [OK, ERROR, SERVFAIL, NOAUTH, DENIED, NOTFOUND, NOTALLOWED]
