#!/usr/bin/env python
# encoding: utf-8

"""Miscellaneous tools for services library"""

import struct
import re
import logging

logger = logging.getLogger('libs.tools')

def valid_ipv6_address(address):
    """Validate ipv6 address"""
    if re.match('^([0-9a-f]{1,4}:)(([0-9a-f]{1,4}:){5,5}[0-9a-f]{0,4}|([0-9a-f]{1,4}:){1,5}:([0-9a-f]{1,4}:){0,5}([0-9a-f]{1,4}))(/128)?$', address):
        if len(address.split(':')) <= 8 and len(address.split(':')) >= 1:
            return True
    return False

def valid_ipv4_address(address):
    """Validate ipv4 address"""
    if re.match('^((25[012345]|2[01234][0-9]|[0-1]?[0-9]?[0-9])\.){3,3}(25[012345]|2[01234][0-9]|[0-1]?[0-9]?[0-9])(/30)?$', address):
        return True
    return False

def valid_ipv6_block(address):
    """Validate ipv6 block"""
    if re.match('^([0-9a-f]{1,4}:)(([0-9a-f]{1,4}:){5,5}[0-9a-f]{0,4}|([0-9a-f]{1,4}:){1,5}:([0-9a-f]{1,4}:){0,5}([0-9a-f]{0,4}))/([0-1][0-2][0-9]|[0-9][0-9])$', address):
        if len(address.split(':')) <= 8 and len(address.split(':')) >= 1:
            return True
    return False

def valid_ipv4_block(address):
    """Validate ipv4 block"""
    if re.match('^((25[0-5]|[0-2][0-4][0-9]|[0-9][0-9]).){4,4}/([89]|[0-3][0-9])$', address):
        return True
    return False

def ipv4_in_block(ip,net):
   "Is an address in a network"
   if len(ip.split('.')) != 4 or len(net.split('/')) != 4:
       return False
   ipaddr = int(''.join([ '%02x' % int(x) for x in ip.split('.') ]), 16)
   net,bits = net.split('/')
   if len(net.split('.')) != 4:
       return False
   netaddr = int(''.join([ '%02x' % int(x) for x in net.split('.') ]), 16)
   mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
   return (ipaddr & mask) == (netaddr & mask)

def ipv6_in_block(ip,net):
   "Is an address in a network"
   iplen = 9 - len(ip.split(':'))
   fill = ':'
   for i in range(0,iplen):
       fill += '0:'
   ip = ip.replace('::',fill)
   if len(ip.split(':')) != 8:
       return False
   ipaddr = ''.join([ '%04x' % int(x) for x in ip.split(':') ])
   ipaddr = int(ipaddr, 16)
   net,bits = net.split('/')
   netlen = 9 - len(net.split(':'))
   fill = ':'
   for i in range(0,netlen):
       fill += '0:'
   net = net.replace('::',fill)
   if net.endswith(':'):
       net += '0'
   if len(net.split(':')) != 8:
       return False
   netaddr = ''.join([ '%04x' % int(x) for x in net.split(':') ])
   netaddr = int(netaddr, 16)
   mask = (0xffffffffffffffffffffffffffffffff << (128 - int(bits))) & 0xffffffffffffffffffffffffffffffff
   return (ipaddr & mask) == (netaddr & mask)

def valid_fqdn(string):
    string = string.split('.')
    if len(string) < 2:
        return False

    # tld contains only letters
    for char in string[-1]:
        if not char.isalpha():
            return False

    # main part of domain should be at least two chars long
    if len(string[-2]) < 2:
        return False

    # Don't allow ower six dots on address
    if len(string) > 6:
        return False

    for substring in string:
        if len(substring) < 1:
            return False
        if not substring[0].isalpha() and not substring[0].isdigit():
            return False
        elif not substring[-1].isalpha() and not substring[-1].isdigit():
            return False
        for char in substring:
            if not char.isalpha() and not char.isdigit() and not char in "-":
                return False

    return True

def is_int(string):
    """test if string is int"""
    try:
        int(string)
        return True
    except:
        return False

def idna_address(address):
    """IDNA-encode mail-address"""
    if len(address.split('@') < 2):
        return idna_domain(address)
    domainpart = address.split('@')[-1]
    name = address.split('@')[:-1]
    domainpart = domainpart.encode('idna').decode()
    return '%s@%s' % (name, domainpart)

def idna_domain(domain):
    """IDNA-encode domain"""
    return domain.encode('idna').decode()

def is_bool(value):
    return value in [True, False]
