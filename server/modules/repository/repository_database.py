# encoding: utf-8


from lib.database.table import RenkiUserDataTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer, types


class RepositoryDatabase(RenkiBase, RenkiUserDataTable):
    __tablename__ = 'repository'

    name = Column('name', String(512), nullable=False)
    server_group_id = Column('server_group_id', Integer, ForeignKey('server_group.id'), nullable=False)
    user_id = Column('user_id', Integer, ForeignKey('server_group.id'), nullable=False)
    repo_type = Column('repo_type', types.Enum('git', 'svn', name='repository_types', native_enum=True), nullable=False)

    __table_args__ = (UniqueConstraint('server_group_id', 'name', 'repo_type'),)

    def validate(self):
        if len(self.name) > 50:
            raise Invalid('Repository name too long')
        return True

    def save(self):
        super(RepositoryDatabase, self).save()
        self._conn.add(self)
        self._conn.commit()

# Register table
register_table(RepositoryDatabase)
