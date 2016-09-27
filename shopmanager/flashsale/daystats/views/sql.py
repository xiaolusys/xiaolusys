# encoding=utf8
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from flashsale.daystats.mylib.db import mongo
from bson.objectid import ObjectId


@login_required
def index(req):
    items = mongo.query.find()
    items = list(items)
    for item in items:
        item['id'] = item['_id']
    return render(req, 'yunying/sql/index.html', {'items': items})


@login_required
def create(req):
    sql = req.POST.get('sql', '')
    name = req.POST.get('name', '')
    date_field = req.POST.get('date_field', '')
    key_desc = req.POST.get('key_desc', '')
    mongo.query.save({
        'sql': sql,
        'name': name,
        'date_field': date_field,
        'key_desc': key_desc
    })
    return HttpResponse('ok')


@login_required
def destroy(req, id):
    mongo.query.remove({'_id': ObjectId(id)})
    return redirect('yy-sql-index')
