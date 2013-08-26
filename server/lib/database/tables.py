# encoding: utf-8


TABLES = []


def register_table(table):
    """
    Register database table to connection.
    All registered tables are mapped on database connection initialization.
    """
    global TABLES
    if table not in TABLES:
        TABLES.append(table)
