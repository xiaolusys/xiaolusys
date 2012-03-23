import json
from django.http import HttpResponse
from shopback.categorys.models import Category
from shopback.categorys.tasks import RecurUpdateCategoreyTask

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

