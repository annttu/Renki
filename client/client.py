# encoding: utf-8

from .exceptions import NotAuthorized, NotFound, NotAuthenticated, \
    InvalidResponse, RenkiException, ServerError, AuthenticationFailed, \
    HTTPException, InvalidRequest, MethodNotAllowed, Conflict
import requests


class RenkiClient(object):
    """
    Client library for Renki service management system

    >>> r = RenkiClient('http://localhost:8080/')
    >>> r.authenticate('test', 'test')
    >>> r.get('/domains')
    {'domains': [
           {'member': 1, 'dns_services': True, 'id': 1, 'name': 'example.com'}
        ],
     'status': 'OK'
    }
    """
    def __init__(self, address):
        """
        @param address: address to Renki server api
        @type address: string
        """
        self.address = address.rstrip('/')
        self._authkey = None
        self._session = requests.Session()
        headers = {'User-Agent': 'RenkiClient v0.1'}
        self._session.headers = headers

    def authenticate(self, username, password):
        """
        Authenticate to server
        @param username: User username
        @type username: string
        @param passoword: User password
        @type password: string
        """
        credentials = {'username': username, 'password': password}
        ret = {}
        try:
            ret = self.post('/login', credentials)
        except NotAuthenticated:
            pass
        except HTTPException:
            raise AuthenticationFailed(
                    'Cannot authenticate due to server error')
        if 'key' not in ret:
            raise AuthenticationFailed('Username or password invalid')
        self._session.params = {'key': ret['key']}
    auth = authenticate

    def _process(self, res):
        """
        Raise exception if code isn't 200
        """
        code = int(res.status_code)
        error = None
        try:
            _json = res.json()
            status = _json['status']
        except (ValueError or KeyError):
            raise InvalidResponse("Got invalid response from server")
        if code == 200 and status == 'OK':
            return _json
        try:
            error = _json['error']
        except KeyError:
            raise InvalidResponse("Got invalid response from server")
        info = None
        try:
            info = _json['info']
        except KeyError:
            pass
        if code == 400 or status == 'ERROR':
            raise InvalidRequest(error, info=info)
        elif code == 401 or status == 'NOAUTH':
            raise NotAuthenticated(error, info=info)
        elif code == 403 or status == 'DENIED':
            raise NotAuthorized(error, info=info)
        elif code == 404 or status == 'NOTFOUND':
            raise NotFound(error, info=info)
        elif code == 405 or status == 'NOTALLOWD':
            raise MethodNotAllowed(error, info=info)
        elif code == 409 or status == 'CONFLICT':
            raise Conflict(error, info=info)
        elif code == 500 or status == 'SERVFAIL':
            raise ServerError(error, info=info)
        else:
            raise RenkiException(error, info=info)

    def _abs_url(self, path):
        """
        Return absolute url
        """
        return '/'.join([self.address, path.lstrip('/')])

    def get(self, path, params={}):
        """
        @param path: API path, eg. domain
        @type path: string
        @param params: optional params for query
        @type params: dict
        """
        ret = self._session.get(self._abs_url(path), params=params)
        return self._process(ret)

    def post(self, path, params={}):
        """
        @param path: API path, eg. domain
        @type path: string
        @param params: optional params for query
        @type params: dict
        """
        ret = self._session.post(self._abs_url(path), data=params)
        return self._process(ret)

    def put(self, path, params={}):
        """
        @param path: API path, eg. domain
        @type path: string
        @param params: optional params for query
        @type params: dict
        """
        ret = self._session.put(self._abs_url(path), params=params)
        return self._process(ret)

    def delete(self, path, params={}):
        """
        @param path: API path, eg. domain
        @type path: string
        @param params: optional params for query
        @type params: dict
        """
        ret = self._session.delete(self._abs_url(path), params=params)
        return self._process(ret)
