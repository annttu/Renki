# encoding: utf-8


from .dns_zone_database import *
from .dns_zone_routes import *

# Default settings, these can be overwritten in local settings.py
from lib import renki_settings as settings
settings.DNS_ZONE_REFRESH = 10800
settings.DNS_ZONE_RETRY = 7200
settings.DNS_ZONE_EXPIRE = 1209600
settings.DNS_ZONE_TTL = 21600
settings.DNS_ZONE_RNAME = 'root.localhost'
settings.DNS_ZONE_RECORD_TTL = 3600
