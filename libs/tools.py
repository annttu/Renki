#!/usr/bin/env python
# encoding: utf-8

"""Miscellaneous tools for services library"""

import struct

def valid_ipv6_address(address):
    """Validate ipv6 address"""
    if re.match('^([0-9a-f]{1,4}:)(([0-9a-f]{1,4}:){5,5}[0-9a-f]{0,4}|([0-9a-f]{1,4}:){1,5}:([0-9a-f]{1,4}:){0,5}([0-9a-f]{1,4}))(/128)?$', address):
        if len(address.split(':')) <= 8 and len(address.split(':')) >= 1:
            return True
    return False

def valid_ipv4_address(address):
    """Validate ipv4 address"""
    if re.match('^((25[0-5]|[0-2][0-4][0-9]|[0-9][0-9]).){4,4}(/30)?$'):
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
    if re.match('^((25[0-5]|[0-2][0-4][0-9]|[0-9][0-9]).){4,4}/([89]|[0-3][0-9])$'):
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
   print("%s %s" % (ip,ipaddr))
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
   print("%s %s" % (net, netaddr))
   netaddr = int(netaddr, 16)
   mask = (0xffffffffffffffffffffffffffffffff << (128 - int(bits))) & 0xffffffffffffffffffffffffffffffff
   return (ipaddr & mask) == (netaddr & mask)

def is_int(string):
    """test if string is int"""
    try:
        int(string)
        return True
    except:
        return False
