#!/usr/bin/env python
# encoding: utf-8

from lib import check_settings
from lib.database import basic_tables
from lib.database.basic_tables import ServiceDatabase, ServiceGroupDatabase, ServerDatabase
from lib.database import tables
from lib.database import connection
from lib.database.connection import session as dbsession
from lib.auth import permissions
#from lib.database.connection import DBConnection
# Import modules to get all tables registered
import modules
from lib.auth import db

import logging
import logging.config
import argparse
import sys

logger = logging.getLogger('admin')

DEBUG=False

def init():
    check_settings.set_settings()
    connection.initialize_connection(echo=DEBUG)

def create_tables():
    """
    Create database tables
    """
    check_settings.set_settings()
    connection.initialize_connection(echo=DEBUG)
    logger.info("Creating tables")
    for table in tables.TABLES:
        logger.info("Table: %s" % table.__tablename__)
    connection.conn.create_tables()
    logger.info("All tables created")

def drop_tables():
    """
    Create database tables
    """
    check_settings.set_settings()
    connection.initialize_connection(echo=DEBUG)
    logger.info("Dropping tables")
    for table in tables.TABLES:
        logger.info("Table: %s" % table.__tablename__)
    connection.conn.drop_tables()
    logger.info("All tables dropped")

def create_permissions():
    for permission in permissions.PERMISSIONS:
        if not db.Permissions.query().filter(
                                    db.Permissions.name == permission).all():
            p = db.Permissions()
            p.name = permission
            p.save()


def add_user(userid, username, password, firstnames, lastname):
    user = db.Users()
    user.id = userid
    user.name = username
    user.set_password(password)
    user.firstnames = firstnames
    user.lastname = lastname
    user.save()
    return user

def setup_development_users():
    """
    Add test and admin users and proper permissions to them
    """
    if not db.Users().query().filter(db.Users.name == 'admin').all():
        admin = add_user(0, 'admin', 'admin', 'Antero', 'Admin')
    else:
        admin = db.Users().query().filter(db.Users.name == 'admin').one()
    if not db.Users().query().filter(db.Users.name == 'test').all():
        test =  add_user(1, 'test','test', 'Pertti', 'Testaaja')
    else:
        test = db.Users().query().filter(db.Users.name == 'test').one()

    for perm in db.Permissions.query().all():
        if perm.name.endswith('own'):
            test.permissions.append(perm)
        admin.permissions.append(perm)
    test.save()
    admin.save()

def setup_development_servers():
    """
    Add lakka and hilla servers and create couple services and service groups
    """
    if not ServerDatabase.query().filter(ServerDatabase.name == 'Hilla').all():
        hilla = ServerDatabase()
        hilla.name = 'Hilla'
        hilla.save()
    else:
        hilla = ServerDatabase.query().filter(ServerDatabase.name == 'Hilla').one()

    if not ServerDatabase.query().filter(ServerDatabase.name == 'Lakka').all():
        lakka = ServerDatabase()
        lakka.name = 'Lakka'
        lakka.save()
    else:
        lakka = ServerDatabase.query().filter(ServerDatabase.name == 'Lakka').one()

    if not ServerDatabase.query().filter(ServerDatabase.name == 'db1').all():
        db1 = ServerDatabase()
        db1.name = 'db1'
        db1.save()
    else:
        db1 = ServerDatabase.query().filter(ServerDatabase.name == 'db1').one()

    if not ServerDatabase.query().filter(ServerDatabase.name == 'db2').all():
        db2 = ServerDatabase()
        db2.name = 'db2'
        db2.save()
    else:
        db2 = ServerDatabase.query().filter(ServerDatabase.name == 'db2').one()

    if not ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Hilla_ports').all():
        hilla_ports = ServiceGroupDatabase()
        hilla_ports.name = 'Hilla_ports'
        hilla_ports.type = 'port'
        hilla_ports.save()
    else:
        hilla_ports = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Hilla_ports').one()

    if not ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Lakka_ports').all():
        lakka_ports = ServiceGroupDatabase()
        lakka_ports.name = 'Lakka_ports'
        lakka_ports.type = 'port'
        lakka_ports.save()
    else:
        lakka_ports = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Lakka_ports').one()

    if not ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Mysql_databases').all():
        mysql_databases = ServiceGroupDatabase()
        mysql_databases.name = 'Mysql_databases'
        mysql_databases.type = 'mysql_database'
        mysql_databases.save()
    else:
        mysql_databases = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Mysql_databases').one()

    if not ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Psql_databases').all():
        psql_databases = ServiceGroupDatabase()
        psql_databases.name = 'Psql_databases'
        psql_databases.type = 'Psql_database'
        psql_databases.save()
    else:
        psql_databases = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.name == 'Psql_databases').one()

    dbsession.flush()

    if not ServiceDatabase.query().filter(ServiceDatabase.name == 'Mysql_database').all():
        mysql_database = ServiceDatabase()
        mysql_database.name = 'Mysql_Database'
        mysql_database.service_group = mysql_databases
        mysql_database.server = hilla
        mysql_database.save()
    else:
        mysql_database = ServiceDatabase.query().filter(ServiceDatabase.name == 'Mysql_database').one()

    if not ServiceDatabase.query().filter(ServiceDatabase.name == 'Psql_database').all():
        psql_database = ServiceDatabase()
        psql_database.name = 'Psql_database'
        psql_database.service_group = psql_databases
        psql_database.server = hilla
        psql_database.save()
    else:
        psql_database = ServiceDatabase.query().filter(ServiceDatabase.name == 'Psql_database').one()

    if not ServiceDatabase.query().filter(ServiceDatabase.name == 'Hilla_port').all():
        hilla_port = ServiceDatabase()
        hilla_port.name = 'Hilla_port'
        hilla_port.service_group = hilla_ports
        hilla_port.server = hilla
        hilla_port.save()
    else:
        hilla_port = ServiceDatabase.query().filter(ServiceDatabase.name == 'Hilla_port').one()

    if not ServiceDatabase.query().filter(ServiceDatabase.name == 'Lakka_port').all():
        lakka_port = ServiceDatabase()
        lakka_port.name = 'Lakka_port'
        lakka_port.service_group = lakka_ports
        lakka_port.server = hilla
        lakka_port.save()
    else:
        lakka_port = ServiceDatabase.query().filter(ServiceDatabase.name == 'Lakka_port').one()
    dbsession.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Admin util for renkiserver')
    parser.add_argument('--sync-database', help="Syncronize database",
                        action="store_true", default=False)
    parser.add_argument('--development-setup', help="Setup dummy users",
                        action="store_true", default=False)
    parser.add_argument('--drop-tables', help="Drop tables",
                        action="store_true", default=False)
    parser.add_argument('-d', '--debug', help="Debug", action="store_true",
                        default=False)

    args = parser.parse_args()
    if args.debug is True:
        DEBUG = True
        logger.setLevel(logging.DEBUG)
    else:
        DEBUG = False
        logger.setLevel(logging.ERROR)
    if args.sync_database is True:
        init()
        create_tables()
        create_permissions()
    elif args.development_setup is True:
        init()
        setup_development_users()
        setup_development_servers()
    elif args.drop_tables is True:
        init()
        drop_tables()
    else:
        parser.print_help()
        sys.exit(1)
    connection.session.commit()
