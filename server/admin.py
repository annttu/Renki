#!/usr/bin/env python
# encoding: utf-8


from lib import check_settings
from lib.database import basic_tables
from lib.database.basic_tables import ServiceDatabase, ServerGroupDatabase
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
    Add lakka and hilla servers and create service for them
    """
    if not ServiceDatabase.query().filter(ServiceDatabase.name == 'TestService').all():
        service = ServiceDatabase()
        service.name = 'TestService'
        service.save()
        dbsession.commit()
    else:
        service = ServiceDatabase.query().filter(ServiceDatabase.name == 'TestService').one()

    if not ServerGroupDatabase.query().filter(ServerGroupDatabase.name == 'Lakka').all():
        lakka = ServerGroupDatabase()
        lakka.name = "Lakka"
        lakka.service = service
        lakka.save()
        dbsession.commit()
    else:
        lakka = ServerGroupDatabase.query().filter(ServerGroupDatabase.name == 'Lakka').one()

    if not ServerGroupDatabase.query().filter(ServerGroupDatabase.name == 'Hilla').all():
        hilla = ServerGroupDatabase()
        hilla.name = "Hilla"
        hilla.service = service
        hilla.save()
        dbsession.commit()
    else:
        hilla = ServerGroupDatabase.query().filter(ServerGroupDatabase.name == 'Hilla').one()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Admin util for renkiserver')
    parser.add_argument('--sync-database', help="Syncronize database",
                        action="store_true", default=False)
    parser.add_argument('--development-setup', help="Setup dummy users",
                        action="store_true", default=False)
    parser.add_argument('--drop_tables', help="Drop tables",
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
