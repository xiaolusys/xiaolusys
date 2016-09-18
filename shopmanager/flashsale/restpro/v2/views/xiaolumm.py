# coding=utf-8
import datetime
import logging
import os
import time
import urlparse

from django.conf import settings
from django.db.models import Sum, Count
from django_statsd.clients import statsd
from django.shortcuts import get_object_or_404
from rest_framework import authentication
from core import xlmm_rest_exceptions as exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import redirect

from core.xlmm_response import make_response, SUCCESS_RESPONSE
from shopapp.weixin.weixin_apis import WeiXinAPI
from flashsale.pay.models import Customer, ModelProduct
from flashsale.restpro import permissions as perms
from flashsale.xiaolumm.models.models_fortune import MamaFortune, CarryRecord, ActiveValue, OrderCarry, ClickCarry, \
    AwardCarry, ReferalRelationship, GroupRelationship, UniqueVisitor, DailyStats

from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.push.models_message import PushMsgTpl

from .. import serializers

logger = logging.getLogger(__name__)


def get_customer_id(user):
    # return 19 # debug test
    customer = Customer.objects.normal_customer.filter(user=user).first()
    if customer:
        return customer.id
    return None


def get_mama_id(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    mama_id = None
    if customer:
        xlmm = customer.get_charged_mama()
        if xlmm:
            mama_id = xlmm.id
    # mama_id = 5 # debug test
    return mama_id


def get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field, exclude_statuses=None):
    qset = queryset.filter(mama_id=mama_id, date_field__gte=from_date, date_field__lte=end_date)

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
    sum_dict = get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field,
                                        exclude_statuses=exclude_statuses)

    for entry in datalist:
        key = entry.date_field
        if key in sum_dict:
            entry.today_carry = float('%.2f' % (sum_dict[key] * scale))



from flashsale.xiaolumm.tasks_mama_fortune import task_mama_daily_app_visit_stats, task_mama_daily_tab_visit_stats

class MamaFortuneViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = MamaFortune.objects.all()
    serializer_class = serializers.MamaFortuneSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)

    def list(self, request, *args, **kwargs):

        statsd.incr('xiaolumm.mamafortune_count')

        # fortunes = self.get_owner_queryset(request)
        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        mama_id = None
        xlmm = None
        if customer:
            xlmm = customer.get_charged_mama()
            if xlmm:
                mama_id = xlmm.id
                ua = request.META.get('HTTP_USER_AGENT', 'unknown')
                task_mama_daily_app_visit_stats.delay(mama_id, ua)

        fortunes = self.queryset.filter(mama_id=mama_id)
        # fortunes = self.paginate_queryset(fortunes)
        serializer = serializers.MamaFortuneSerializer(fortunes, many=True,
                                                       context={'request': request,
                                                                "customer": customer,
                                                                "xlmm": xlmm})
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"mama_fortune": res})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def get_mama_app_download_link(self, request):
        """ 妈妈的app下载链接 """
        from core.upload.xqrcode import push_qrcode_to_remote

        mama_id = get_mama_id(request.user)
        qrcode_url = ''
        mama_fortune = None
        if mama_id and int(mama_id) > 0:  # 如果有代理妈妈
            # wx_api = WeiXinAPI()
            # wx_api.setAccountId(appKey=settings.WXPAY_APPID)
            # resp = wx_api.createQRcode('QR_SCENE', mama_id)
            # qrcode_url = wx_api.genQRcodeAccesssUrl(resp.get('ticket',''))
            mama_fortune = self.queryset.filter(mama_id=mama_id).first()
            if mama_fortune:
                qrcode_url = mama_fortune.app_download_qrcode_url
            else:
                logger.warn("get_mm_app_download_link: mm id %s cant find mama_fortune" % mama_id)
        else:
            logger.warn("get_mm_app_download_link: request.user %s cant find mama_id" % request.user)
        if not qrcode_url:  # 如果没有则生成链接上传到七牛 并且更新到字段
            customer_id = get_customer_id(request.user)
            params = {'from_customer': customer_id, "time_str": int(time.time())}
            share_link = "/sale/promotion/appdownload/?from_customer={from_customer}"
            share_link = urlparse.urljoin(settings.M_SITE_URL, share_link).format(**params)
            file_name = os.path.join('qrcode/mm_appdownload',
                                     'from_customer_{from_customer}_{time_str}.jpg'.format(**params))
            qrcode_url = push_qrcode_to_remote(file_name, share_link)
            if mama_fortune:
                kwargs = {"app_download_qrcode_url": qrcode_url}
                mama_fortune.update_extras_qrcode_url(**kwargs)
        return Response({"code": 0, "qrcode_url": qrcode_url})


class CarryRecordViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = CarryRecord.objects.all()
    serializer_class = serializers.CarryRecordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        qset = self.queryset.filter(mama_id=mama_id)
        task_mama_daily_tab_visit_stats.delay(mama_id, MamaTabVisitStats.TAB_CARRY_RECORD)

        # we dont return canceled record
        if exclude_statuses:
            for ex in exclude_statuses:
                qset = qset.exclude(status=ex)

        return qset.order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_carryrecord_count')

        exclude_statuses = [3, ]
        datalist = self.get_owner_queryset(request, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)
        sum_field = 'carry_num'

        if len(datalist) > 0:
            add_day_carry(datalist, self.queryset, sum_field, exclude_statuses=exclude_statuses)
        serializer = serializers.CarryRecordSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class OrderCarryViewSet(viewsets.ModelViewSet):
    """
    return mama's order list (including web/app direct orders, and referal's orders).
    with parameter "?carry_type=direct", will return only direct orders.
    ### carry_type:
      - 1 : Web直接订单,
      - 2 : App订单,
      - 3 :下属订单,

    ### GET /rest/v2/ordercarry/get_latest_order_carry 获取所有用户最近２０条订单收益记录
    - Response
    ```
    [
         {
        "content": "子飞@小鹿美美收到一笔收益0.81元",
        "avatar": "http://wx.qlogo.cn/m"
        },
    ]
    ```
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = OrderCarry.objects.all()
    page_size = 10
    serializer_class = serializers.OrderCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request, carry_type, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        if carry_type == "direct":

            visit_tab = MamaTabVisitStats.TAB_ORDER_CARRY
            task_mama_daily_tab_visit_stats.delay(mama_id, visit_tab)

            return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

        qset = self.queryset.filter(mama_id=mama_id)
        if exclude_statuses:
            for ex in exclude_statuses:
                qset = qset.exclude(status=ex)
        return qset.order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        exclude_statuses = [0, 3]  # not show unpaid/canceled orders

        carry_type = request.REQUEST.get("carry_type", "all")
        if carry_type == "direct":
            exclude_statuses = None  # show all orders excpet indirect ones

        datalist = self.get_owner_queryset(request, carry_type, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)

        # find from_date and end_date in datalist
        mama_id, from_date, end_date = None, 0, 0
        if len(datalist) > 0:
            sum_field = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_field, exclude_statuses=exclude_statuses)
        serializer = serializers.OrderCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['GET'])
    def get_latest_order_carry(self, request, *args, **kwargs):
        ordercarrys = self.queryset.filter().exclude(carry_num=0).order_by('-created')[:20]
        items = []
        msgtpl = PushMsgTpl.objects.filter(id=12, is_valid=True).first()

        if not msgtpl:
            return Response([])

        for ordercarry in ordercarrys:
            try:
                mama = XiaoluMama.objects.filter(id=ordercarry.mama_id).first()
                customer = mama.get_customer()
                money = '%.2f' % ordercarry.carry_num_display()
                nick = customer.nick
                content = msgtpl.get_emoji_content().format(nick=nick[:8], money=money)
            except Exception:
                continue

            items.append({
                'content': content,
                'avatar': customer.thumbnail,
            })
        items.reverse()
        return Response(items)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class ClickCarryViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = ClickCarry.objects.all()
    serializer_class = serializers.ClickCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)
        if len(datalist) > 0:
            sum_field = 'total_value'
            add_day_carry(datalist, self.queryset, sum_field)

        serializer = serializers.ClickCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class AwardCarryViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = AwardCarry.objects.all()
    serializer_class = serializers.AwardCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_field = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_field)
        serializer = serializers.AwardCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class ActiveValueViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = ActiveValue.objects.all()
    serializer_class = serializers.ActiveValueSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        qset = self.queryset.filter(mama_id=mama_id)

        # we dont return canceled record
        if exclude_statuses:
            for ex in exclude_statuses:
                qset = qset.exclude(status=ex)

        return qset.order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_active_count')

        exclude_statuses = [3, ]
        datalist = self.get_owner_queryset(request, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_field = 'value_num'
            add_day_carry(datalist, self.queryset, sum_field, scale=1, exclude_statuses=exclude_statuses)

        serializer = serializers.ActiveValueSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class ReferalRelationshipViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = ReferalRelationship.objects.all()
    serializer_class = serializers.ReferalRelationshipSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(referal_from_mama_id=mama_id, referal_type__lte=XiaoluMama.HALF).order_by('-created')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_referalrelationship_count')

        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.ReferalRelationshipSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class GroupRelationshipViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = GroupRelationship.objects.all()
    serializer_class = serializers.GroupRelationshipSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(leader_mama_id=mama_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.GroupRelationshipSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class UniqueVisitorViewSet(viewsets.ModelViewSet):
    """
    given from=0 (or omit), we return today's visitors;
    given from=2 , we return all the visitors for 2 days ago.
    given recent=2, return all the visitors from 2 days ago,including 3 days.
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = UniqueVisitor.objects.all()
    serializer_class = serializers.UniqueVisitorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        content = request.REQUEST
        days_from = int(content.get("from", 0))
        days_recent = int(content.get("recent", 0))

        date_field = datetime.datetime.now().date()
        if days_from > 0:
            date_field = date_field - datetime.timedelta(days=days_from)

        mama_id = get_mama_id(request.user)
        task_mama_daily_tab_visit_stats.delay(mama_id,MamaTabVisitStats.TAB_VISITOR_LIST)

        if days_recent > 0:
            date_field = date_field - datetime.timedelta(days=days_recent)
            return self.queryset.filter(mama_id=mama_id, date_field__gt=date_field).order_by('-created')
        else:
            return self.queryset.filter(mama_id=mama_id, date_field=date_field).order_by('-created')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_uniquevisitor_count')

        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.UniqueVisitorSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


from flashsale.xiaolumm.models.models_fans import XlmmFans


class XlmmFansViewSet(viewsets.ModelViewSet):
    """
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = XlmmFans.objects.all()
    serializer_class = serializers.XlmmFansSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer_id = get_customer_id(request.user)
        mama_id = get_mama_id(request.user)
        task_mama_daily_tab_visit_stats.delay(mama_id,MamaTabVisitStats.TAB_FANS_LIST)

        return self.queryset.filter(xlmm_cusid=customer_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_fans_count')

        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.XlmmFansSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['POST'])
    def change_mama(self, request):
        new_mama_id = request.REQUEST.get('new_mama_id')
        fans = XlmmFans.get_by_customer_id(request.user.customer.id)
        new_mama = get_object_or_404(XiaoluMama, pk=new_mama_id)
        if not fans:
            try:
                XlmmFans.bind_mama(request.user.customer, new_mama)
            except Exception, e0:
                raise exceptions.ValidationError(make_response(e0.message))
        if new_mama.id == fans.xlmm:
            raise exceptions.ValidationError(make_response(u'更换的新妈妈ID与原小鹿妈妈ID必须不一致'))
        fans.change_mama(new_mama)
        return Response(SUCCESS_RESPONSE)

    @detail_route(methods=['POST', 'GET'])
    def bind_mama(self, request, pk):
        try:
            pk=int(pk)
        except:
            raise exceptions.ValidationError(make_response(u'妈妈id必须为整数'))
        cus = request.user.customer
        mama = get_object_or_404(XiaoluMama, pk=pk)
        try:
            XlmmFans.bind_mama(cus, mama)
        except Exception, e0:
            # raise exceptions.ValidationError(e0.message)
            raise exceptions.ValidationError(make_response(e0.message))
        return Response(SUCCESS_RESPONSE)


def match_data(from_date, end_date, visitors, orders):
    """
    match visitors/orders data according to date range.
    """
    data = []
    i, j = 0, 0
    maxi, maxj = len(visitors), len(orders)

    from_date = from_date + datetime.timedelta(1)
    while from_date <= end_date:
        visitor_num, order_num, carry = 0, 0, 0
        if i < maxi and visitors[i]["date_field"] == from_date:
            visitor_num = visitors[i]["visitor_num"]
            i += 1

        if j < maxj and orders[j]["date_field"] == from_date:
            order_num, carry = orders[j]["order_num"], orders[j]["carry"]
            j += 1

        entry = {"date_field": from_date, "visitor_num": visitor_num,
                 "order_num": order_num, "carry": float('%.2f' % (carry * 0.01))}
        data.append(entry)
        from_date += datetime.timedelta(1)
    return data


class OrderCarryVisitorView(APIView):
    """
    given from=2 and days=5, we find out all 5 days' data, starting
    from 2 days ago, backing to 7 days ago.
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = UniqueVisitor.objects.all()
    page_size = 10
    serializer_class = serializers.UniqueVisitorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get(self, request):
        content = request.REQUEST
        days_from = int(content.get("from", 0))
        days_length = int(content.get("days", 1))

        mama_id = get_mama_id(request.user)

        today_date = datetime.datetime.now().date()
        end_date = today_date - datetime.timedelta(days_from)
        from_date = today_date - datetime.timedelta(days_from + days_length)

        visitors = self.queryset.filter(mama_id=mama_id, date_field__gt=from_date, date_field__lte=end_date).order_by(
            'date_field').values('date_field').annotate(visitor_num=Count('pk'))
        orders = OrderCarry.objects.filter(mama_id=mama_id, date_field__gt=from_date,
                                           date_field__lte=end_date).order_by('date_field').values(
            'date_field').annotate(order_num=Count('pk'), carry=Sum('carry_num'))

        data = match_data(from_date, end_date, visitors, orders)
        return Response(data)


def fill_data(data, from_date, end_date):
    res = []
    i = len(data) - 1

    while from_date <= end_date:
        visitor_num, order_num, carry = 0, 0, 0
        if i >= 0 and data[i]["date_field"] == str(from_date):
            visitor_num, order_num, carry = data[i]["today_visitor_num"], data[i]["today_order_num"], data[i][
                "today_carry_num"]
            i = i - 1
        entry = {"date_field": from_date, "visitor_num": visitor_num, "order_num": order_num, "carry": carry}
        res.append(entry)
        from_date += datetime.timedelta(1)

    return res


class DailyStatsViewSet(viewsets.ModelViewSet):
    """
    given from=2 and days=5, we find out all 5 days' data, starting
    from 2 days ago, backing to 7 days ago.

    from=x: starts from x days before
    days=n: needs n days' data
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = DailyStats.objects.all()
    serializer_class = serializers.DailyStatsSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request, from_date, end_date):
        mama_id = get_mama_id(request.user)

        return self.queryset.filter(mama_id=mama_id, date_field__gte=from_date, date_field__lte=end_date).order_by(
            '-date_field', '-created')

    def list(self, request, *args, **kwargs):
        content = request.REQUEST
        days_from = int(content.get("from", 0))
        days_length = int(content.get("days", 1))

        today_date = datetime.datetime.now().date()
        end_date = today_date - datetime.timedelta(days=days_from)
        from_date = end_date - datetime.timedelta(days=days_length - 1)

        datalist = self.get_owner_queryset(request, from_date, end_date)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.DailyStatsSerializer(datalist, many=True)
        res = fill_data(serializer.data, from_date, end_date)

        return self.get_paginated_response(res)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


from flashsale.pay.serializers import ModelProductSerializer


class ModelProductViewSet(viewsets.ModelViewSet):
    """
    1) /rest/v2/mama/modelproducts
       returns all model_products
    2) /rest/v2/mama/modelproducts?category=1
       returns all model_products with category=1
    """
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    queryset = ModelProduct.objects.all()
    serializer_class = ModelProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, category):
        today_date = datetime.datetime.now().date()
        last_date = today_date - datetime.timedelta(days=1)
        queryset = self.queryset.filter(sale_time__gte=last_date, sale_time__lte=today_date)

        category = int(category)
        if category > 0:
            queryset = queryset.filter(category=category)

        return queryset.order_by('-sale_time')

    def list(self, request, *args, **kwargs):
        statsd.incr('xiaolumm.mama_productselection_count')

        content = request.REQUEST
        category = content.get("category", "0")

        datalist = self.get_owner_queryset(category)
        datalist = self.paginate_queryset(datalist)

        serializer = ModelProductSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


from rest_framework import generics
from flashsale.promotion.models import AppDownloadRecord


class PotentialFansView(generics.GenericAPIView):
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, *args, **kwargs):
        customer_id = get_customer_id(request.user)
        # customer_id = 1
        records = AppDownloadRecord.objects.filter(from_customer=customer_id, status=AppDownloadRecord.UNUSE).order_by(
            '-created')
        datalist = self.paginate_queryset(records)
        serializer = serializers.AppDownloadRecordSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)


class MamaAdministratorViewSet(APIView):
    """
    ## GET /rest/v2/mama/administrator
    """

    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        from flashsale.xiaolumm.models.mama_administrator import MamaAdministrator

        customer = Customer.getCustomerByUser(user=request.user)
        if not customer:
            return Response({"code": 1, "info": u"用户未找到"})  # 登录过期

        mama = customer.get_xiaolumm()
        if not mama:
            return Response({"code": 1, "info": u'没有这个妈妈'})

        referal_mama_ids = mama.get_parent_mama_ids()
        if referal_mama_ids:
            referal_mama_id = referal_mama_ids[0]
            referal_mama = XiaoluMama.objects.filter(id=referal_mama_id).first()
            referal_customer = referal_mama.get_customer()
            referal_mama_nick = referal_customer.nick
            referal_mama_avatar = referal_customer.thumbnail
        else:
            referal_mama_nick = ''
            referal_mama_avatar = ''

        administrator = MamaAdministrator.get_or_create_by_mama(mama)

        return Response({
            'mama_id': mama.id,
            'qr_img': administrator.weixin_qr_img,
            'referal_mama_nick': referal_mama_nick,
            'referal_mama_avatar': referal_mama_avatar,
        })



class ActivateMamaView(APIView):
    """
    GET /rest/v2/mama/activate
    """
    
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


    def get(self, request, *args, **kwargs):
        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        mama = customer.get_xiaolumm()

        redirect_link = "/mall/"
        if mama:
            redirect_link = "/m/%s" % mama.id
            task_mama_daily_tab_visit_stats.delay(mama.id, MamaTabVisitStats.TAB_WX_MAMA_ACTIVATE)

        return redirect(redirect_link)

        
