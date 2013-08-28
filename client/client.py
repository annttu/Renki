# encoding: utf-8

from .exceptions import NotAuthorized, NotFound, NotAuthenticated, \
    InvalidResponse, RenkiException, ServerError
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
        self._session = requests.Session()
        self._authkey = None


    def authenticate(self, username, password):
        """
        Authenticate to server
        @param username: User username
        @type username: string
        @param passoword: User password
        @type password: string
        """
        try:
            ret = self.post('/login', {'username': 'test', 'password': 'test'})
        except NotAuthenticated:
            pass
        if 'key' not in ret:
            raise RenkiException('Invalid username or password')
        self._session.params = {'key': ret['key']}

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

        if code == 401 or status == 'NOAUTH':
            raise NotAuthenticated(error)
        elif code == 403 or status == 'DENIED':
            raise NotAuthorized(error)
        elif code == 404 or status == 'NOTFOUND':
            raise NotFound(error)
        elif code == 500 or status == 'SERVFAIL':
            raise ServerError(error)
        else:
            raise RenkiException(error)

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

    def deleste(self, path, params={}):
        """
        @param path: API path, eg. domain
        @type path: string
        @param params: optional params for query
        @type params: dict
        """
        ret = self._session.delete(self._abs_url(path), params=params)
        return self._process(ret)
