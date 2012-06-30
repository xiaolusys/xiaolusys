import json
from django.http import HttpResponse
from djangorestframework.serializer import Serializer
from shopback.categorys.models import Category
from shopback.categorys.tasks import RecurUpdateCategoreyTask
import logging

logger = logging.getLogger('category.update')

def crawFullCategories(request,cid):

    top_session = request.session['top_session']

    puctask = RecurUpdateCategoreyTask.delay(top_session,cid)

    return HttpResponse(json.dumps({'code':0,"response_content":[{"task_id":puctask.task_id}]}))



def getCategoryIds(request):

    cat_names_str = request.GET.get('cat_names')
    cat_names_list = cat_names_str.split(',')

    cat_list = []
    parent_cid = None

    for cat_name in cat_names_list:
        cat_name = cat_name.strip()
        try:
            if parent_cid:
                category = Category.objects.get(name=cat_name,parent_cid=parent_cid)
            else:
                category = Category.objects.get(name=cat_name)

            parent_cid = category.cid
            cat_list.append([category.cid,category.name])
        except Category.DoesNotExist:
            break

    return HttpResponse(json.dumps({'code':0,"response_content":cat_list}))



def getCategoryTree(request):

    cat_id = request.GET.get('cat_id')
    cats   = Category.objects.filter(parent_cid=cat_id).order_by('sort_order')

    cats_json = Serializer().serialize(cats)

    return HttpResponse(json.dumps(cats_json),mimetype='application/json')
