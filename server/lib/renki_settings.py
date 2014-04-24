#encoding: utf-8

"""
This settings module is dynamically populated by lib.check_settings.
"""

class REQUIRED:
    """
    This setting doesn't have default value
    """
    pass

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
RENKISRV_LISTEN_ADDRESS = '0.0.0.0'
RENKISRV_LISTEN_PORT = 6550
RENKISRV_LISTEN_SSL = True
RENKISRV_LISTEN_CERT = REQUIRED
RENKISRV_LISTEN_KEY = REQUIRED
RENKISRV_LISTEN_CA = None
KEY_EXPIRE_TIME = 86400
AUTH_SECRET = REQUIRED
