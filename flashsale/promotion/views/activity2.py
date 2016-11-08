# coding=utf-8
import datetime
import django_filters
from operator import itemgetter
from itertools import groupby

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from ..models.activity import ActivityEntry
from ..serializers.activity import ActivitySerializer
from ..apis.activity import get_activity_by_id, create_activity, update_activity
from ..utils import choice_2_name_value
from ..deps import get_future_schedules


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = ActivityEntry.objects.all()
    serializer_class = ActivitySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException(u'不予删除操作')

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        act_type = choice_2_name_value(ActivityEntry.ACT_CHOICES)
        f_schedules = get_future_schedules().values('id', 'sale_time')
        return Response({
            'act_type': act_type,
            'schedules': f_schedules
        })

    def create(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = request.data.pop('title')
        act_type = request.data.pop('act_type')
        start_time = datetime.datetime.strptime(request.data.pop('start_time'), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(request.data.pop('end_time'), '%Y-%m-%d %H:%M:%S')
        activity = create_activity(
            title=title,
            act_type=act_type,
            start_time=start_time,
            end_time=end_time,
            **request.data
        )
        serializer = self.get_serializer(activity)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        partial = kwargs.pop('partial', False)
        instance_id = kwargs.get('pk')
        activity = get_activity_by_id(instance_id)
        serializer = self.get_serializer(activity, data=request.data, partial=partial)
        start_time = datetime.datetime.strptime(request.data.pop('start_time'), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(request.data.pop('end_time'), '%Y-%m-%d %H:%M:%S')
        request.data.update({'start_time': start_time, 'end_time': end_time})
        serializer.is_valid(raise_exception=True)
        update_activity(instance_id, **request.data)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def create_pro_info_by_topic_schedule(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        activity_id = kwargs.get('pk')
        schedule_id = request.get('schedule_id')

        return Response()
