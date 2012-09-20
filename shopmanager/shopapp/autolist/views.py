import json
import settings
import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from djangorestframework.utils import as_tuple
from djangorestframework import status,signals
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView
from django.contrib.auth.decorators import login_required
from shopback.base.views import ListModelView
from shopback.base.models import UNEXECUTE
from shopback.categorys.models import Category
from shopback.items.models import Item,Product,ONSALE_STATUS,INSTOCK_STATUS
from shopapp.autolist.models import Logs,ItemListTask,TimeSlots
from auth import apis




@login_required(login_url=settings.LOGIN_URL)
def pull_from_taobao(request):

    profile = request.user.get_profile()
    session = request.session

    onsaleItems = apis.taobao_items_onsale_get(page_no=1,page_size=200,tb_user_id=profile.visitor_id)
    if onsaleItems['items_onsale_get_response']['total_results'] <= 0:
        return  HttpResponseRedirect('itemlist/')

    items = onsaleItems.get('items_onsale_get_response',[]) and onsaleItems['items_onsale_get_response']['items'].get('item',[])

    session['update_items_datetime'] = datetime.datetime.now()

    currItems = profile.items.all()

    itemstat = {}
    for item in currItems:
        itemstat[item.num_iid] = {'onsale':0, 'item':item}

    fields = ['outer_id','num','seller_cids','type','valid_thru','price','postage_id','has_showcase','has_discount','props','title','pic_url']
    for item in items:
        o = None
        num_iid = str(item['num_iid'])
        if num_iid in itemstat:
            o = itemstat[num_iid]['item']
            itemstat[num_iid]['onsale'] = 1
        else:
            o = Item()
            o.num_iid = num_iid

        for field in fields:
            setattr(o,field,item[field])

        o.approve_status = ONSALE_STATUS
        o.modified = datetime.datetime.strptime(item['modified'],'%Y-%m-%d %H:%M:%S')
        o.list_time = datetime.datetime.strptime(item['list_time'],'%Y-%m-%d %H:%M:%S')
        o.delist_time = datetime.datetime.strptime(item['delist_time'],'%Y-%m-%d %H:%M:%S')

        o.user = profile
        o.category = Category.objects.get(cid=item['cid'])
        product,state = Product.objects.get_or_create(outer_id=item['outer_id'])
        if state:
            product.name=item['title']
            product.category=o.category
            product.price=str(item['price'])
            product.collect_num = item['num']
            product.save()
        o.product = product
        o.save()

    for item in currItems:
        sale_status = itemstat[item.num_iid]['onsale']
        if sale_status == 0:
            item.approve_status = INSTOCK_STATUS
            item.save()

    return HttpResponseRedirect(reverse('list_all_items'))




def list_all_items(request):
    user = request.user.get_profile()
    items = user.items.filter(approve_status=ONSALE_STATUS).order_by('list_time')

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
            
    return render_to_response("autolist/itemtable.html", {'page':'itemlist', 'items':items}, RequestContext(request))


def show_timetable_cats(request):
    from auth.utils import get_closest_time_slot, get_all_time_slots
    catname = request.GET.get('catname', None)

    user_id = request.session['top_parameters']['taobao_user_id']
    try:
        category =  Category.objects.get(name=catname)
    except Category.DoesNotExist:
        category = None

    items = Item.objects.filter(user=user_id, category=category, approve_status=ONSALE_STATUS)
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

    return  render_to_response("autolist/catstable.html", {'timeslots': timekeys, 'data':data, 'catname':catname},
                               RequestContext(request))


def show_weektable(request, weekday):
    user_profile = request.user.get_profile()
    items = Item.objects.filter(user=user_profile,approve_status=ONSALE_STATUS).order_by('category', 'outer_id')
    timeslots = [int(o.timeslot) for o in TimeSlots.objects.all()]
    cats = {}
    total = 0
    
    if timeslots:
        for item in items:
            try:
                o = ItemListTask.objects.get(num_iid=item.num_iid)
            except:
                list_day = item.list_time.isoweekday()
                list_hour = item.list_time.hour
                list_minute = item.list_time.minute
            else:   
                list_day = o.list_weekday
                list_hour = o.hour
                list_minute = o.minute
                
            if list_day == int(weekday):
                timeslot = list_hour * 100 + list_minute
                
                idx = 0
                for i in range(0,len(timeslots)):
                    if timeslot <= timeslots[i]:
                        idx = i
                        break
                mapslot = timeslots[idx]
                cat = item.category
                if not cat in cats:
                    cats[cat] = {}
                    for slot in timeslots:
                        cats[cat][slot] = []
    
                cats[cat][mapslot].append(item)
                total += 1

    for cat,slotitems in cats.items():
        temp_items = slotitems.items()
        temp_items.sort(lambda a,b: cmp(a[0], b[0]))
        cats[cat]= [ i[1] for i in temp_items]
          
    return render_to_response("autolist/weektable.html",
        {'cats':cats, 'timeslots': timeslots, 'weekday': weekday, 'total': total},
        RequestContext(request))


def show_time_table_summary(request):
    user_profile = request.user.get_profile()
    items = Item.objects.filter(user=user_profile,approve_status=ONSALE_STATUS).order_by('category', 'outer_id')

    weekstat = [0,0,0,0,0,0,0]
    data = {}

    for item in items:
        try:
            o = ItemListTask.objects.get(num_iid=item.num_iid)
        except:
            idx = item.list_time.isoweekday() - 1
        else:   
            idx = o.list_weekday - 1

        cat = item.category
        if not cat in data:
            data[cat] = [[],[],[],[],[],[],[]]

        weekstat[idx] += 1
        data[cat][idx].append(item)

    cats = []
    for k,v in data.iteritems():
        t = 0
        for x in v:
            t += len(x)
        cats.append({'cat':k,  'items':v, 'total':t})
    cats.sort(lambda a,b: cmp(b['total'], a['total']))

    return render_to_response("autolist/tablesummary.html", {'cats':cats, 'weekstat':weekstat}, RequestContext(request))




def show_time_table(request):
    items = Item.objects.all().order_by('category', 'outer_id')

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


def get_timeslots_json(request):

    time_slots = TimeSlots.objects.all()
    slot_list = [ '%d:%d'%(s.hour,s.minute) for s in time_slots]
    return HttpResponse(json.dumps(slot_list),mimetype='application/json')

def show_logs(request):
    logs = Logs.objects.all().order_by('execute_time')
    return render_to_response("autolist/logs.html", {'logs':logs}, RequestContext(request))




def change_list_time(request):
    num_iid = request.POST.get('num_iid')
    weekday = int(request.POST.get('list_weekday'))
    delist_time = request.POST.get('list_time')
    

    item = Item.objects.get(num_iid=num_iid)

    try:
        o = ItemListTask.objects.get(num_iid=num_iid)
    except ItemListTask.DoesNotExist:
        o = ItemListTask()

    tokens = delist_time.split(':')
    hour = int(tokens[0])
    minute = int(tokens[1])

    now = datetime.datetime.now()

    target_time = datetime.datetime(now.year, now.month, now.day, hour, minute) - \
                  datetime.timedelta(days=(now.isoweekday()-weekday))

    if target_time < now:
        target_time = target_time + datetime.timedelta(days=7)
    
    o.num_iid = num_iid
    o.user_id = item.user.visitor_id
    o.nick    = item.user.nick
    o.title   = item.title
    o.num     = item.num
    o.list_weekday = target_time.isoweekday()
    o.list_time = delist_time
    o.save()

    return HttpResponse(json.dumps({'list_weekday':target_time.strftime("%Y-%m-%d"),
                                    'list_time':target_time.strftime("%H:%M")}),mimetype='application/json')


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
    
    response = apis.taobao_item_update_listing(num_iid=num_iid,num=num,tb_user_id=user_id)

    return HttpResponse(json.dumps(response),mimetype='application/json')



@login_required
def direct_del_listing(request,num_iid):

    if not num_iid.isdigit():
        response = {'errormsg':'The num_iid  must be number!'}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    response = apis.taobao_item_update_delisting(num_iid=num_iid,tb_user_id=user_id)

    return HttpResponse(json.dumps(response),mimetype='application/json')


