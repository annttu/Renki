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
            'formatter': 'simple'
        }
    },
    'loggers': {
        'routes': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'server': {
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
        'database/routes': {
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
        }
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
KEY_EXPIRE_TIME = 86400
AUTH_SECRET = REQUIRED
