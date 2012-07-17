#!/usr/bin/env python
# encoding: utf-8
"""
user_port.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""

from exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class User_ports(object):
    """Services user_ports service
    Initialize with Services object"""

    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.user_ports')

    def list(self):
        ports = self.main.session.query(self.main.User_ports)
        if self.main.customer_id:
            ports = ports.filter(self.main.User_ports.t_customers_id==self.main.customer_id)
        if self.main.username:
            ports = ports.filter(self.main.User_ports.username == self.main.username)
        retval = ports.all()
        self.main.session.commit()
        return retval

    def get(self, server, port):
        """Get user port on <server>
        Raises DoesNotExist if not found
        Returns port object on successful """
        try:
            port = int(port)
        except ValueError:
            raise RuntimeError('Port must be integer!')
        query = self.main.session.query(self.main.User_ports).filter(self.main.User_ports.server == server, self.main.User_ports.port == port)
        if self.main.customer_id:
            query = query.filter(self.main.User_ports.t_customers_id == self.main.customer_id)
        if self.main.customer_id:
            query = query.filter(self.main.User_ports.username == self.main.username)
        try:
            retval = query.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Port %d on server %s not found' % (port, server))

    def add(self, server):
        """Open port on given <server>
        Raises RuntimeError if server not found
        Raises RuntimeError on error
        returns opened port
        """
        try:
           host = self.get_server(server)
        except DoesNotExist:
            raise RuntimeError('Server %s does not found!' % server)
        if not self.main.username or self.main.username == '':
            raise RuntimeError('Cannot add port without username')
        port = self.main.User_ports()
        port.t_customers_id = self.main.customer_id
        port.username = self.main.username
        port.server = host.server
        self.main.session.add(port)
        try:
            self.main.session.commit()
        except IntegrityError as e:
            self.main.session.rollback()
            self.main.log.error('Cannot commit to database %s' % e)
            self.main.log.exception(e)
            raise RuntimeError('Cannot commit to database %s' % e)
        return port.port

    def delete(self, server, port):
        """Delete <port> on <server>
        Raises RuntimeError on database error
        Returns True on successful delete"""
        port = self.get_user_port(server, port)
        try:
            self.main.session.delete(port)
            self.main.session.commit()
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.error('Cannot commit to database %s' % e)
            self.log.exception(e)
            raise RuntimeError('Cannot commit to database %s' % e)
        return True

    def get_server(self,server):
        """Get shell server object by name
        Raises RuntimeError on database error
        Raises NoResultFound if no result found
        Returns user_port_server object on success"""
        try:
            retval = self.main.session.query(self.main.User_port_servers).filter(self.main.User_port_servers.server==server).one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Host %s does not exist' % server)
        except OperationalError as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Cannot get server %s' % server)
            
    def list_servers(self):
        """Get shell servers list
        Raises RuntimeError on database error
        Returns list of user_port_server objects on success"""
        try:
            retval = self.main.session.query(self.main.User_port_servers).all()
            self.main.session.commit()
            return retval
        except Exception as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Cannot server list')
        except:
            self.log.error('Unknown error while getting user_ports server_list')
            return RuntimeError('Cannot get server list')
