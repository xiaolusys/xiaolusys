import json
from django.http import HttpResponse
# from djangorestframework.serializer import Serializer
from shopback.categorys.models import Category
from shopback.categorys.tasks import RecurUpdateCategoreyTask
import logging

# from serializer import  Serializer



logger = logging.getLogger('category.update')


def crawFullCategories(request, cid):
    profile = request.user.get_profile()

    puctask = RecurUpdateCategoreyTask.delay(profile.visitor_id, cid)

    return HttpResponse(json.dumps({'code': 0, "response_content": [{"task_id": puctask.task_id}]}))


def getCategoryIds(request):
    cat_names_str = request.GET.get('cat_names')
    cat_names_list = cat_names_str.split(',')

    cat_list = []
    parent_cid = None

    for cat_name in cat_names_list:
        cat_name = cat_name.strip()
        try:
            if parent_cid:
                category = Category.objects.get(name=cat_name, parent_cid=parent_cid)
            else:
                category = Category.objects.get(name=cat_name)

            parent_cid = category.cid
            cat_list.append([category.cid, category.name])
        except Category.DoesNotExist:
            break

    return HttpResponse(json.dumps({'code': 0, "response_content": cat_list}))


from    serializers import CategorySerializer
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders it's content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def getCategoryTree(request):
    cat_id = request.GET.get('cat_id')
    cats = Category.objects.filter(parent_cid=cat_id).order_by('sort_order')
    # cats=Category.objects.all().order_by('sort_order')
    # cats_json = Serializer().serialize(cats)
    # print cats[1].cid,cats[1].name,cats[1].__dict__
    serializer = CategorySerializer(cats, many=True)
    # print serializer
    cats_json = serializer.data
    # print  cats_json,55566666666666
    # return JSONResponse(serializer.data)
    return HttpResponse(json.dumps(cats_json), content_type='application/json')
    # return HttpResponse(json.dumps(cats_json),content_type='application/json')
