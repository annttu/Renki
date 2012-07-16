#!/usr/bin/env python
# encoding: utf-8

from exceptions import *
import logging
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class Database(object):
    def __init__(self,main):
        self.main = main
        self.log = logging.getLogger('services.databases')
        self.type = ''

    ### databases ###

    def require_database_alias(self,alias):
        """Check if there is alias row for <alias>"""
        aliases = self.main.list_aliases()
        for a in aliases:
            if alias.startswith("%s_" % a) or alias == a:
                return True
        raise RuntimeError('No alias found for database %s' % alias)

    def valid_dbtype(self):
        """Check if <dbtype> is valid sql database type"""
        if self.type in ['MYSQL','POSTGRESQL']:
            return True
        return False

    def get_sql_database(self,server,database):
        """Get user's <database> on <server>
        return database object on success
        raise DoesNotExist if does not exist
        raise RuntimeError on database error"""
        serv = self.get_sql_server(server)
        query = self.main.session.query(self.main.Databases).filter(self.main.Databases.server==serv.server)
        query = query.filter(self.main.Databases.database_name == str(database))
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        if self.main.customer_id:
            query = query.filter(self.main.Databases.t_customers_id==self.main.customer_id)
        else:
            self.main.require_admin()
        try:
            query = query.filter(self.main.Databases.database_type==self.type).filter(self.main.Databases.database_name == database)
            query = query.filter(self.main.Databases.server == serv.server)
            retval = query.one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotExist('Database %s does not exist' % database)
        except OperationalError as e:
            self.main.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Database error %s' % e)
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.error('Cannot get database, got error %s' % e)
            self.log.exception(e)
            raise RuntimeError('Database error %s' % e)

    def list_sql_databases(self):
        """List all user's databases
        returns list of database objects
        raises RuntimeError on error"""
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        query = self.main.session.query(self.main.Databases)
        if self.main.customer_id:
            query = query.filter(self.main.Databases.t_customers_id==self.main.customer_id)
        else:
            self.main.require_admin()
        try:
            query = query.filter(self.main.Databases.database_type==self.type)
            retval = query.all()
            self.main.session.commit()
            return retval
        except OperationalError as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Database error %s' % e)
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.error('Cannot get databases, got error %s' % e)
            self.log.exception(e)
            raise RuntimeError('Database error %s' % e)

    def add_sql_database(self,server,database,username=None):
        """Add <database> to server <server> for user"""
        if username == None:
            username = database
        if self.main.customer_id is None:
            raise RuntimeError('Cannot add database without customer_id')
        database = database.lower()
        # check database name validity
        for char in str(database):
            if char not in 'abcdefghijklmnopqrstuvwxyz0123456789_':
                raise RuntimeError('Database name %s contains unvalid chars, allowed chars 0-9,a-z and _' % database)
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        try:
            serv = self.get_sql_server(server)
        except DoesNotExist:
            raise RuntimeError('Cannot find database server %s for %s database' % (server, self.type))
        # require alias
        self.require_database_alias(database)
        self.require_database_alias(username)
        
        try:
            self.get_sql_database(server,database)
            raise AlreadyExist('Database %s already exist' % database)
        except DoesNotExist:
            pass

        db = self.main.Databases()
        db.username = username
        db.database_name = database
        db.server = server
        db.database_type = self.type
        db.approved = True
        db.t_customers_id = self.main.customer_id
        
        try:
            self.main.session.add(db)
            self.main.session.commit()
        except Exception as e:
            self.log.exception(e)
            self.main.session.rollback()
            raise RuntimeError('Cannot add domain')
        except:
            self.main.session.rollback()
            raise RuntimeError('Cannot add domain')

    def del_sql_database(self,server,database):
        """Delete <dbype> <database> on <server>
        Used as lazy operation, server removes"""
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        if self.main.customer_id is None:
            raise RuntimeError('Select user first')
        serv = self.get_sql_server(server)
        db = self.get_mysql_database(server,database)
        self.main.session.delete(db)
        try:
            self.main.session.commit()
        except Exception as e:
            self.log.exception(e)
            self.log.error('Cannot delete mysql database %s on %s' % (database, server))
            raise RuntimeError('Cannot delete mysql database %s on %s' % (database, server))
        except:
            self.log.error('Cannot delete mysql database %s on %s' % (database, server))
            raise RuntimeError('Cannot delete mysql database %s on %s' % (database, server))

    def get_sql_server(self,server):
        """Get list of mysql servers"""
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        try:
            retval = self.main.session.query(self.main.Database_servers).filter(self.main.Database_servers.server==server)
            retval = retval.filter(self.main.Databases.database_type == self.type).one()
            self.main.session.commit()
            return retval
        except NoResultFound:
            self.main.session.rollback()
            raise DoesNotFound('Database server %s does not exist' % server)
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.exception(e)
            self.log.error('Cannot get database server %s' % server)
            raise RuntimeError('Cannot get database server %s' % server)
        except OperationalError as e:
            self.main.session.rollback()
            self.reconnect()
            self.log.exception(e)
            self.log.error('Cannot get database server %s' % server)
            raise RuntimeError('Cannot get database server %s' % server)

    def list_sql_servers(self):
        """Get list of database servers"""
        if not self.valid_dbtype():
            raise RuntimeError('Invalid database type %s' % self.type)
        try:
            retval = self.main.session.query(self.main.Database_servers).filter(self.main.Database_servers.database_type==self.type).all()
            self.main.session.commit()
            return retval
        except IntegrityError as e:
            self.main.session.rollback()
            self.log.exception(e)
            self.log.error('Cannot get database server list')
            raise RuntimeError('Cannot get database server list')
        except OperationalError as e:
            self.main.session.rollback()
            self.reconnect()
            self.log.exception(e)
            self.log.error('Cannot get mysql database list')
            raise RuntimeError('Cannot get database server list')


### MySQL ###

class MySQL(Database):
    def __init__(self,main):
        super(Database,self).__init__()
        self.type = 'MYSQL'
        self.log = logging.getLogger('services.databases')
        self.main = main

    def list(self):
        """List all user's databases
        returns list of database objects
        raises RuntimeError on error"""
        return self.list_sql_databases()

    def get(self,server,database):
        """Get user's mysql <database> on <server>
        return database object on success
        raise DoesNotExist if does not exist
        raise RuntimeError on database error"""
        return self.get_sql_database(server,database)

    def add(self,server,database,username=None):
        """Add mysql <database> to server <server> for user"""
        return self.add_sql_database(server,database,username)

    def delete(self,server,database):
        """Delete mysql <database> on <server>
        Used as lazy operation, server removes"""
        return self.del_sql_database(server,database)


    def list_servers(self):
        """Get list of mysql servers"""
        return self.list_sql_servers()

    def get_server(self,server):
        """Get list of mysql servers"""
        return self.get_sql_server(server)


### PostgreSQL ###

class PostgreSQL(Database):
    def __init__(self,main):
        super(Database,self).__init__(main)
        self.main = main
        self.type = 'POSTGRESQL'
        self.log = logging.getLogger('services.databases')

    def list(self):
        """List all user's databases
        returns list of database objects
        raises RuntimeError on error"""
        return self.list_sql_databases()

    def get(self,server,database):
        """Get user's postgres <database> on <server>
        return database object on success
        raise DoesNotExist if does not exist
        raise RuntimeError on database error"""
        return self.get_sql_database(server,database)

    def add(self,server,database,username=''):
        """Add mysql <database> to server <server> for user"""
        # check database name validity
        return self.add_sql_database(server,database,username)

    def delete(self,server,database):
        """Delete mysql <database> on <server>
        Used as lazy operation, server removes"""
        return self.del_sql_database(server,database)

    def list_servers(self):
        """Get list of mysql servers"""
        return self.list_sql_servers()

    def get_server(self,server):
        """Get list of mysql servers"""
        return self.get_sql_server(server)
