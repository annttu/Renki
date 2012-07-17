#!/usr/bin/env python
# encoding: utf-8
"""
host.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""
from exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class Hosts(object):
    

    def __init__(self,main):
        self.main = main
        self.a = 'a'
        self.log = logging.getLogger('services.databases')


class Host(object):
    """Create, modify and delete hosts
    host is usually server
    """
    
    def __init__(self,main):
        self.main = main
        self.name = None
        self.type = 'HARDWARE'
        self.domain = None
        self.host_id = None
        self.domain_id = None
        self.interfaces = []
        self.add_interfaces = []
        self.del_interfaces = []
        self.services = []
        self.add_services = []
        self.del_services = []
        self.customer_id = None
    
    def add_interface(self, name, ip_address, subnet_id, domains_id):
        """Add interface to host
        """
        iface = self.main.Interface()
        iface.t_subnets_id = interface.t_subnet_id
        iface.ip_address = ip_address
        iface.
        self.interfaces.append(iface)
        return True

    def del_interface(self, name=None, domain=None, domain_id=None, hostname=None, interface_id=None):
        """Delete given interface by 
         - hostname (name + domain)
         - name and domain
         - name and t_domains_id
         - interface_id
         - mac
        """
        if self.host_id is None:
            raise RuntimeError('No host selected!')
        if self.interfaces == []:
            raise DoesNotFound('Interface on host %s does not found' % self.name)
        if t_interfaces_id is not None:
            for interface in self.interfaces:
                if interface.t_interfaces_id == interface_id:
                    self.del_interfaces.append(interface)
                    return True
            for interface in self.del_interfaces:
                if interface.t_interfaces_id == interface_id:
                    # already about to be deleted
                    return True
            raise RuntimeError('Given interface %s does not found on host %s' % (interface_id, self.name))
        if hostname != None and hostname != '':
            try:
                domain = self.main.domains.get(hostname)
                domain_id = domain.t_domains_id
            except DoesNotExist:
                raise RuntimeError('Given interface %s does not found on host %s' % (interface_id, self.name))
            name = hostname[:len(domain.name)+1]
        elif name != None and domain != None:
            try:
                domain_id = self.main.domains.get(domain)
            except DoesNotFound:
                raise RuntimeError('Given interface %s domain %s does not found on host %s' % (name, domain, self.name))
        if name != None and domain_id != None:
            for interface in self.interfaces:
                if interface.name == name and inteface.t_domains_id == domain_id:
                    self.del_interfaces.append(interface)
                    return True
        raise RuntimeError('Invalid options given to del_interface')
            
    

    def get_interface(self,name, t_domains_id):
        """Get interface by name and t_domains_id"""
        if name != None and t_domains_id != None:
            query = self.main.session.query(self.main.Interfaces).filter(self.main.Interfaces.name == name)
            query = query.filter(self.main.Interfaces.t_domains_id = t_domains_id)
            try:
                retval = query.one()
                self.main.session.commit()
                return retval
            except NoResultsFound:
                raise DoesNotExist('Interface %s for host %s does not found' % (name, self.name))
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Database error')
        else:
            raise RuntimeError('Invalid name or t_domains_id given')

    def _verify_name(self):
        for char in self.name:
            if char not in self.name:
                return False
        return True

    def _verify_interface(self, interface):
        """TODO"""
        # subnet exist
        # ip in subnet
        pass

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
        
    def commit(self):
        """Commit changes to database
        """
        self.verify()
        if self.host_id is None:
            host = self.main.Host()
            host.name = self.name
            host.type = self.type
            host.t_domains_id = self.domain_id
            host.t_customers_id = self.customer_id
            try:
                self.main.session.add(host)
            except Exception as e:
                self.log.exception(e)
                raise RuntimeError('Cannot add host %s to database' % self.name)
        for interface in self.add_interfaces:
            interface.t_hosts_id = self.host_id
            self._verify_interface(interface)
            self.main.session.add(interface)

        for interface in self.del_interfaces:
            self.main.session.delete(interface)
            
        for service in self.add_services:
            self.main.session.add(service)
            
        for service in self.del_services:
            self.main.session.delete(service)
            
        try:
            self.main.session.commit()
        except Exception as e:
            self.log.exception(e)
            raise RuntimeError('Cannot commit host %s to database' % self.name)
            
    def __unicode__(self):
        return('Host %s' % self.name)