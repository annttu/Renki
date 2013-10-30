# encoding: utf-8

import settings
from .exceptions import SettingError

import logging
import logging.config

LOGGING = {}
_ARGS = [('DEBUG', False),
         ('BIND_HOST', 'localhost'),
         ('BIND_PORT', 8080),
         ('LOGGING', {}),
         ('DB_DATABASE', 'renki'),
         ('DB_USER', 'renki'),
         ('DB_PASSWORD', ''),
         ('DB_SERVER', 'localhost'),
         ('DB_PORT', 5432),
         ('DB_TEST_DATABASE', 'renki_test'),
         ('DB_TEST_USER', 'renki'),
         ('DB_TEST_PASSWORD', ''),
         ('DB_TEST_SERVER', 'localhost'),
         ('DB_TEST_PORT', 5432),
         ('KEY_EXPIRE_TIME', 86400)
]

# Copy obvious values
for it in _ARGS:
    name = it[0]
    globals()[name] = getattr(settings, name, it[1])


# Import authentication module
AUTHENTICATION_MODULES = []
import_failed = None
for mod in settings.AUTHENTICATION_MODULES:
    try:
        from_ = '.'.join(mod.split('.')[:-1])
        module_ = mod.split('.')[-1]
        authmod = __import__(from_, fromlist=[module_])
        AUTHENTICATION_MODULES.append(vars(authmod)[module_]())
    except ImportError as e:
        import_failed = e
        break
if import_failed:
    raise SettingError('Cannot import module: %s' %
                       import_failed)


logging.config.dictConfig(LOGGING)
