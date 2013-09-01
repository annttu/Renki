# encoding: utf-8


from lib.database.table import RenkiTable, RenkiBase
from lib.database.tables import register_table
from lib.exceptions import Invalid
from sqlalchemy import Column, String, Integer


class RepositoryDatabase(RenkiBase, RenkiTable):
    __tablename__ = 'repository'
    name = Column('name', String(512), nullable = False)
    userid = Column('userid', Integer, nullable=False)

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
