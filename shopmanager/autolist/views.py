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
        relist_time, status = get_closest_time_slot(x.list_time)
        if status:
            x.relist_day,x.relist_hm = relist_time.strftime("%Y-%m-%d"), relist_time.strftime("%H:%M:%S")
        else:
            x.relist_day,x.relist_hm = "",""
        x.isoweekday = x.list_time.isoweekday()
        x.list_day,x.list_hm = x.list_time.strftime("%Y-%m-%d"), x.list_time.strftime("%H:%M:%S")


    return render_to_response("base.html", {'page':'itemlist', 'items':items}, RequestContext(request))


def show_time_table(request):
    items = ProductItem.objects.all().order_by('category_id', 'ref_code')

    from auth.utils import get_closest_time_slot, get_all_time_slots

    slots = get_all_time_slots()
    timekeys = slots.keys()
    timekeys.sort()

    data = [[],[],[],[],[],[],[]]
    for x in data:
        for slot in timekeys:
            x.append({'slot':slot, 'items':[]})

    cats = {}
    for x in items:
        relist_time, status = get_closest_time_slot(x.list_time)
        x.relist_time = "%s" % relist_time
        x.isoweekday = relist_time.isoweekday()

        slot = "%02d:%02d" % (relist_time.hour, relist_time.minute)
        print 'slot', slot
        x.list_time = "%s" % x.list_time

        if slot in slots:
            idx = slots[slot]
            data[x.isoweekday-1][idx]['items'].append(x)
        else:
            print slot, x.category_name, x.list_time, x.title

        if not x.category_name in cats:
            cats[x.category_name] = 1
        else:
            cats[x.category_name] += 1

        cat = []
        for k in cats.keys():
            if cats[k] > 3:
                cat.append(k)
    return render_to_response("base.html", {'page': 'timetable', 'data':data, 'cats':cat, 'slots':slots}, RequestContext(request))


def change_list_time(request):
    num_iid = request.GET.get('num_iid')
    weekday = int(request.GET.get('weekday'))
    timeslot = request.GET.get('timeslot')

    from auth.utils import get_all_time_slots
    timekeys = get_all_time_slots().keys()
    timekeys.sort()

    tokens = timekeys[int(timeslot)-1].split(':')
    hour = int(tokens[0])
    minute = int(tokens[1])

    now = datetime.datetime.now()

    target_time = datetime.datetime(now.year, now.month, now.day, hour, minute) - \
                  datetime.timedelta(days=(now.isoweekday()-weekday))

    if target_time < now:
        target_time = target_time + datetime.timedelta(days=7)

    n = ProductItem.objects.filter(num_iid=num_iid).update(list_time=target_time)
    print n, 'records updated'

    return HttpResponse(json.dumps({'date':target_time.strftime("%Y-%m-%d"), 'timeslot':target_time.strftime("%H:%M-%S")}),mimetype='application/json')


