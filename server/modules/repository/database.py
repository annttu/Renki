# encoding: utf-8


from lib.database.table import RenkiTable, RenkiBase
from lib.exceptions import Invalid
from lib.database.tables import register_table
from sqlalchemy import Column, String


class Repository(RenkiBase, RenkiTable):
    __tablename__ = 'repository'
    name = Column(String(512))

    def validate(self):
        if len(self.name) > 50:
            raise Invalid('Repository name too long')
        return True

    def save(self):
        super(Repository, self).save()
        self._conn._session.add(self)
        self._conn._session.commit()


# Register table
register_table(Repository)
