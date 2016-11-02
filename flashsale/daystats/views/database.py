# encoding=utf8
from django.shortcuts import render
from flashsale.daystats.mylib.db import get_cursor, execute_sql
from django.contrib.auth.decorators import login_required


@login_required
def index(req):
    cursor = get_cursor()
    sql = 'show tables from xiaoludb'
    items = execute_sql(cursor, sql)

    return render(req, 'yunying/database/index.html', locals())


@login_required
def table(req, name):
    sql = 'desc xiaoludb.%s' % name
    items = execute_sql(get_cursor(), sql)

    return render(req, 'yunying/database/table.html', locals())
