import json
import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from auth import apis
from autolist.models import ProductItem, Logs
import datetime

from shopback.task.models import ItemListTask

@login_required(login_url=settings.LOGIN_URL)
def pull_from_taobao(request):

    profile = request.user.get_profile()
    session = request.session

    onsaleItems = apis.taobao_items_onsale_get(session=profile.top_session,page_no=1,page_size=200)

    items = onsaleItems.get('items_onsale_get_response',[]) and onsaleItems['items_onsale_get_response']['items'].get('item',[])

    session['update_items_datetime'] = datetime.datetime.now()

    owner_id = profile.visitor_id

    currItems = ProductItem.objects.filter(owner_id=owner_id)

    itemstat = {}
    for item in currItems:
        itemstat[item.num_iid] = {'onsale':0, 'item':item}

    for item in items:
        detail = apis.taobao_item_get(session=session['top_session'],num_iid=item['num_iid'])
        detail_item = detail['item_get_response']['item']

        cats = apis.taobao_itemcats_get(session=session['top_session'],cids=item['cid'])
        cats_detail = cats['itemcats_get_response']['item_cats']['item_cat']

        o = None
        num_iid = str(item['num_iid'])
        if num_iid in itemstat:
            o = itemstat[num_iid]['item']
            itemstat[o.num_iid]['onsale'] = 1
        else:
            o = ProductItem()
            o.num_iid = num_iid

        o.onsale = 1
        o.owner_id = owner_id
        o.detail_url = detail_item['detail_url']

        o.title = item['title']
        o.category_id = item['cid']
        o.category_name = cats_detail[0]['name']

        o.ref_code = item['outer_id']

        o.list_time = item['list_time']
        o.modified = item['modified']
        o.pic_url = item['pic_url']
        o.num = item['num']
        o.save()

    for item in currItems:
        if itemstat[item.num_iid]['onsale'] == 0:
            item.onsale = 0
            item.save()

    return HttpResponseRedirect('itemlist/')

def list_all_items(request):
    owner_id = request.session['top_parameters']['taobao_user_id']
    items = ProductItem.objects.filter(owner_id=owner_id).order_by('category_id', 'ref_code')

    from auth.utils import get_closest_time_slot

    for x in items:
        relist_time, status = get_closest_time_slot(x.list_time)
        if status:
            x.relist_day,x.relist_hm = relist_time.strftime("%Y-%m-%d"), relist_time.strftime("%H:%M:%S")
        else:
            x.relist_day,x.relist_hm = "",""
        x.isoweekday = x.list_time.isoweekday()
        x.list_day,x.list_hm = x.list_time.strftime("%Y-%m-%d"), x.list_time.strftime("%H:%M:%S")

        try:
            y = ItemListTask.objects.get(num_iid=x.num_iid)
            x.scheduled_day = y.list_weekday
            x.scheduled_hm = y.list_time
            x.status = y.status
        except ItemListTask.DoesNotExist:
            x.scheduled_day = None
            x.scheduled_hm = None
            x.status = 'unscheduled'


    return render_to_response("itemtable.html", {'page':'itemlist', 'items':items}, RequestContext(request))



def show_timetable_cats(request):
    from auth.utils import get_closest_time_slot, get_all_time_slots
    catname = request.GET.get('catname', None)

    owner_id = request.session['top_parameters']['taobao_user_id']
    items = ProductItem.objects.filter(owner_id=owner_id, category_name=catname, onsale=1)
    data = [[],[],[],[],[],[],[]]
    for item in items:
        relist_slot, status = get_closest_time_slot(item.list_time)
        item.slot = relist_slot.strftime("%H:%M")
        idx = relist_slot.isoweekday() - 1
        try:
            o = ItemListTask.objects.get(num_iid=item.num_iid)
            item.slot = o.list_time
            idx = o.list_weekday - 1
        except ItemListTask.DoesNotExist:
            pass

        data[idx].append(item)

    slots = get_all_time_slots()
    timekeys = slots.keys()
    timekeys.sort()

    return  render_to_response("catstable.html", {'timeslots': timekeys, 'data':data, 'catname':catname}, RequestContext(request))



def show_time_table_summary(request):
    from auth.utils import get_closest_time_slot, get_all_time_slots

    owner_id = request.session['top_parameters']['taobao_user_id']
    weekday = request.GET.get('weekday', None)
    items = ProductItem.objects.filter(owner_id=owner_id, onsale=1).order_by('category_id', 'ref_code')
    weekstat = [0,0,0,0,0,0,0]
    data = {}
    for item in items:
        relist_time, status = get_closest_time_slot(item.list_time)

        item.slot = relist_time.strftime("%H:%M")
        idx = item.list_time.isoweekday() - 1

        try:
            o = ItemListTask.objects.get(num_iid=item.num_iid)
            item.slot = o.list_time
            idx = o.list_weekday - 1
        except ItemListTask.DoesNotExist:
            pass

        cat = item.category_name
        if not cat in data:
            data[cat] = [[],[],[],[],[],[],[]]

        weekstat[idx] += 1
        data[cat][idx].append(item)

    cats = []
    for k,v in data.iteritems():
        t = 0
        for x in v:
            t += len(x)
        cats.append({'cat':k, 'total':t})
    cats.sort(lambda a,b: cmp(b['total'], a['total']))

    for c in cats:
        key = c['cat']
        if weekday:
            c['items'] = data[key][int(weekday)-1]
        else:
            c['items'] = data[key]


    slots = get_all_time_slots()
    timekeys = slots.keys()
    timekeys.sort()

    if weekday:
        return  render_to_response("weektable.html", {'page':'weektable', 'cats':cats, 'timeslots': timekeys, 'weekday': int(weekday), 'total': weekstat[int(weekday)-1]}, RequestContext(request))

    return render_to_response("tablesummary.html", {'page':'timetable', 'cats':cats, 'weekstat':weekstat}, RequestContext(request))

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
            cat.append(k)
    return render_to_response("base.html", {'page': 'timetable', 'data':data, 'cats':cat, 'slots':slots}, RequestContext(request))

def show_logs(request):
    logs = Logs.objects.all().order_by('execute_time')
    return render_to_response("logs.html", {'logs':logs}, RequestContext(request))


def change_list_time(request):
    num_iid = request.GET.get('num_iid')
    weekday = int(request.GET.get('weekday'))
    timeslot = request.GET.get('timeslot')

    try:
        o = ItemListTask.objects.get(num_iid=num_iid)
    except ItemListTask.DoesNotExist:
        o = ItemListTask()

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

    return HttpResponse(json.dumps({'date':target_time.strftime("%Y-%m-%d"), 'timeslot':target_time.strftime("%H:%M-%S")}),mimetype='application/json')


