# -*- coding:utf8 -*-
import datetime
import json
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Q, Sum
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication

from . import serializers
from core.options import log_action, User as DjangoUser, ADDITION, CHANGE
from shopback.base.new_renders import new_BaseJSONRenderer
from shopapp.calendar.models import StaffEvent
from common.utils import parse_datetime, format_datetime


def get_users_by_string(executor_strng):
    ectors = executor_strng.split(',')

    exectors = []

    if 'everyone' in ectors:
        return DjangoUser.objects.filter(is_active=True, is_staff=True)

    for s in ectors:
        try:
            django_user = DjangoUser.objects.get(username=s)
        except:
            continue
        exectors.append(django_user)

    return exectors


def delete_staff_event(request, id):
    eff_row = StaffEvent.objects.filter(id=id).update(status='cancel')

    ret = {}
    if eff_row == 1:
        ret = {'code': 0, 'response_content': 'success'}

        event = StaffEvent.objects.get(id=id)

        log_action(request.user.id, event, CHANGE, u'取消事件')
    else:
        ret = {'code': 1, 'response_error': 'fail'}

    return HttpResponse(json.dumps(ret), content_type="application/json")


def complete_staff_event(request, id):
    try:
        event = StaffEvent.objects.get(id=id)
    except StaffEvent.DoesNotExist:
        ret = {'code': 1, 'response_error': '未找到该事件'}
    else:
        event.is_finished = True
        event.save()

        ret = {'code': 0, 'response_content': {
            'id': event.id,
            'creator': event.creator.username,
            'executor': event.executor.username,
            'start': format_datetime(event.start),
            'end': format_datetime(event.end),
            'interval_day': event.interval_day,
            'title': event.title,
            'type': event.type,
            'created': format_datetime(event.created),
            'modified': format_datetime(event.modified),
            'is_finished': event.is_finished,
        }}
        log_action(request.user.id, event, CHANGE, u'完成事件')

    return HttpResponse(json.dumps(ret), content_type="application/json")


class MainEventPageView(APIView):
    """ docstring for class MainEventPageView """

    serializer_class = serializers.MainStaffEventSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (new_BaseJSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer)
    template_name = "fullcalendar/default.html"

    def get(self, request, *args, **kwargs):
        cur_user = request.user
        staffs = DjangoUser.objects.filter(is_active=True, is_staff=True)

        return Response({'curuser': cur_user, 'staffs': staffs})


class StaffEventView(APIView):
    """ docstring for class StaffEventView """
    # print "88855656+44"
    # serializer_class = serializers.StaffEventSerializer  #baocuo   xuyao kaolvhao
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)

    # template_name = "fullcalendar/default.html"
    def get(self, request, *args, **kwargs):
        # print "get99"
        content = request.GET
        exector = content.get('exector')
        date_type = content.get('date_type', 'task')
        finished = content.get('is_finished', '')
        order_desc = content.get('order_desc')
        df = content.get('df')
        dt = content.get('dt')

        try:
            django_user = DjangoUser.objects.get(username=exector)
        except:
            django_user = request.user

        start = parse_datetime(df)
        end = dt and parse_datetime(dt) or None

        staff_events = StaffEvent.objects.filter(Q(executor=django_user) | Q(creator=django_user), status='normal')
        if finished:
            staff_events = staff_events.filter(is_finished=finished.upper() == 'Y')

        order_by = ''
        if date_type == 'task':
            if end:
                staff_events = staff_events.filter(Q(start__gte=start) | Q(end__lte=end))
            else:
                staff_events = staff_events.filter(start__gte=start)

            order_by = order_desc == '1' and '-end' or 'start'
        elif date_type == 'modify':
            staff_events = staff_events.filter(modified__gte=start)
            if end:
                staff_events = staff_events.filter(modified__lte=end)

            order_by = order_desc == '1' and '-modified' or 'modified'
        elif date_type == 'create':
            staff_events = staff_events.filter(created__gte=start)
            if end:
                staff_events = staff_events.filter(created__lte=end)

            order_by = order_desc == '1' and '-created' or 'created'

        if order_by:
            staff_events = staff_events.order_by(order_by)

        staff_list = []
        for event in staff_events:
            staff_dict = {
                'id': event.id,
                'creator': event.creator.username,
                'executor': event.executor.username,
                'start': event.start,
                'end': event.end,
                'interval_day': event.interval_day,
                'title': event.title,
                'type': event.type,
                'created': event.created,
                'modified': event.modified,
                'is_finished': event.is_finished,
            }
            staff_list.append(staff_dict)

        return Response(staff_list)

    def post(self, request, *args, **kwargs):
        creator = request.user
        content = request.POST

        start = content.get('start')
        end = content.get('end')

        start = parse_datetime(start)
        end = end and parse_datetime(end) or datetime.datetime(start.year, start.month, start.day)

        interval_day = content.get('interval_day', '0')
        title = content.get('title')
        type = content.get('type', 'temp')

        executor_string = content.get('executor', '')

        exectors = get_users_by_string(executor_string) or [creator]

        staff_events = []
        for executor in exectors:
            staff_event = StaffEvent.objects.create(
                executor=executor,
                creator=creator,
                start=start,
                end=end,
                interval_day=interval_day,
                title=title,
                type=type
            )
            staff_events.append(staff_event)

        staff_list = []
        for event in staff_events:
            staff_dict = {
                'id': event.id,
                'creator': event.creator.username,
                'executor': event.executor.username,
                'start': event.start,
                'end': event.end,
                'interval_day': event.interval_day,
                'title': event.title,
                'type': event.type,
                'created': event.created,
                'modified': event.modified,
                'is_finished': event.is_finished,
            }
            staff_list.append(staff_dict)
        return Response(staff_list)


###############
class BaseJsonRenderer222(JSONRenderer):
    """
    Renderer which serializes to JSON
    """
    media_type = 'application/json'
    format = 'json'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* into serialized JSON.
        """
        if isinstance(obj, (list, tuple,)):
            obj = {"code": 0, "response_content": obj}
        elif isinstance(obj, dict) and (obj.has_key('code') or obj.has_key('field-errors')
                                        or obj.has_key('errors') or obj.has_key('errcode')):
            pass
        elif isinstance(obj, dict):
            obj = {"code": 0, "response_content": obj}
        else:
            obj = {"code": 1, "response_error": obj}

        # If the media type looks like 'application/json; indent=4', then
        # pretty print the result.
        indent = get_media_type_params(media_type).get('indent', None)
        sort_keys = False
        try:
            indent = max(min(int(indent), 8), 0)
            sort_keys = True
        except (ValueError, TypeError):
            indent = None

        return json.dumps(obj, cls=DjangoJSONEncoder, indent=indent, sort_keys=sort_keys)
