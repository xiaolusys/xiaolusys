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

import logging
logger = logging.getLogger(__name__)


from flashsale.xiaolumm.models_lesson import LessonTopic, Instructor, Lesson, LessonAttendRecord
from flashsale.pay.models_custom import ActivityEntry

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


def get_xiaolu_university_activity_entry():
    xiaolu_university_activity_id = 6
    records = ActivityEntry.objects.filter(id=xiaolu_university_activity_id)
    if records.count() > 0:
        return records[0]
    return None
    
    

class LessonTopicViewSet(viewsets.ModelViewSet):
    """
    Return lesson topics.
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = LessonTopic.objects.all()
    serializer_class = lesson_serializers.LessonTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        topics = self.paginate_queryset(self.queryset)
        serializer = lesson_serializers.LessonTopicSerializer(topics, many=True)
        res = self.get_paginated_response(serializer.data)
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
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = Lesson.objects.all()
    serializer_class = lesson_serializers.LessonSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_queryset(self, request):
        content = request.GET

        lesson_id = content.get("lesson_id")
        if lesson_id:
            return self.queryset.filter(id=lesson_id)
        
        return self.queryset
    
    def list(self, request, *args, **kwargs):
        query_set = self.get_queryset(request)
        datalist = self.paginate_queryset(query_set)

        customer_id = get_customer_id(request.user)
        #customer_id = 0 # debug
        for entry in datalist:
            entry.customer_idx = customer_id % 5

        serializer = lesson_serializers.LessonSerializer(datalist, many=True)
        res = self.get_paginated_response(serializer.data)
        #res['Access-Control-Allow-Origin'] = '*'
        return res

        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

from rest_framework.pagination import PageNumberPagination
class InstructorViewSet(viewsets.ModelViewSet):
    """
    Return instructors.
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = Instructor.objects.all()
    serializer_class = lesson_serializers.InstructorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
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


class LessonAttendRecordViewSet(viewsets.ModelViewSet):
    """
    Return attending records.
    
    /attendrecord?lesson_id=1&unionid=xxx
    lesson_id: lesson id
    unionid: user's unionid
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = LessonAttendRecord.objects.all()
    serializer_class = lesson_serializers.LessonAttendRecordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    #permission_classes = (permissions.IsAuthenticated, )
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
        serializer = lesson_serializers.LessonAttendRecordSerializer(topics, many=True)
        res = self.get_paginated_response(serializer.data)
        #res['Access-Control-Allow-Origin'] = '*'
        return res
        
    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


from core.weixin.mixins import WeixinAuthMixin

class WeixinSNSAuthJoinView(WeixinAuthMixin, APIView):
    """
    Lesson signup.
    """
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, lesson_id, *args, **kwargs):
        # 1. check whether event_id is valid
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        # 2. get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        #userinfo = {"unionid":"o29cQs9QlfWpL0v0ZV_b2nyTOM-4", "nickname":"zifei", "headimgurl":"xxxx"}
        if not self.valid_openid(unionid):
            # 3. get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")

            if not self.valid_openid(unionid):
                # 4. if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)

            # now we have userinfo
            logger.warn("snsauth: %s" % userinfo)
            from flashsale.promotion.tasks_activity import task_userinfo_update_application
            task_userinfo_update_application.delay(userinfo)

            from flashsale.xiaolumm.tasks_lesson import task_create_lessonattendrecord
            task_create_lessonattendrecord.delay(lesson_id, userinfo)

        activity_entry = get_xiaolu_university_activity_entry()
        key = "signup"
        html = "%s?lesson_id=%s&unionid=%s" % (activity_entry.get_html(key), lesson_id, unionid)
        response = redirect(html)
        self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response
