#encoding: utf-8

"""
This settings module is dynamically populated by lib.check_settings.
"""

import os

class SettingError(Exception):
    pass

class Condition(object):
    def __init__(self, name):
        self.name = name

    def __or__(self, other):
        c = self.check
        def f(*args, **kwargs):
            return c(*args, **kwargs) or other.check(*args, **kwargs)
        self.check = f
        return self
        
    def __and__(self, other):
        c = self.check
        def f(*args, **kwargs):
            return c(*args, **kwargs) and other.check(*args, **kwargs)
        self.check = f
        return self


class REQUIRED(Condition):
    """
    This setting doesn't have default value
    """
    def __init__(self, name):
        self.name = name

    def check(self, settings, value=None):
        if not value:
            raise SettingError("Value for setting %s is required" % self.name)
        return value


class REQUIREDIF(Condition):
    def __init__(self, name, condition):
        self.name = name
        self.condition = condition

    def check(self, settings, value=None):
        if not self.condition(settings):
            raise SettingError("Invalid value %s for setting %s" % (value, self.name))
        return value


class CHECKVALUE(Condition):
    def __init__(self, name, condition):
        self.name = name
        self.condition = condition

    def check(self, settings, value):
        if not self.condition(settings):
            raise SettingError("Invalid value %s for setting %s" % (value, self.name))
        return value

class ISFILE(Condition):
    def __init__(self, name):
        self.name = name

    def check(self, settings, value):
        p = os.path.abspath(os.path.expanduser(value))
        if not os.path.isfile(p):
            raise SettingError("File %s does not exist, invalid value for setting %s" % (p, self.name))
        return p

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            '()': 'logging.Formatter',
            'format': '%(asctime)-20s %(levelname)s %(module)s %(message)s'
        }
    },
    'filters': {
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'server': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'admin': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'login_routes': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'create_tables': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'dbconnection': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'BasicAuthentication': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'auth.db': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'utils': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'ticket': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'module_database': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'module_dns_zone': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'module_domain': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'module_port': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'module_repository': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'tickets_done': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'RenkiSocket': {
            'handlers' : ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
     }
}


AUTHENTICATION_MODULES = []
DEBUG = True
BIND_HOST = 'localhost'
BIND_PORT = 8080
DB_DATABASE = 'renki'
DB_USER = 'renki'
DB_PASSWORD = ''
DB_SERVER = 'localhost'
DB_PORT = 5432
DB_TEST_DATABASE = 'renki_test'
DB_TEST_USER = 'renki'
DB_TEST_PASSWORD = ''
DB_TEST_SERVER = 'localhost'
DB_TEST_PORT = 5432
RENKISRV_SOCKET_ADDRESS = '0.0.0.0'
RENKISRV_SOCKET_PORT = 6550
RENKISRV_SOCKET_SSL = True
RENKISRV_SOCKET_CERT = REQUIREDIF('RENKISRV_SOCKET_CERT', lambda x: x.RENKISRV_SOCKET_SSL) & ISFILE('RENKISRV_SOCKET_CERT')
RENKISRV_SOCKET_KEY = REQUIREDIF('RENKISRV_SOCKET_KEY', lambda x: x.RENKISRV_SOCKET_SSL) & ISFILE('RENKISRV_SOCKET_KEY')
RENKISRV_SOCKET_CA = None
KEY_EXPIRE_TIME = 86400
AUTH_SECRET = REQUIRED('AUTH_SECRET')
