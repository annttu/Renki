#!/usr/bin/env python
# encoding: utf-8
"""
host.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""
from services.exceptions import *
from sqlalchemy.dialects.postgresql import INET, MACADDR
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, Boolean, ForeignKey, String, Enum
from sqlalchemy.orm import mapper, relationship

from services.libs.tools import valid_ipv4_block, valid_ipv6_block, valid_ipv6_address, valid_ipv4_address, ipv4_in_block, ipv6_in_block, is_int

class Hosts(object):

    def __init__(self,main):
        self.main = main
        self.a = 'a'
        self.log = logging.getLogger('services.hosts')
        self.main.require_admin()
        self.database_loaded = False
        if not self.main.dynamic_load and not self.main.loaded:
            self._load_database()

    def _load_database(self):
        """Dynamically load database when needed"""
        if self.database_loaded:
            return True
        ## load subnets before that
        self.main.subnets._load_database()
        hosts = Table('t_hosts', self.main.metadata,
            Column("t_hosts_id", Integer, primary_key=True),
            Column('name', String, primary_key=False, nullable=False),
            Column('type', Enum('HARDWARE', 'VIRTUAL'), primary_key=False, nullable=False, default="'VIRTUAL'::t_hosts_type"),
            Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id')),
            Column('t_customers_id', Integer, ForeignKey('customers.t_customers_id'), primary_key=False),
            Column('location', String, primary_key=False, nullable=False, default=''))
            #,autoload=True)
        mapper(self.main.Hosts, hosts, properties={
            'domain': relationship(self.main.Domains, backref='hosts'),
            'customer': relationship(self.main.Customers, backref='hosts')
            })
        addresses = Table('t_addresses', self.main.metadata,
            Column("t_addresses_id", Integer, primary_key=True),
            Column("t_hosts_id", Integer, ForeignKey('t_hosts.t_hosts_id'), nullable=False),
            Column("t_domains_id", Integer, ForeignKey('domains.t_domains_id'), nullable=False),
            Column('t_subnets_id', Integer, ForeignKey('t_subnets.t_subnets_id'), primary_key=False, nullable=False),
            Column('ip_address', INET(), primary_key=False, nullable=False),
            Column('name', String, primary_key=False, nullable=False),
            Column('info', String, primary_key=False),
            Column('active', Boolean, primary_key=False, nullable=False, default='true'),
            Column('mac_address', MACADDR(), primary_key=False),
            )
            #,autoload=True)
        mapper(self.main.Addresses, addresses, properties={
            'host': relationship(self.main.Hosts, backref='addresses'),
            'domain': relationship(self.main.Domains, backref='addresses'),
            'subnet': relationship(self.main.Subnets, backref='addresses')
        })
        self.database_loaded = True
        return True

    def get(self,name=None,domain_id=None,domain=None,hostname=None,host_id=None):
        """Get host by
        name and domain or
        name and domain_id or
        host_id or
        hostname (host + domain)
        raises DoesNotExist if does not exist
        raises RuntimeError on error
        """
        self._load_database()
        host = self.host()
        host.get(name=name,domain_id=domain_id,domain=domain,host_id=host_id,hostname=hostname)
        return host.object

    def host(self):
        self._load_database()
        return Host(self.main)

class Host(object):
    """Create, modify and delete hosts
    host is usually server
    """

    def __init__(self,main):
        self.log = logging.getLogger('services.hosts')
        self.main = main
        self.object = None
        self.name = None
        self.type = 'HARDWARE'
        self.domain = None
        self.host_id = None
        self.domain_id = None
        self.addresses = []
        self.add_addresses = []
        self.del_addresses = []
        self.services = []
        self.add_services = []
        self.del_services = []
        self.customer_id = None

    def add_address(self, name, ip_address, subnet_id, domain_id, mac=None):
        """Add address to host
        """
        address = self.main.Addresses()
        address.t_subnets_id = subnet_id
        address.ip_address = ip_address
        address.name = name
        address.t_domains_id = domain_id
        address.mac = mac
        #see commit
        #address.t_hosts_id = self.host_id
        self.addresses.append(iface)
        return True

    def del_address(self, name=None, domain=None, domain_id=None, hostname=None, address_id=None):
        """Delete given address by
         - hostname (name + domain)
         - name and domain
         - name and t_domains_id
         - address_id
         - mac
        """
        if self.host_id is None:
            raise RuntimeError('No host selected!')
        if self.addresses == []:
            raise DoesNotFound('Interface on host %s does not found' % self.name)
        if addresses_id is not None:
            for address in self.addresses:
                if addresses.t_addresses_id == address_id:
                    self.del_addresses.append(address)
                    return True
            for address in self.del_addresses:
                if address.t_addresses_id == address_id:
                    # already about to be deleted
                    return True
            raise RuntimeError('Given address %s does not found on host %s' % (address_id, self.name))
        if hostname != None and hostname != '':
            try:
                domain = self.main.domains.get(hostname)
                domain_id = domain.t_domains_id
            except DoesNotExist:
                raise RuntimeError('Given address %s does not found on host %s' % (address_id, self.name))
            name = hostname[:len(domain.name)+1]
        elif name != None and domain != None:
            try:
                domain_id = self.main.domains.get(domain)
            except DoesNotFound:
                raise RuntimeError('Given address %s domain %s does not found on host %s' % (name, domain, self.name))
        if name != None and domain_id != None:
            for address in self.addresses:
                if address.name == name and inteface.t_domains_id == domain_id:
                    self.del_addresses.append(address)
                    return True
        raise RuntimeError('Invalid options given to del_address')

    def get_address(self,name, t_domains_id):
        """Get address by name and t_domains_id"""
        if name != None and t_domains_id != None:
            query = self.main.session.query(self.main.Interfaces).filter(self.main.Interfaces.name == name)
            query = query.filter(self.main.Interfaces.t_domains_id == t_domains_id)
            try:
                retval = query.one()
                self.main.session.commit()
                return retval
            except NoResultFound:
                raise DoesNotExist('Interface %s for host %s does not found' % (name, self.name))
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Database error')
        else:
            raise RuntimeError('Invalid name or t_domains_id given')

    def _verify_name(self):
        for char in self.name:
            if char not in 'abcdefghijklmnopqrstuvwxyz0123456789-_.':
                return False
        return True

    def _verify_address(self, address):
        """verify address object validity"""
        if self.host_id is None:
            raise RuntimeError('Cannot add address without selecting host first')
        try:
            # is subnet exist?
            subnet = self.main.subnets.get(address.t_subnets_id)
        except DoesNotExist as e:
            raise RuntimeError('Invalid subnet_id %s' % address.t_subnets_id)
        if not ipv6_in_block(address.ip_address, subnet.address) and not ipv4_in_block(address.ip_address, subnet.address):
            # ip not in subnet
            raise RuntimeError('Address %s not in subnet %s' % (address.ip_address, subnet.address))
        if subnet.dhcp_range is not None:
            if ipv4_in_block(address.ip_address, subnet.dhcp_range) or ipv6_in_block(address.ip_address, subnet.dhcp_range):
                # ip in dhcp_range
                raise RuntimeError('Address %s is in subnet dhcp_range %s' % (address.ip_address, subnet.dhcp_range))
        return True

    def verify(self):
        """Verify host data"""
        if self.main.customer_id == None:
            raise RuntimeError('Cannot add host without customer_id')
        else:
            try:
                self.customer_id = int(self.main.customer_id)
            except ValueError:
                raise RuntimeError('Invalid customer_id %s' % self.main.customer_id)
        if self.name == None or self._verify_name() is False:
            raise RuntimeError('Invalid hostname %s' % self.name)
        self.type = self.type.upper()
        if self.type not in ['VIRTUAL','HARDWARE']:
            raise RuntimeError('Invalid host type %s, valid values are VIRTUAL and HARDWARE' % self.type)
        try:
            self.domain_id = self.main.domains.get(str(self.domain)).t_domains_id
        except DoesNotExist:
            raise RuntimeError('Domain %s does not exist' % self.domain)
        return True

    def get(self, name=None, domain=None, domain_id=None, hostname=None, host_id=None):
        """Get host by
        name and domain or
        name and domain_id or
        hostname (name + domain) or
        host_id"""
        query = self.main.session.query(self.main.Hosts)
        if host_id is not None and is_int(host_id):
            query = query.filter(self.main.Hosts.t_hosts_id==host_id)
        elif name is not None:
            if domain is not None:
                try:
                    domain = self.main.domains.get(domain)
                    domain_id = domain.t_domains_id
                    query = query.filter(self.main.Hosts.t_domains_id == domain_id)
                    query = query.filter(self.main.Hosts.name == name)
                except DoesNotExist:
                    raise DoesNotExist('Domain %s does not exist' % domain)
            elif domain_id is not None and is_int(domain_id):
                domain_id = int(domain_id)
                query = query.filter(self.main.Hosts.t_domains_id == domain_id)
                query = query.filter(self.main.Hosts.name == name)
            else:
                self.log.error('Invalid host.get call name=%s, domain=%s, domain_id=%s, hostname=%s, host_id=%s' % (name, domain, domain_id, hostname, host_id))
                raise RuntimeError('Give either domain or domain_id!')
        elif hostname:
            try:
                domain = self.main.domains.get(hostname)
            except DoesNotExist:
                raise DoesNotExist('Domain for hostname %s does not found' % hostname)
            name = hostname[:-(len(domain.name)+1)]
            query = query.filter(self.main.Hosts.t_domains_id == domain.t_domains_id)
            query = query.filter(self.main.Hosts.name == name)
        else:
            self.log.error('Invalid host.get call name=%s, domain=%s, domain_id=%s, hostname=%s, host_id=%s' % (name, domain, domain_id, hostname, host_id))
            raise RuntimeError('Invalid options given')
        try:
            retval = query.one()
            self.object = retval
            self.main.session.commit()
            self.host_id = retval.t_hosts_id
            self.name = retval.name
            self.type = retval.type
            self.domain_id = retval.t_domains_id
            self.customer_id = retval.t_customers_id
            self.location = retval.location

        except NoResultFound as e:
            raise DoesNotExist('Host does not found')
        except Exception as e:
            self.log.exception(e)
            raise RuntimeError('Error while getting host')

    def commit(self):
        """Commit changes to database
        """
        self.verify()
        changes = False
        if self.host_id is None:
            host = self.main.Host()
            host.name = self.name
            host.type = self.type
            host.location = self.location
            host.t_domains_id = self.domain_id
            host.t_customers_id = self.customer_id
            try:
                self.main.session.add(host)
                changes = True
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Cannot add host %s to database' % self.name)
        else:
            if self.object.name != self.name:
                self.object.name = self.name
                changes = True
            if self.object.type != self.type:
                self.object.type = self.type
                changes = True
            if self.object.location != self.location:
                self.object.location = self.location
                changes = True
            if self.object.t_domains_id != self.domain_id:
                self.object.t_domains_id = self.domain_id
                changes = True
            if self.object.t_custoemrs_id != self.customer_id:
                self.object.t_customers_id = self.customer_id
                changes = True

        for address in self.add_addresses:
            address.t_hosts_id = self.host_id
            self._verify_address(address)
            self.main.session.add(address)
            changes = True

        for address in self.del_addresses:
            self.main.session.delete(address)
            changes = True

        for service in self.add_services:
            self.main.session.add(service)
            changes = True

        for service in self.del_services:
            self.main.session.delete(service)
            changes = True

        if changes:
            try:
                self.main.session.commit()
                if self.host_id is None:
                    self.host_id = host.host_id
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Cannot commit host %s to database' % self.name)

    def __unicode__(self):
        return('Host %s' % self.name)