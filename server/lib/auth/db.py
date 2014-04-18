# encoding: utf-8


"""
Users database
"""

from lib.database.table import RenkiTable, RenkiBase
from lib.database.tables import register_table
from lib import renki_settings as settings
from lib.database.tables import metadata
from lib.validators import validate_user_id, validate_string, \
                           validate_positive_int
from lib.exceptions import DoesNotExist
from lib.utils import generate_key

from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import Table
from sqlalchemy import Column, Unicode, Integer, DateTime, ForeignKey, or_
from datetime import datetime, timedelta
from hashlib import sha512

import logging

logger = logging.getLogger("auth.db")


def expires_funct():
    return datetime.now() + timedelta(seconds=settings.KEY_EXPIRE_TIME)


def hash_key(key):
    if isinstance(key, str):
        key = key.encode("utf-8")
    return sha512(settings.AUTH_SECRET.encode("utf-8") + key).hexdigest()

def hash_password(password, salt=None):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if salt is None:
        salt = generate_key(size=20)
    return "$1$%s$%s" % (salt, sha512(salt.encode("utf-8") + password).hexdigest())

class Users(RenkiBase, RenkiTable):
    """
    Users database table
    """
    __tablename__ = 'users'
    # Member ID (mid)
    id = Column('id', Integer, nullable=False, primary_key=True)
    added = Column('added', DateTime, default=datetime.now)
    name = Column('name', Unicode, nullable=False, default="")
    firstnames = Column('firstnames', Unicode, nullable=False, default="")
    lastname = Column('lastname', Unicode, nullable=False, default="")
    password = Column('password', Unicode)

    @property
    def user_id(self):
        return self.id

    def set_password(self, password):
        self.password = hash_password(password)

    def check_password(self, password):
        try:
            crap, pwtype, salt, pwhash = self.password.split('$', 3)
        except Exception as e:
            logger.exception(e)
            return False
        return self.password == hash_password(password, salt=salt)

    def validate(self):
        validate_user_id(self.id)
        validate_string(self.name)
        validate_string(self.firstnames)
        validate_string(self.lastname)
        if self.password:
            validate_string(self.password)
        return True

    def has_permission(self, permission):
        for perm in self.permissions:
            if perm.name == permission:
                return True
        for group in self.permission_groups:
            for perm in group.permissions:
                if perm.name == permission:
                    return True
        return False

register_table(Users)


class AuthKeys(RenkiBase, RenkiTable):
    """
    Database table for keys
    """
    __tablename__ = 'auth_keys'
    key = Column("key", Unicode, nullable=False)
    expires = Column("expires", DateTime, nullable=False,
                     default=expires_funct)
    user_id = Column("user_id", Integer, ForeignKey('users.id'),
                     nullable=False)
    user = relationship("Users", backref='auth_keys')

    def validate(self):
        if self.user_id is not None:
            validate_user_id(self.user_id)
        else:
            validate_user_id(self.user.id)
        validate_string(self.key)
        return True


    @classmethod
    def add_key(cls, user, key, expires=None):
        a = AuthKeys()
        a.key = hash_key(key)
        a.user_id = user.id
        if expires:
            a.expires = expires
        a.save()
        return a

    @classmethod
    def delete_key(cls, key):
        try:
            item = cls.query().filter(AuthKeys.key==key).one()
        except SQLAlchemyError as e:
            logger.exception(e)
            raise DoesNotExist("Key does not exist")
        item.delete()

    @classmethod
    def get_key(cls, key):
        key = hash_key(key)
        try:
            item = cls.query().filter(AuthKeys.key == key, or_(
                                      AuthKeys.expires > datetime.now(),
                                      AuthKeys.expires == None)).one()
        except SQLAlchemyError as e:
            logger.exception(e)
            raise DoesNotExist("Key does not exist")
        return item

    def get_user(self):
        if self.user_id is None:
            return None
        try:
            user = Users.query().filter(Users.id == self.user_id).one()
        except SQLAlchemyError as e:
            logger.exception(e)
            raise DoesNotExist("Key does not exist")
        return user

register_table(AuthKeys)


permissions_to_groups = Table('permissions_to_groups', metadata,
    Column('permissions_id', Integer, ForeignKey('permissions.id')),
    Column('permission_groups_id', Integer, ForeignKey('permission_groups.id'))
)

permissions_to_users = Table('permissions_to_users', metadata,
    Column('permissions_id', Integer, ForeignKey('permissions.id')),
    Column('users_id', Integer, ForeignKey('users.id'))
    )

users_to_groups = Table('users_to_groups', metadata,
    Column('users_id', Integer, ForeignKey('users.id')),
    Column('permission_groups_id', Integer, ForeignKey('permission_groups.id'))
    )

class Permissions(RenkiBase, RenkiTable):
    """
    Database table for permissions
    """
    __tablename__ = 'permissions'
    name = Column('name', Unicode, nullable=False, unique=True)
    description = Column('description', Unicode, nullable=False, default="")
    permission_groups = relationship("PermissionGroups",
                                     secondary=permissions_to_groups,
                                     backref="permissions")
    users = relationship("Users",
                         secondary=permissions_to_users,
                         backref="permissions")

    def validate(self):
        validate_string(self.name, name="Name")
        if self.description:
            validate_string(self.description, name="description")

register_table(Permissions)


class PermissionGroups(RenkiBase, RenkiTable):
    """
    Database table for permission groups
    """
    __tablename__ = 'permission_groups'
    name = Column('name', Unicode, nullable=False, unique=True)
    description = Column('description', Unicode, nullable=False, default="")

    users = relationship("Users",
                         secondary=users_to_groups,
                         backref="permission_groups")

    def validate(self):
        validate_string(self.name)
        validate_string(self.description)

register_table(PermissionGroups)

class DefaultLimits(RenkiBase, RenkiTable):
    """
    Database table for limits
    """
    __tablename__ = 'default_limits'
    table = Column('table', Unicode, nullable=False)
    soft_limit = Column('soft_limit', Integer)
    hard_limit = Column('hard_limit', Integer)

    def validate(self):
        return True
register_table(DefaultLimits)

class Limits(RenkiBase, RenkiTable):
    """
    Database table for limits
    """
    __tablename__ = 'limits'
    user_id = Column('users_id', Integer, ForeignKey('users.id'))
    table = Column('table', Unicode, nullable=False)
    soft_limit = Column('soft_limit', Integer)
    hard_limit = Column('hard_limit', Integer)
    relationship(Users, backref="limits")

    def validate(self):
        return True
        
register_table(Limits)