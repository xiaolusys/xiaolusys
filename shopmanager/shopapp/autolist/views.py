import json
import settings
import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from djangorestframework.utils import as_tuple
from djangorestframework import status,signals
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView
from django.contrib.auth.decorators import login_required
from shopback.base.views import ListModelView
from shopapp.syncnum.models import UNEXECUTE
from auth import apis
from shopback.items.models import Item,ONSALE_STATUS,INSTOCK_STATUS
from shopapp.autolist.models import Logs,ItemListTask
from shopback.categorys.models import Category



@login_required(login_url=settings.LOGIN_URL)
def pull_from_taobao(request):

    profile = request.user.get_profile()
    session = request.session

    onsaleItems = apis.taobao_items_onsale_get(session=profile.top_session,page_no=1,page_size=200)
    if onsaleItems['items_onsale_get_response']['total_results'] <= 0:
        return  HttpResponseRedirect('itemlist/')

    items = onsaleItems.get('items_onsale_get_response',[]) and onsaleItems['items_onsale_get_response']['items'].get('item',[])

    session['update_items_datetime'] = datetime.datetime.now()

    user_id = profile.visitor_id

    currItems = Item.objects.filter(user_id=user_id)

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
            o = Item()
            o.num_iid = num_iid

        o.approve_status = INSTOCK_STATUS
        o.user_id = user_id
        o.detail_url = detail_item['detail_url']

        o.title = item['title']
        o.category_id   = item['cid']
        o.category_name = cats_detail[0]['name']

        o.outer_id  = item['outer_id']

        o.list_time = item['list_time']
        o.modified  = item['modified']
        o.pic_url   = item['pic_url']
        o.num       = item['num']
        o.save()

    for item in currItems:
        sale_status = itemstat[item.num_iid]['onsale']
        item.approve_status = ONSALE_STATUS if sale_status == 1 else INSTOCK_STATUS
        item.save()

    return HttpResponseRedirect('itemlist/')




def list_all_items(request):
    user_id = request.session['top_parameters']['taobao_user_id']
    items = Item.objects.filter(user_id=user_id).order_by('cid', 'outer_id')

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

    user_id = request.session['top_parameters']['taobao_user_id']
    try:
        cid =  Category.objects.get(name=catname)
    except Category.DoesNotExist:
        cid = None

    items = Item.objects.filter(user_id=user_id, cid=cid, approve_status=ONSALE_STATUS)
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

    return  render_to_response("catstable.html", {'timeslots': timekeys, 'data':data, 'catname':catname},
                               RequestContext(request))




def show_time_table_summary(request):
    from auth.utils import get_closest_time_slot, get_all_time_slots

    user_id = request.session['top_parameters']['taobao_user_id']
    weekday = request.GET.get('weekday', None)
    items   = Item.objects.filter(user_id=user_id,approve_status=ONSALE_STATUS).order_by('cid', 'outer_id')
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
        return  render_to_response("weektable.html",
                {'page':'weektable', 'cats':cats, 'timeslots': timekeys, 'weekday': int(weekday),
                'total': weekstat[int(weekday)-1]}, RequestContext(request))

    return render_to_response("tablesummary.html", {'page':'timetable', 'cats':cats, 'weekstat':weekstat},
                              RequestContext(request))




def show_time_table(request):
    items = Item.objects.all().order_by('cid', 'outer_id')

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
    return render_to_response("base.html", {'page': 'timetable', 'data':data, 'cats':cat, 'slots':slots},
                              RequestContext(request))




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

    n = Item.objects.filter(num_iid=num_iid).update(list_time=target_time)

    return HttpResponse(json.dumps({'date':target_time.strftime("%Y-%m-%d"),
                                    'timeslot':target_time.strftime("%H:%M-%S")}),mimetype='application/json')


################################ List View ##############################

class ListItemTaskView(ListModelView):
    queryset = None

    def get(self, request, *args, **kwargs):
        model = self.resource.model
        visitor_id = request.session['top_parameters']['visitor_id']

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        kwargs.update({'user_id':visitor_id})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        return queryset.filter(**kwargs)

    def get_queryset(self):
        return self.queryset



class CreateListItemTaskModelView(CreateModelMixin,ModelView):
    """A view which provides default operations for create, against a model in the database."""

    def post(self, request, *args, **kwargs):
        model = self.resource.model

        content = dict(self.CONTENT)

        all_kw_args = dict(content.items() + kwargs.items())

        update_nums = model.objects.filter(num_iid=all_kw_args['num_iid']).update(**all_kw_args)

        if update_nums == 0:

            if args:
                instance = model(pk=args[-1], **all_kw_args)
            else:
                instance = model(**all_kw_args)
            instance.save()

            signals.obj_created.send(sender=model, obj=instance, request=self.request)

        else:
            instance = model.objects.get(num_iid=all_kw_args['num_iid'],status=UNEXECUTE)

        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.resource(self).url(instance)
        return Response(status.HTTP_201_CREATED, instance, headers)



@login_required
def direct_update_listing(request,num_iid,num):

    if not (num_iid.isdigit() and num.isdigit()):
        response = {'errormsg':'The num_iid and num must be number!'}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    response = apis.taobao_item_update_listing(num_iid,num,request.session.get('top_session'))

    return HttpResponse(json.dumps(response),mimetype='application/json')



@login_required
def direct_del_listing(request,num_iid):

    if not num_iid.isdigit():
        response = {'errormsg':'The num_iid  must be number!'}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    response = apis.taobao_item_update_delisting(num_iid,request.session.get('top_session'))

    return HttpResponse(json.dumps(response),mimetype='application/json')


