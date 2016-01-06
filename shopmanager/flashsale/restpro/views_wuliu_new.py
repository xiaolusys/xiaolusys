# coding=utf-8
import json
import urllib, urllib2
from rest_framework import permissions
from rest_framework import authentication
from rest_framework.response import Response
from shopback.trades.models import TradeWuliu
from shopback.items.models import Product
import datetime
from . import serializers
from flashsale.restpro.tasks import SaveWuliu_only
from rest_framework import viewsets
from rest_framework import renderers
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer, SaleTrade
from rest_framework.decorators import list_route
from shopback import paramconfig as pacg


class WuliuViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/get_wuliu_by_tid : 由tid获取物流信息
    """
    queryset = TradeWuliu.objects.all()
    serializer_class = serializers.TradeWuliuSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    gap_time = 7200  # 查询间隔时间
    BADU_KD100_URL = "http://www.kuaidiapi.cn/rest"  # 访问第三方接口
    apikey = '47deda738666430bab15306c2878dd3a'
    uid = '39400'
    default_post = 'yunda'

    BAIDU_POST_CODE_EXCHANGE = {
        'YUNDA': 'yunda', 'YUNDA_QR': 'yunda', 'STO': 'shentong', 'EMS': 'ems', 'ZTO': 'zhongtong', 'ZJS': 'zhaijisong',
        'SF': 'shunfeng', 'YTO': 'yuantong', 'HTKY': 'huitongkuaidi', 'TTKDEX': 'tiantian',
        'QFKD': 'quanfengkuaidi',
    }

    def get_trade(self, tid):
        trade = get_object_or_404(SaleTrade, tid=tid)
        return trade

    def get_status_message(self, trade):
        """ 根据交易状态不同返回不同的物流提示信息 """
        res = {u'data': [], u'errcode': u'', u'id': u'', u'message': u'',
               u'name': u'', u'order': u'', u'status': None}
        if trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:  # 如果是已经付款状态
            for t in trade.sale_orders.all():
                pro = get_object_or_404(Product, id=t.item_id)
                if pro.shelf_status == Product.UP_SHELF:  # 上架状态
                    res['message'] = "您的订单正在配货"
                    return res
            res['message'] = "付款成功"
            return res
        elif trade.status in (SaleTrade.TRADE_CLOSED_BY_SYS, SaleTrade.TRADE_NO_CREATE_PAY):
            res['message'] = "暂无更新"
            return res
        return None

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        queryset = self.queryset.filter(tid__in=(SaleTrade.objects.filter(buyer_id=customer.id).values('tid')))
        return queryset

    def list(self, request, *args, **kwargs):
        """ 根据时间判断选取list """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        return Response()

    def get_third_apidata(self, trade):
        """ 访问第三方api 获取物流参数 并保存到本地数据库　"""
        tid = trade.tid
        # 快递编码(快递公司编码)
        exType = trade.logistics_company.code if trade.logistics_company is not None else self.default_post
        data = {'id': self.BAIDU_POST_CODE_EXCHANGE.get(exType), 'order': trade.out_sid, 'key': self.apikey,
                'uid': self.uid}
        req = urllib2.urlopen(self.BADU_KD100_URL, urllib.urlencode(data), timeout=30)
        content = json.loads(req.read())
        SaveWuliu_only.delay(tid, content)  # 异步任务，存储物 流信息到数据库
        return

    def packet_data(self, queryset):
        res = {u'data': [], u'errcode': u'', u'id': u'', u'message': u'', u'name': u'', u'order': u'', u'status': None}
        for query in queryset:
            res['order'] = query.out_sid
            res['name'] = query.logistics_company
            res['status'] = query.get_status_display()
            res['errcode'] = query.errcode
            res["data"].append({"content": query.content, "time": query.time})
        return res

    @list_route(methods=['get'])
    def get_wuliu_by_tid(self, request):
        content = request.REQUEST
        tid = content.get("tid", None)
        if tid is None:  # 参数缺失
            return Response({"code": 1})
        trade = self.get_trade(tid)
        message = self.get_status_message(trade)
        if message is not None:
            return Response(message)
        else:
            queryset = self.filter_queryset(self.get_owner_queryset(request)).filter(tid=trade.tid).order_by(
                "-time")  # 这里要按照物流信息时间倒序
            if queryset.exists():
                last_wuliu = queryset[0]
                last_time = last_wuliu.created  # 数据库中最新的记录时间
                now = datetime.datetime.now()  # 现在时间
                gap_time = (now - last_time).seconds
                if gap_time <= self.gap_time or (last_wuliu.status in (pacg.RP_ALREADY_SIGN_STATUS,
                                                                       pacg.RP_REFUSE_SIGN_STATUS,
                                                                       pacg.RP_CANNOT_SEND_STATUS,
                                                                       pacg.RP_INVALID__STATUS,
                                                                       pacg.RP_OVER_TIME_STATUS,
                                                                       pacg.RP_FAILED_SIGN_STATUS)):
                    # 属性定义的请求间隙 或者是物流信息是　已经签收了 疑难单　无效单　签收失败则不更新展示数据库中的数据
                    res = self.packet_data(queryset)
                    return Response(res)
                else:  # 更新物流
                    self.get_third_apidata(trade)
                    res = self.packet_data(queryset)
                    return Response(res)
            else:  # 更新物流
                self.get_third_apidata(trade)
                res = self.packet_data(queryset)
                return Response(res)

    def create(self, request, *args, **kwargs):
        """ 创建本地物流信息存储 """
        return Response({"code": 0})

