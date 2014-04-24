# encoding: utf-8

import settings

import logging
import logging.config
from lib import renki_settings as rsettings


def import_modules(modules):
    imported_modules = []
    import_failed = None
    for mod in modules:
        try:
            from_ = '.'.join(mod.split('.')[:-1])
            module_ = mod.split('.')[-1]
            authmod = __import__(from_, fromlist=[module_])
            imported_modules.append(vars(authmod)[module_]())
        except ImportError as e:
            import_failed = e
            break
    if import_failed:
        raise SettingError('Cannot import module: %s' %
                           import_failed)
    return imported_modules

def set_settings():
    """
    Populate renki_settings module with values set in settings.py and
    local_settings.py
    """
    ignored = ['Condition', 'REQUIRED', 'REQUIREDIF', 'CHECKVALUE',
               'SettingError']
    # Copy obvious values
    defaults = vars(rsettings).copy()
    for name, default in defaults.items():
        if name.startswith('__') or name in ignored or isinstance(default, type):
            continue
        value = getattr(settings, name, None)
        if issubclass(default.__class__, rsettings.Condition):
            value = default.check(rsettings, value)
        elif value is None:
            continue
        setattr(rsettings, name, value)

    # Import authentication module
    rsettings.AUTHENTICATION_MODULES = import_modules(
                                            settings.AUTHENTICATION_MODULES)

    logging.config.dictConfig(rsettings.LOGGING)
