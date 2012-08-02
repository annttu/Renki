#!/usr/bin/env python
# encoding: utf-8
"""
user_port.py

This file is part of Services Python library and Renki project.

Licensed under MIT-license

Kapsi Internet-käyttäjät ry 2012
"""

from services.exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import MetaData, Table, Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import mapper, relationship


class User_ports(object):
    """Services user_ports service
    Initialize with Services object"""

    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.user_ports')
        self.database_loaded = False
        if not self.main.dynamic_load and not self.main.loaded:
            self._load_database()

    def _load_database(self):
        """Load database when needed"""
        if self.database_loaded or (self.main.loaded and not self.main.dynamic_load):
            return True
        user_ports = Table('user_ports', self.main.metadata,
            Column('t_user_ports_id', Integer, primary_key=True),
            Column('active', Boolean, default=True),
            Column("t_customers_id", Integer, ForeignKey('customers.t_customers_id')),
            Column("t_users_id", Integer, ForeignKey('users.t_users_id')),
            autoload=True)
        mapper(self.main.User_ports, user_ports, properties={
            'customer': relationship(self.main.Customers, backref='user_ports'),
            'user': relationship(self.main.Users, backref='user_ports'),
        })
        user_port_servers = Table('user_port_servers', self.main.metadata,
            Column("t_services_id", Integer, primary_key=True), autoload=True)
        mapper(self.main.User_port_servers, user_port_servers)
        self.database_loaded = True
        return True

    def list(self):
        """List all user ports
        """
        self._load_database()
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
        Returns port object on successful
        """
        self._load_database()
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
        self._load_database()
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
        Returns True on successful delete
        """
        self._load_database()
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
        Returns user_port_server object on success
        """
        self._load_database()
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
        Returns list of user_port_server objects on success
        """
        self._load_database()
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
