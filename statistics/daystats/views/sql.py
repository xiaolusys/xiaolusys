# encoding=utf8
from __future__ import absolute_import, unicode_literals
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from bson.objectid import ObjectId

from statistics.daystats.models import DailySqlRecord
from statistics.daystats.mylib.db import (
    get_cursor,
    execute_sql,
)


@login_required
def index(req):
    query_list = DailySqlRecord.normal_records().values('id', 'query_data')
    items = []
    for query in query_list:
        query['query_data'].update({'id': query['id']})
        items.append(query['query_data'])
    return render(req, 'yunying/sql/index.html', {'items': items})


@login_required
def create(req):
    sql = req.POST.get('sql', '')
    name = req.POST.get('name', '')
    date_field = req.POST.get('date_field', '')
    key_desc = req.POST.get('key_desc', '')
    display = req.POST.get('display') or ''

    data = {
        'sql': sql,
        'name': name,
        'date_field': date_field,
        'key_desc': key_desc,
        'display': display
    }

    sql_record, state = DailySqlRecord.objects.get_or_create(
        uni_key=DailySqlRecord.gen_unikey(sql)
    )
    sql_record.status = True
    sql_record.query_data = data
    sql_record.save()

    return HttpResponse('ok')


@login_required
def destroy(req, id):
    sql_record = get_object_or_404(DailySqlRecord, pk=id)
    sql_record.set_invalid()
    sql_record.save()
    return redirect('yy-sql-index')


@login_required
def query(req):
    sql = req.GET.get('sql') or ''
    query_name = req.GET.get('query_name') or ''
    if sql:
        result = execute_sql(get_cursor(), sql)

    return render(req, 'yunying/sql/query.html', locals())
