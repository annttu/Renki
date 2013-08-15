# encoding: utf-8

DEBUG = True
BIND_HOST = 'localhost'
BIND_PORT = 8080

######################
### Authentication ###
######################

AUTHENTICATION_MODULES = ('lib.auth.dummy.AuthenticationModule',)

###############
### Logging ###
###############

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
            'level': 'INFO',
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
        }
     }
}

