# coding=utf-8
import datetime
from django.db.models import Sum
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm import util_unikey
from ..serializers import lesson_serializers

import logging

logger = logging.getLogger(__name__)

from flashsale.xiaolumm.models.models_lesson import LessonTopic, Instructor, Lesson, LessonAttendRecord
from flashsale.promotion.models import ActivityEntry


def get_customer_id(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    customer_id = None
    if customer:
        customer_id = customer.id
    # customer_id = 19 # debug test
    return customer_id


def get_mama_id(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    mama_id = None
    if customer:
        xlmm = customer.get_charged_mama()
        if xlmm:
            mama_id = xlmm.id
    # mama_id = 5 # debug test
    return mama_id


def get_xiaolu_university_activity_entry():
    xiaolu_university_activity_id = 7
    records = ActivityEntry.objects.filter(id=xiaolu_university_activity_id)
    if records.count() > 0:
        return records[0]
    return None


class LessonTopicFilter(filters.FilterSet):
    class Meta:
        model = LessonTopic
        fields = ['lesson_type', 'is_show']


class LessonTopicViewSet(viewsets.ModelViewSet):
    """
    Return lesson topics.
    ### 小鹿妈妈/主题课程接口
    - [/rest/lesson/lessontopic](/rest/lesson/lessontopic) 主题课程list:
        1. method: get
            * 可过滤字段: `lesson_type`: 课程类型（3:基础课程,0: 课程,1: 实战, 2:知识）
            * 可排序字段: `ordering`: 排序（num_attender：　参加人数排序, created：　创建时间排序 ）
        2. method: patch:
            * patch 指定id  {'num_attender': 1}
            * 参数: `num_attender`: 阅读数量 值: 1

    - [/rest/lesson/lessontopic/extra_data](/rest/lesson/lessontopic/extra_data) 接口附加信息:
        1. method: get
            * 可过滤字段: `lesson_type`: 课程类型（3:基础课程,0: 课程,1: 实战, 2:知识）
            * 可排序字段: `ordering`: 排序（num_attender：　参加人数排序, created：　创建时间排序, order_weight: 排序设置值, click_num: 点击数量）
            * return: `total_num_attender`: 有效主题的总参加人数
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = LessonTopic.objects.all()
    serializer_class = lesson_serializers.LessonTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = LessonTopicFilter
    ordering_fields = ('num_attender', 'created', 'modified', 'lesson_type', 'order_weight', 'click_num')

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def extra_data(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        total_num_attender = queryset.filter(status=LessonTopic.STATUS_EFFECT).aggregate(
            s_num_attender=Sum('num_attender')).get('s_num_attender') or 0
        return Response({'total_num_attender': total_num_attender})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(is_show=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if request.data.get('num_attender') or request.data.get('click_num'):  # 上线后需要修改该参数为click_num() TODO: Jie.Lin
            request.data.update({'click_num': instance.click_num + 1})  # 点击数量加1
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        else:
            serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @detail_route(methods=['get'])
    def get_instructor_lesson(self, request, pk, *args, **kwargs):
        """
        获取讲师课程
        """
        mama_id = get_mama_id(request.user)
        customer = Customer.objects.filter(user=request.user).first()
        redirect_url = request.data.get('next') or None
        instruct_status = request.data.get('instruct_status') or 1
        if not mama_id or not customer:
            if redirect_url:
                return redirect(redirect_url)
            return Response({'code': 1, 'info': '您还不是小鹿妈妈哦~',
                             'lesson_attend_record_url': '', 'lesson': {}, 'lesson_attend_rcds': []})
        # 查看讲师记录
        instructor = Instructor.objects.filter(mama_id=mama_id).first()
        if instructor:
            instructor.update_status(status=int(instruct_status))
        else:  # 没有则创建讲师记录
            instructor = Instructor.create_instruct(
                name=customer.nick,
                title='特聘讲师',
                image=customer.thumbnail,
                introduction='',
                mama_id=mama_id,
                status=instruct_status)
        topic = self.get_object()
        lesson_uni_key = '-'.join([str(topic.id), str(mama_id)])
        # uni_key: lesson_topic_id + instructor_id
        lesson = Lesson.objects.filter(uni_key=lesson_uni_key).first()
        if not lesson:
            lesson = Lesson.create_instruct_lesson(
                lesson_topic_id=topic.id,
                title=topic.title,
                description=topic.description,
                content_link=topic.content_link,
                instructor_id=instructor.id,
                instructor_name=instructor.name,
                instructor_title=instructor.title,
                instructor_image=instructor.image,
                start_time=datetime.datetime.now(),
                uni_key=lesson_uni_key,
                status=1)
        lesson_attend_rcds = LessonAttendRecord.objects.filter(lesson_id=lesson.id)
        attend_serializer = lesson_serializers.LessonAttendRecordSerializer(lesson_attend_rcds, many=True)
        serialiser = lesson_serializers.LessonSerializer(lesson)
        return Response({'code': 0, 'info': '获取课程成功~',
                         'lesson_attend_record_url': '{0}/rest/lesson/snsauth/?lesson_id={1}&key=signup'.format(
                             settings.M_SITE_URL, lesson.id),
                         'lesson': serialiser.data,
                         'lesson_attend_rcds': attend_serializer.data})


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
    # permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        lesson_id = request.GET.get("lesson_id")
        if lesson_id:
            query_set = self.queryset.filter(id=lesson_id)
        else:
            query_set = self.queryset.filter(status=Lesson.STATUS_EFFECT)

        datalist = self.paginate_queryset(query_set)

        customer_id = get_customer_id(request.user)
        #customer_id = 0 # debug
        for entry in datalist:
            entry.customer_idx = customer_id % 5

        serializer = lesson_serializers.LessonSerializer(datalist, many=True)
        res = self.get_paginated_response(serializer.data)
        #res['Access-Control-Allow-Origin'] = '*'
        return res

    @list_route(methods=['get'])
    def get_lesson_info(self, request):
        lesson_id = request.GET.get("lesson_id")
        lesson = self.queryset.filter(id=lesson_id).first()
        if lesson:
            serializer = lesson_serializers.LessonSerializer(lesson)
            res = Response(serializer.data)
        else:
            res = Response({"code": 1, "msg": "no data"})
        #res['Access-Control-Allow-Origin'] = '*'
        return res

    @detail_route(methods=['get'])
    def lesson_sign(self, request, pk, *args, **kwargs):
        lesson = self.get_object()
        from flashsale.xiaolumm.tasks import task_create_lessonattendrecord

        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            return Response({'code': 1, 'info': '您还没有登陆哦~', 'attend_record': {}})
        userinfo = {'unionid': customer.unionid,
                    'nickname': customer.nick,
                    'headimgurl': customer.thumbnail}
        task_create_lessonattendrecord.delay(lesson.id, userinfo)
        uni_key = util_unikey.gen_lessonattendrecord_unikey(lesson.id, customer.unionid)
        record = LessonAttendRecord.objects.filter(uni_key=uni_key).first()
        serializer = lesson_serializers.LessonAttendRecordSerializer(record)
        return Response({'code': 0, 'info': '签到成功!', 'attend_record': serializer.data})

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
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = Instructor.objects.all()
    serializer_class = lesson_serializers.InstructorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, )
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        records = self.paginate_queryset(self.queryset.order_by('status'))
        serializer = lesson_serializers.InstructorSerializer(records, many=True)
        res = self.get_paginated_response(serializer.data)
        #res['Access-Control-Allow-Origin'] = '*'
        return res

    @list_route(methods=['get'])
    def get_instructor(self, request, *args, **kwargs):
        content = request.GET
        unionid = content.get('unionid')
        mamas = XiaoluMama.objects.filter(openid=unionid)
        mama = mamas.first()
        if mama:
            me = self.queryset.filter(mama_id=mama.id).first()
            serializer = lesson_serializers.InstructorSerializer(me)
            res = Response(serializer.data)
        else:
            res = Response()

        #res['Access-Control-Allow-Origin'] = '*'
        return res

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
    # permission_classes = (permissions.IsAuthenticated, )
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

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
from shopapp.weixin.models_base import WeixinUserInfo


class WeixinSNSAuthJoinView(WeixinAuthMixin, APIView):
    """
    Lesson signup.
    """
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, *args, **kwargs):
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)

        # get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        userinfo = {}
        userinfo_records = WeixinUserInfo.objects.filter(unionid=unionid)
        record = userinfo_records.first()
        if record:
            userinfo.update({"unionid": record.unionid, "nickname": record.nick, "headimgurl": record.thumbnail})
        else:
            # get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")

            if not self.valid_openid(unionid):
                # if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)

        activity_entry = get_xiaolu_university_activity_entry()
        html = settings.M_SITE_URL
        content = request.GET
        key = content.get("key")
        if key == "signup":
            lesson_id = content.get("lesson_id")
            if lesson_id:
                from flashsale.xiaolumm.tasks import task_create_lessonattendrecord

                task_create_lessonattendrecord.delay(lesson_id, userinfo)
                html = "%s?lesson_id=%s&unionid=%s" % (activity_entry.get_html(key), lesson_id, unionid)

        if key == "apply":
            from flashsale.xiaolumm.tasks import task_create_instructor_application

            task_create_instructor_application.delay(userinfo)
            html = "%s?unionid=%s" % (activity_entry.get_html(key), unionid)

        response = redirect(html)
        self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response

