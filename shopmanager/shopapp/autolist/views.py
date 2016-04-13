# -*- coding:utf8 -*-
import json
import datetime
from django.db.models import signals
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.conf import settings
# from djangorestframework.utils import as_tuple
# from djangorestframework import status
# from djangorestframework.response import Response
# from djangorestframework.mixins import CreateModelMixin
# from djangorestframework.views import ModelView
from django.contrib.auth.decorators import login_required
# from core.options.views import ListModelView
from shopback import paramconfig as pcfg
from shopback.categorys.models import Category
from shopback.items.models import Item, Product
from shopback.users.models import User
from shopapp.autolist.models import Logs, ItemListTask, TimeSlots, UNEXECUTE, UNSCHEDULED, DELETE, LISTING_TYPE, \
    DELISTING_TYPE
from auth import apis
from . import serializers
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.mixins import CreateModelMixin
from rest_framework import authentication
from rest_framework import status


@login_required
def invalid_list_task(request, num_iid):
    if not num_iid.isdigit():
        response = {'code': 1, 'response_error': u'商品编号不合规则'}
        return HttpResponse(json.dumps(response), content_type='application/json')

    ItemListTask.objects.get(num_iid=num_iid).update(status=DELETE)
    response = {'code': 0, 'response_content': 'success'}

    return HttpResponse(json.dumps(response), content_type='application/json')


@login_required(login_url=settings.LOGIN_URL)
def pull_from_taobao(request):
    content = request.REQUEST
    user_id = content.get('user_id', '')
    try:
        profile = User.objects.get(user=user_id)
    except Exception:
        profile = request.user.get_profile()

    onsaleItems = apis.taobao_items_onsale_get(page_no=1, page_size=200, tb_user_id=profile.visitor_id)
    if onsaleItems['items_onsale_get_response']['total_results'] <= 0:
        return HttpResponseRedirect('itemlist/?user_id=' + user_id)

    items = onsaleItems.get('items_onsale_get_response', []) and onsaleItems['items_onsale_get_response']['items'].get(
        'item', [])

    currItems = profile.items.all()

    itemstat = {}
    for item in currItems:
        itemstat[item.num_iid] = {'onsale': 0, 'item': item}

    for item in items:
        num_iid = str(item['num_iid'])
        if num_iid in itemstat:
            itemstat[num_iid]['onsale'] = 1
        item.pop('modified', None)
        Item.save_item_through_dict(profile.visitor_id, item)

    for item in currItems:
        sale_status = itemstat[item.num_iid]['onsale']
        if sale_status == 0:
            item.approve_status = pcfg.INSTOCK_STATUS
            item.save()

    return HttpResponseRedirect(reverse('list_all_items') + '?user_id=' + user_id)


def list_all_items(request):
    content = request.REQUEST
    user_id = content.get('user_id', '')
    # print user_id,"77666666666666666"
    try:
        # profile = User.objects.get(user=u"优尼小小世界")
        # profile = User.objects.all()[1]
        # print profile
        profile = User.objects.get(user=user_id)
    except Exception:
        profile = request.user.get_profile()

    items = profile.items.filter(approve_status=pcfg.ONSALE_STATUS).order_by('list_time')

    from common.utils import get_closest_time_slot

    for x in items:
        relist_time, status = get_closest_time_slot(x.list_time)
        if status:
            x.relist_day, x.relist_hm = relist_time.strftime("%Y-%m-%d"), relist_time.strftime("%H:%M:%S")
        else:
            x.relist_day, x.relist_hm = "", ""
        x.isoweekday = x.list_time.isoweekday()
        x.list_day, x.list_hm = x.list_time.strftime("%Y-%m-%d"), x.list_time.strftime("%H:%M:%S")

        try:
            y = ItemListTask.objects.get(num_iid=x.num_iid)
            x.scheduled_day = y.list_weekday
            x.scheduled_hm = y.list_time
            x.status = y.status
        except ItemListTask.DoesNotExist:
            x.scheduled_day = None
            x.scheduled_hm = None
            x.status = UNSCHEDULED

    return render_to_response("autolist/itemtable.html", {'page': 'itemlist', 'items': items, 'user_id': user_id},
                              RequestContext(request))


def show_timetable_cats(request):
    content = request.REQUEST
    user_id = content.get('user_id', '')
    print user_id, "8888888888888888888"
    try:
        profile = User.objects.get(user=user_id)
    except Exception:
        profile = request.user.get_profile()

    from common.utils import get_closest_time_slot, get_all_time_slots
    catname = request.GET.get('catname', None)

    try:
        category = Category.objects.get(name=catname)
    except Category.DoesNotExist:
        category = None

    items = Item.objects.filter(user=profile, category=category, approve_status=pcfg.ONSALE_STATUS)
    data = [[], [], [], [], [], [], []]
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

    return render_to_response("autolist/catstable.html",
                              {'timeslots': timekeys, 'data': data, 'catname': catname, 'user_id': user_id},
                              RequestContext(request))


def show_weektable(request, weekday):
    content = request.REQUEST
    user_id = content.get('user_id', '')
    try:
        profile = User.objects.get(user=user_id)
    except Exception:
        profile = request.user.get_profile()

    items = Item.objects.filter(user=profile, approve_status=pcfg.ONSALE_STATUS).order_by('category', 'outer_id')
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
                for i in range(0, len(timeslots)):
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

    for cat, slotitems in cats.items():
        temp_items = slotitems.items()
        temp_items.sort(lambda a, b: cmp(a[0], b[0]))
        cats[cat] = [i[1] for i in temp_items]

    return render_to_response("autolist/weektable.html",
                              {'cats': cats, 'timeslots': timeslots, 'weekday': weekday, 'total': total},
                              RequestContext(request))


def show_time_table_summary(request):
    content = request.REQUEST
    user_id = content.get('user_id', '')
    try:
        profile = User.objects.get(user=user_id)
    except Exception:
        profile = request.user.get_profile()

    items = Item.objects.filter(user=profile, approve_status=pcfg.ONSALE_STATUS).order_by('category', 'outer_id')

    weekstat = [0, 0, 0, 0, 0, 0, 0]
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
            data[cat] = [[], [], [], [], [], [], []]

        weekstat[idx] += 1
        data[cat][idx].append(item)

    cats = []
    for k, v in data.iteritems():
        t = 0
        for x in v:
            t += len(x)
        cats.append({'cat': k, 'items': v, 'total': t})
    cats.sort(lambda a, b: cmp(b['total'], a['total']))

    return render_to_response("autolist/tablesummary.html",
                              {'cats': cats, 'weekstat': weekstat, 'user_id': user_id},
                              RequestContext(request))


def show_time_table(request):
    items = Item.objects.all().order_by('category', 'outer_id')

    from common.utils import get_closest_time_slot, get_all_time_slots

    slots = get_all_time_slots()
    timekeys = slots.keys()
    timekeys.sort()

    data = [[], [], [], [], [], [], []]
    for x in data:
        for slot in timekeys:
            x.append({'slot': slot, 'items': []})

    cats = {}
    for x in items:
        relist_time, status = get_closest_time_slot(x.list_time)
        x.relist_time = "%s" % relist_time
        x.isoweekday = relist_time.isoweekday()

        slot = "%02d:%02d" % (relist_time.hour, relist_time.minute)

        x.list_time = "%s" % x.list_time

        if slot in slots:
            idx = slots[slot]
            data[x.isoweekday - 1][idx]['items'].append(x)
        else:
            print slot, x.category_name, x.list_time, x.title

        if not x.category_name in cats:
            cats[x.category_name] = 1
        else:
            cats[x.category_name] += 1

        cat = []
        for k in cats.keys():
            cat.append(k)
    return render_to_response("base.html", {'page': 'timetable', 'data': data, 'cats': cat, 'slots': slots},
                              RequestContext(request))


def get_timeslots_json(request):
    time_slots = TimeSlots.objects.all()
    slot_list = ['%02d:%02d' % (s.hour, s.minute) for s in time_slots]
    return HttpResponse(json.dumps(slot_list), content_type='application/json')


def show_logs(request):
    logs = Logs.objects.all().order_by('execute_time')
    return render_to_response("autolist/logs.html", {'logs': logs}, RequestContext(request))


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
                  datetime.timedelta(days=(now.isoweekday() - weekday))

    if target_time < now:
        target_time = target_time + datetime.timedelta(days=7)

    o.num_iid = num_iid
    o.user_id = item.user.visitor_id
    o.nick = item.user.nick
    o.title = item.title
    o.num = item.num
    o.list_weekday = target_time.isoweekday()
    o.list_time = delist_time
    o.task_type = LISTING_TYPE
    o.status = UNEXECUTE
    o.save()

    return HttpResponse(json.dumps({'list_weekday': target_time.strftime("%Y-%m-%d"),
                                    'list_time': target_time.strftime("%H:%M")}), content_type='application/json')


################################ List View ##############################
from rest_framework import renderers


class ListItemTaskView(APIView):
    # queryset = ItemListTask.objects.all()
    #     serializer_class = serializers. ItemListTaskSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = None

    def get(self, request, *args, **kwargs):
        # print 'debug:',args,kwargs
        # model = self.resource.model

        model = ItemListTask
        visitor_id = request.session['top_parameters']['visitor_id']
        # visitor_id=1
        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()
        # print queryset,"66666666666"
        if hasattr(self, 'serializer_class'):
            ordering = getattr(self.serializer_class, 'ordering', None)
            # print "resource"
        else:
            ordering = None
            # print "resource33"
        kwargs.update({'user_id': visitor_id})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
            # return Response(queryset)
            # return Response(queryset.filter(**kwargs))
        serializer = serializers.ItemListTaskSerializer(queryset.filter(**kwargs), many=True)
        return Response(serializer.data)

    #         return Response(data)

    def get_queryset(self):
        return self.queryset


from rest_framework import views  # CreateModelMixin


class CreateListItemTaskModelView(APIView):
    """A view which provides default operations for create, against a model in the database."""
    serializer_class = serializers.ItemListTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    # print "1111111222"
    def post(self, request, *args, **kwargs):
        # print "0000000000000000000000"
        # model = self.resource.model
        model = self.serializer_class.model
        content = dict(self.CONTENT)

        all_kw_args = dict(content.items() + kwargs.items())

        update_nums = model.objects.filter(num_iid=all_kw_args['num_iid']).update(**all_kw_args)

        if update_nums == 0:

            if args:
                instance = model(pk=args[-1], **all_kw_args)
            else:
                instance = model(**all_kw_args)
            instance.save()

            signals.post_save.send(sender=model, obj=instance, request=self.request)

        else:
            instance = model.objects.get(num_iid=all_kw_args['num_iid'], status=UNEXECUTE)

        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.resource(self).url(instance)
        return Response(status.HTTP_201_CREATED, instance, headers)


# fang  djangorestframework  utils / ini--.py
def as_tuple(obj):
    """
    Given an object which may be a list/tuple, another object, or None,
    return that object in list form.

    IE:
    If the object is already a list/tuple just return it.
    If the object is not None, return it in a list with a single element.
    If the object is None return an empty list.
    """
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)
