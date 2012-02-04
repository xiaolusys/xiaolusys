import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from auth import apis
from autolist.models import ProductItem
import datetime


def pull_from_taobao(request):
    session = request.session

    onsaleItems = apis.taobao_items_onsale_get(session=session['top_session'],page_no=1,page_size=200)

    items = onsaleItems.get('items_onsale_get_response',[]) and onsaleItems['items_onsale_get_response']['items'].get('item',[])

    session['update_items_datetime'] = datetime.datetime.now()

    for item in items:
        detail = apis.taobao_item_get(session=session['top_session'],num_iid=item['num_iid'])
        detail_item = detail['item_get_response']['item']

        cats = apis.taobao_itemcats_get(session=session['top_session'],cids=item['cid'])
        cats_detail = cats['itemcats_get_response']['item_cats']['item_cat']

        o = None
        try:
            o = ProductItem.objects.get(num_iid=item['num_iid'])
        except ProductItem.DoesNotExist:
            o = ProductItem()
            o.num_iid = item['num_iid']

        o.detail_url = detail_item['detail_url']

        o.title = item['title']
        o.category_id = item['cid']
        o.category_name = cats_detail[0]['name']

        o.ref_code = item['outer_id']

        o.list_time = item['list_time']
        o.modified = item['modified']
        o.pic_url = item['pic_url']

        o.save()

    response = {'pulled':len(items)}

    return HttpResponse(json.dumps(response),mimetype='application/json')



def list_all_items(request):
    items = ProductItem.objects.all().order_by('category_id', 'ref_code')

    from auth.utils import get_closest_time_slot

    for x in items:
        relist_time = get_closest_time_slot(x.list_time)
        if relist_time != x.list_time:
            x.relist_time = "%s" % relist_time
        else:
            x.relist_time = ""
        x.isoweekday = x.list_time.isoweekday()
        x.list_time = "%s" % x.list_time


    return render_to_response("prod-list.html", {'page':'itemlist', 'items':items}, RequestContext(request))


def show_time_table(request):
    items = ProductItem.objects.all().order_by('category_id', 'ref_code')

    from auth.utils import get_closest_time_slot

    for x in items:
        relist_time = get_closest_time_slot(x.list_time)
        x.relist_time = "%s" % relist_time
        x.isoweekday = relist_time.isoweekday()

        x.list_time = "%s" % x.list_time


    #return render_to_response("prod-list.html", {'page': 'timetable', 'items':items}, RequestContext(request))

