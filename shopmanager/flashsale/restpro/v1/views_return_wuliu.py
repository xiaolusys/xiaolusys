# coding=utf-8
__author__ = "huazi"

from rest_framework import permissions
from rest_framework import authentication
from rest_framework.decorators import list_route
from shopback.trades.models import ReturnWuLiu
from shopback.items.models import Product
from . import serializers
from flashsale.pay.models import Customer, SaleTrade
from shopback.logistics.models import LogisticsCompany
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from shopback.trades.models import TradeWuliu
from flashsale.restpro import wuliu_choice
import logging
from shopback.logistics.models import LogisticsCompany

logger = logging.getLogger('lacked_wuliu_company_name')
class ReturnWuliuViewSet(viewsets.ModelViewSet):
    """
    {prefix}/get_wuliu_by_tid: 由tid获取退货物流信息
    """
    queryset = ReturnWuLiu.objects.all()
    serializers_class = serializers.ReturnWuliuSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BaseAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    gap_time = 7200  #查询时间间隔 2个小时

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        queryset = self.queryset.filter(tid__in=(SaleTrade.objects.filter(buyer_id=customer.id).values('tid')))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        根据客户的id的tid获取相应的物流信息
        """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        return Response(queryset)


    def get_trade(self, tid):
        try:
            saletrade = get_object_or_404(SaleTrade, tid=tid)
        except:
            saletrade = get_object_or_404(SaleTrade, id=tid)
        return saletrade

    def get_status_message(self, trade):
        """根据交易状态不同返回不同的物流提示信息"""
        res = {u'data':[],u'errcode':u'', u'id':u'', u'message':u'',
               u'name':u'', u'order':u'',u'status':None}
        if trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:
            for t in trade.sale_orders.all():
                pro = get_object_or_404(Product, id=t.item_id)
                if pro.shelf_status == Product.UP_SHELF:
                    res[u'message'] = "您的订单正在配货"
                    return res
                res[u'message'] = "付款成功"
                return res
        elif trade.status in (SaleTrade.TRADE_CLOSED_BY_SYS,
                              SaleTrade.TRADE_NO_CREATE_PAY,
                              SaleTrade.WAIT_BUYER_PAY,
                              SaleTrade.TRADE_CLOSED):
            res[u'message'] = trade.get_status_display()
            return res
        return None

    def packet_data(self, queryset):
        res = {u'data':[], u'errcode':u'', u'id':u'', u'message':u'',u'name':u'',u'order':u'',u'status':None}
        for query in queryset:
            res['order'] = query.out_sid
            res['name'] = query.logistics_company
            res['status'] = query.get_status_display()
            res['errcode'] = query.errcode
            res['data'].append({"content":query.content,"time":query.time})
        return res

    # @list_route(methods=['get'])
    # def get_return_wuliu_by_tid(self, request):
    #     content = request.REQUEST
    #     tid = content.get("tid",None)
    #     if tid is None:
    #         return Response({"code":1})
    #     trade = self.get_trade(tid)
    #     message = self.get_status_message(trade)
    #     if message is not None:
    #         return Response(message)
    #     else:
    #         queryset = self.queryset.filter(tid=trade.tid).order_by("-time")
    #         if queryset.exists():
    #             last_wuliu = queryset[0]
    #             last_time = last_wuliu.created
    #             now = datetime.datetime.now()
    #             gap_time = (now - last_time).seconds
    #             if gap_time <= self.gap_time or (last_wuliu.status in (pacg.RP_ALREADY_SIGN_STATUS,
    #                                                                    pacg.RP_REFUSE_SIGN_STATUS,
    #                                                                    pacg.RP_CANNOT_SEND_STATUS,
    #                                                                    pacg.RP_INVALID__STATUS,
    #                                                                    pacg.RP_OVER_TIME_STATUS,
    #                                                                    pacg.RP_FAILED_SIGN_STATUS)):
    #                 res = self.packet_data(queryset)
    #                 return Response(res)
    #             else: #更新物流
    #                 get_third
    #                 _apidata.delay(trade)  #退货物流接口要重写
    #                 res = self.packet_data(queryset)
    #                 return Response(res)

    def get_company_code(self,company_name):
        company_id = LogisticsCompany.objects.filter(name=company_name).first()
        if not company_id:
            lc = LogisticsCompany.objects.values("name")
            head = company_name.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')
            sim = [j['name'] for j in lc if j['name'].find(head)!=-1]
            if len(sim):
                company_id = LogisticsCompany.objects.get(name=sim[0])
        if company_id:
            return company_id.express_key
        else:
            logger.warn(company_name)
            return None

    @list_route(methods=['get'])
    def get_wuliu_company_code(self, request):
        company_name = request.REQUEST.get("company_name",None)
        if company_name is None:

            return Response([])
        else:
            return Response({'company_name':company_name,'company_id':self.get_company_code(company_name)})

    # @list_route(methods=['get'])
    # def get_wuliu_by_packetid(self, request):
    #     content = request.REQUEST
    #     packetid = content.get("packetid", None)
    #     packetid = ''.join(str(packetid).split())
    #     company_name = content.get("company_name",None)
    #     rid = content.get("rid",None)
    #     if company_name:
    #         company_code = self.get_company_code(company_name)
    #     # company_code = content.get("company_code", None)
    #     if not packetid or not company_code or not rid:
    #         return Response({"errorinfo":"物流编号,物流公司编号或者退货单编号不存在"})
    #     queryset = ReturnWuLiu.objects.filter(out_sid=packetid).order_by("-time")
    #     if queryset.exists():
    #         last_wuliu = queryset[0]
    #         last_time = last_wuliu.created
    #         now = datetime.datetime.now()
    #         gap_time = (now - last_time).seconds
    #         if gap_time <= self.gap_time or (last_wuliu.status in (pacg.RP_ALREADY_SIGN_STATUS,
    #                                                                pacg.RP_REFUSE_SIGN_STATUS,
    #                                                                pacg.RP_CANNOT_SEND_STATUS,
    #                                                                pacg.RP_INVALID__STATUS,
    #                                                                pacg.RP_OVER_TIME_STATUS,
    #                                                                pacg.RP_FAILED_SIGN_STATUS)):
    #             res = self.packet_data(queryset)
    #             return Response(res)
    #         else:  #更新物流
    #             get_third_apidata_by_packetid_return(rid, packetid, company_code)
    #             res = self.packet_data(queryset)
    #             return Response(res)
    #     else:
    #         get_third_apidata_by_packetid_return(rid, packetid, company_code)
    #         res = self.packet_data(queryset)
    #         return Response(res)

    @list_route(methods=['get'])
    def get_wuliu_by_packetid(self, request):
        content = request.REQUEST
        packetid = content.get("packetid",None)
        packetid = ''.join(str(packetid).split())
        company_name = content.get("company_name",None)
        if not packetid or not company_name:
            return Response({"errorinfo":"物流编号,物流公司编号或者退货单编号不存在"})
        logistics_company = company_name
        out_sid = packetid
        assert logistics_company is not None,'物流公司不能为空'
        assert out_sid is not None, '物流单号不能为空'
        tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid).order_by("-id")
        if tradewuliu.first():
            result = wuliu_choice.result_choice[1](logistics_company,
                                                             out_sid,
                                                             tradewuliu.first())
        else:
            result = wuliu_choice.result_choice[0](logistics_company,
                                                             out_sid,
                                                             tradewuliu.first())
        return Response(result)

    def create(self, request, *args, **kwargs):
        """创建本地物流存储"""
        return Response({"code":0})