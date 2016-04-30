# coding=utf-8
import os, urlparse
import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum, Count

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.views import APIView

from flashsale.pay.models import Customer
from flashsale.restpro import permissions as perms
from . import lesson_serializers


from flashsale.xiaolumm.models_lesson import LessonTopic, Instructor, Lesson, AttendRecord


def get_customer_id(user):
    customers = Customer.objects.filter(user=user)
    customer_id = None
    if customers.count() > 0:
        customer_id = customers[0].id
    #customer_id = 19 # debug test
    return customer_id


def get_mama_id(user):
    customers = Customer.objects.filter(user=user)
    mama_id = None
    if customers.count() > 0:
        customer = customers[0]
        xlmm = customer.getXiaolumm()
        if xlmm:
            mama_id = xlmm.id
    #mama_id = 5 # debug test
    return mama_id


def get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field, exclude_statuses=None):
    qset = queryset.filter(mama_id=mama_id,date_field__gte=from_date,date_field__lte=end_date)

    if exclude_statuses:
        for ex in exclude_statuses:
            qset = qset.exclude(status=ex)
    
    qset = qset.values('date_field').annotate(today_carry=Sum(sum_field))
    sum_dict = {}
    for entry in qset:
        key = entry["date_field"]
        sum_dict[key] = entry["today_carry"]
    return sum_dict


def add_day_carry(datalist, queryset, sum_field, scale=0.01, exclude_statuses=None):
    """
    计算求和字段按
    照日期分组
    添加到<today_carry>字段　的　值
    """
    mama_id = datalist[0].mama_id
    end_date = datalist[0].date_field
    from_date = datalist[-1].date_field
    ### search database to group dates and get carry_num for each group
    sum_dict = get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field, exclude_statuses=exclude_statuses)
    
    for entry in datalist:
        key = entry.date_field
        if key in sum_dict:
            entry.today_carry = float('%.2f' % (sum_dict[key] * scale))


class LessonTopicViewSet(viewsets.ModelViewSet):
    """
    Return lesson topics.
    """
    queryset = LessonTopic.objects.all()
    serializer_class = lesson_serializers.LessonTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        topics = self.paginate_queryset(self.queryset)
        serializer = lesson_serializers.LessonTopicSerializer(topics, many=True)
        res = self.get_paginated_response(serializer.data)
        res['Access-Control-Allow-Origin'] = '*'
        return res
        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class LessonViewSet(viewsets.ModelViewSet):
    """
    Return lessons.
    """
    queryset = Lesson.objects.all()
    serializer_class = lesson_serializers.LessonSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        topics = self.paginate_queryset(self.queryset)
        serializer = lesson_serializers.LessonSerializer(topics, many=True)
        res = self.get_paginated_response(serializer.data)
        res['Access-Control-Allow-Origin'] = '*'
        return res
        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class InstructorViewSet(viewsets.ModelViewSet):
    """
    Return instructors.
    """
    queryset = Instructor.objects.all()
    serializer_class = lesson_serializers.InstructorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        topics = self.paginate_queryset(self.queryset)
        serializer = lesson_serializers.InstructorSerializer(topics, many=True)
        return self.get_paginated_response(serializer.data)
        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class AttendRecordViewSet(viewsets.ModelViewSet):
    """
    Return attending records.
    
    /attendrecord?lesson_id=1&unionid=xxx
    lesson_id: lesson id
    unionid: user's unionid
    """
    queryset = AttendRecord.objects.all()
    serializer_class = lesson_serializers.AttendRecordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_queryset(self, request):
        content = request.GET

        filter_params = {}
        lesson_id = content.get("lesson_id")
        if lesson_id:
            filter_params["lesson_id"] = lesson_id

        unionid = content.get("unionid")
        if unionid:
            filter_params["student_unionid"] = unionid
        
        return self.queryset.filter(**filter_params)

    def list(self, request, *args, **kwargs):
        query_set = self.get_queryset(request)
        topics = self.paginate_queryset(query_set)
        serializer = lesson_serializers.AttendRecordSerializer(topics, many=True)
        return self.get_paginated_response(serializer.data)
        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


from core.weixin.mixins import WeixinAuthMixin

class WeixinSNSAuthJoinView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, lesson_id, *args, **kwargs):
        # 1. check whether event_id is valid
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        # 2. get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        userinfo = {"unionid":"o29cQs9QlfWpL0v0ZV_b2nyTOM-4", "nickname":"zifei", "headimgurl":"xxxx"}
        if not self.valid_openid(unionid):
            # 3. get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")

            if not self.valid_openid(unionid):
                # 4. if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)

            # now we have userinfo
            #logger.warn("snsauth: %s" % userinfo)
            from flashsale.promotion.tasks_activity import task_userinfo_update_application
            task_userinfo_update_application.delay(userinfo)

        from flashsale.xiaolumm.tasks_lesson import task_userinfo_update_attendrecord
        task_userinfo_update_attendrecord.delay(lesson_id, userinfo)

        response = redirect('/rest/lesson/attendrecord?unionid=%s' % unionid)
        self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response
