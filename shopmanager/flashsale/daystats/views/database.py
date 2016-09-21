# encoding=utf8
from django.shortcuts import render
from flashsale.daystats.mylib.db import get_cursor, execute_sql


def index(req):
    cursor = get_cursor()
    sql = 'show tables from xiaoludb'
    items = execute_sql(cursor, sql)

    return render(req, 'yunying/database/index.html', locals())


def table(req, name):
    sql = 'desc xiaoludb.%s' % name
    items = execute_sql(get_cursor(), sql)

    return render(req, 'yunying/database/table.html', locals())
