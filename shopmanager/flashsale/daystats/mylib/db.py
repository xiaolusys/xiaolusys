# encoding=utf8
import os
from django.conf import settings
from django.db import connections
from pymongo import MongoClient


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def execute_sql(cursor, sql, params=None):
    with cursor as c:
        if params:
            c.execute(sql, params)
        else:
            c.execute(sql)
        # print c._last_executed
        res = dictfetchall(cursor)
        return res


def get_cursor():
    cursor = connections['product'].cursor()
    return cursor


if os.environ.get('INSTANCE') == 'admin':
    mongo = MongoClient(settings.MONGODB_URI).xlmm
else:
    # mongo = MongoClient('0.0.0.0:32769').xlmm
    mongo = None
