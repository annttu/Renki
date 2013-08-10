#!/usr/bin/env python
# encoding: utf-8

"""
database.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""

from services.exceptions import *
from sqlalchemy.dialects.postgresql import INET, ARRAY
import logging
import re
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy.orm import mapper

from services.libs.tools import valid_ipv4_block, valid_ipv6_block, valid_ipv6_address, valid_ipv4_address

ipv6_pattern="^([0-9a-f]{1,4}:)((:[0-9a-f]{1,4}){1,6}|:[0-9a-f]{1,4}){1,6})"


class Subnets(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.subnets')
        self.main.require_admin()
        self.database_loaded = False
        if not self.main.dynamic_load and not self.main.loaded:
            self._load_database()

    def _load_database(self):
        """Dynamically load database when needed"""
        if self.database_loaded or (self.main.loaded and not self.main.dynamic_load):
            return True
        subnets = Table('t_subnets', self.main.metadata,
            Column("t_subnets_id", Integer, primary_key=True),
            Column('name', String, primary_key=False, nullable=False),
            Column('location', String, primary_key=False, nullable=False),
            Column('info', String, primary_key=False),
            Column('vlan_tag', Integer, primary_key=False, nullable=False, default='0'),
            Column('address', INET(), primary_key=False, nullable=False),
            Column('gateway', INET(), primary_key=False),
            Column('dns_servers', ARRAY(INET()), primary_key=False),
            Column('dhcp_range', INET(), primary_key=False),
            Column('dhcp_options', String, primary_key=False),
            Column('mtu', Integer, primary_key=False, nullable=False, default='1500'),
            Column('hostmaster_address', String, primary_key=False, nullable=False, default=self.main.defaults.hostmaster_address)
            #,autoload=True
            )
        mapper(self.main.Subnets, subnets)
        self.database_loaded = True
        return True

    def subnet(self):
        self._load_database()
        return Subnet(self.main)

    def get(self,name=None,location=None,subnet_id=None):
        """Get subnet"""
        self._load_database()
        subnet = self.subnet()
        subnet.get(name,location=location,subnet_id=subnet_id)
        return subnet.object

    def list(self):
        """List all subnets"""
        self._load_database()
        retval = self.main.session.query(self.main.Subnets).all()
        self.main.session.commit()
        return retval


class Subnet(object):
    """Subnet object"""
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.subnets')
        self.object = None
        self.address = None
        self.gateway = None
        self.dns_servers = []
        self.dhcp_range = None
        self.dhcp_options = None
        self.mtu = 1500
        self.vlan_tag = 0
        self.info = None
        self.location = None
        self.name = None
        self.subnet_id = None
        self.hostmaster_address = self.main.defaults.hostmaster_address

    def get(self,name=None,subnet_id=None,location=None):
        """Get subnet object by
        subnet_id or name (and location)
        """
        query = self.main.session.query(self.main.Subnets)
        if subnet_id is not None:
            query = query.filter(self.main.Subnets.t_subnets_id == subnet_id)
        elif name is not None:
            if location is not None:
                query = query.filter(self.main.Subnets.location == location)
            query = query.filter(self.main.Subnets.name == name)
        else:
            raise RuntimeError('Invalid parameters to subnet.get')
        try:
            self.object = query.one()
            self.main.session.commit()
            self.address = self.object.address
            self.gateway = self.object.gateway
            self.dns_servers = self.object.dns_servers
            self.dhcp_range = self.object.dhcp_range
            self.dhcp_options = self.object.dhcp_options
            self.location = self.object.location
            self.name = self.object.name
            self.vlan_tag = self.object.vlan_tag
            self.subnet_id = self.object.t_subnets_id
            self.hostmaster_address = self.object.hostmaster_address

        except NoResultsFound:
            if name != None:
                raise DoesNotFound('Subnet %s does not found' % name)
            else:
                raise DoesNotFound('Subnet %s does not found' % subnet_id)
        except Exception as e:
            self.log.exception(e)
            if name != None:
                raise DoesNotFound('Error getting subnet %s' % name)
            else:
                raise DoesNotFound('Error getting subnet %s' % subnet_id)

    def delete(self):
        """Delete this object"""
        if not self.object:
            raise RuntimeError('Select subnet first!')
        self.main.session.delete(self.object)
        self.main.session.commit()

    def validate(self):
        """Validate object"""
        if self.name is None or self.name is '':
            raise RuntimeError('Cannot create subnet without name')
        if self.location is None or self.location is '':
            raise RuntimeError('Cannot create subnet without location')
        if self.address is None or self.addess is '':
            raise RuntimeError('Cannot create subnet without address')
        if not valid_ipv4_block(self.address) and not valid_ipv6_block(self.address):
            raise RuntimeError('Invalid address block %s' % self.address)
        if self.gateway is not None:
            if not valid_ipv4_address(self.gateway) and not valid_ipv6_address(self.gateway):
                raise RuntimeError('Invalid gateway address %s' % self.gateway)
        if self.dhcp_range is not None:
            if not valid_ipv4_block(self.dhcp_range) and not valid_ipv6_block(self.dhcp_range):
                raise RuntimeError('Invalid dhcp_range %s' % self.dhcp_range)
        for dns_server in self.dns_servers:
            if not valid_ipv4_address(dns_server) and not valid_ipv6_address(dns_server):
                raise RuntimeError('Invalid dns_server %s' % dns_server)
        try:
            self.mtu = int(self.mtu)
        except:
            raise RuntimeError('Invalid mtu %s given' % self.mtu)
        if self.mtu < 1500 or self.mtu > 15500:
            raise RuntimeError('Invalid mtu %s given, must be over 1499 and under 15501' % self.mtu)
        try:
            self.vlan_tag = int(self.vlan_tag)
        except:
            raise RuntimeError('Invalid vlan_tag %s given' % self.vlan_tag)
        if self.vlan_tag < 0 or self.vlan_tag > 65536:
            raise RuntimeError('Invalid vlan_tag %s given, must be >= 0 and <= 65536' % self.vlan_tag)
        if '@' not in self.hostmaster_address or len(self.hostmaster_address) < 5 or len(self.hostmaster_address.split('@')) != 2:
            raise RuntimeError('Invalid hostmaster_address %s' % self.hostmaster_address)

    def commit(self):
        """Commit data to database"""
        if self.subnet_id is None:
            # new object
            self.object = self.main.Subnets()
        self.object.address = self.address
        self.object.name = self.name
        self.object.location = self.location
        self.object.info = self.info
        self.object.vlan_tag = self.vlan_tag
        self.object.address = self.address
        self.object.gateway = self.gateway
        self.object.dns_servers = self.dns_servers
        self.object.dhcp_range = self.dhcp_range
        self.object.dhcp_options = self.dhcp_options
        self.object.mtu = self.mtu
        self.object.hostmaster_address = self.hostmaster_address
        try:
            if self.subnet_id is None:
                self.main.session.add(self.object)
            self.main.session.commit()
            self.subnet_id = self.object.t_subnets_id
        except Exception as e:
            self.log.exception(e)
            raise RuntimeError('Cannot commit data to database, got error %s' % e)
