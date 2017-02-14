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
from flashsale.restpro import kdn_wuliu_extra,exp_map
from common.auth import WeAppAuthentication
from flashsale.restpro import kd100_wuliu
import json
from flashsale.restpro.tasks import create_or_update_tradewuliu
logger = logging.getLogger('lacked_wuliu_company_name')

kd100_exp_map = {"韵达":"yunda",'韵达快递':'yunda','韵达速递':'yunda',
                 "申通":"shentong","申通快递":"shentong","申通速递":"shentong",
                 "顺丰":"shunfeng","顺丰快递":"shunfeng","顺丰速递":"shunfeng",
                 "EMS":"ems",  #对应于上面物流表中EMS
                 "ems":"ems",
                 "百世":"huitongkuaidi","百世汇通":"huitongkuaidi",
                 "中通":"zhongtong","中通快递":"zhongtong","中通速递":"zhongtong",
                 "圆通":"yuantong","圆通快递":"yuantong","圆通速递":"yuantong",
                 "国通":"guotong","国通快递":"guotong","国通速递":"guotong",
                 "天天":"tiantian","天天快递":"tiantian",
                 "邮政包裹":"youzhengguonei","邮政": "youzhengguonei","邮政快递":"youzhengguonei",
                 "安能物流":"annengwuliu","安能":"annengwuliu","安能快递":"annengwuliu","安能速递":"annengwuliu",
                 "优速快递":"youshuwuliu","优速速递":"youshuwuliu","优速":"youshuwuliu",
                 "龙邦快递":"longbanwuliu","龙邦":"longbanwuliu","龙邦速递":"longbanwuliu",
                 "如风达快递":"rufengda","如风达":"rufengda","如风达速递":"rufengda",
                 "全峰快递":"quanfengkuaidi","全峰":"quanfengkuaidi","全峰速递":"quanfengkuaidi",
                 "德邦快递":"debangwuliu","德邦":"debangwuliu","德邦速递":"debangwuliu",
                 "宅急送":"zhaijisong",
                 "全一":"quanyikuaidi","全一快递":"quanyikuaidi","全一速递":"quanyikuaidi",
                 "快捷速递":"kuaijiesudi","快捷":"kuaijiesudi","快捷快递":"kuaijiesudi",
                 "DH":"dhl","DHL":"dhl",
                 "邮政小包":"youzhengguonei",
                 "天天":"tiantian",

                 }
class ReturnWuliuViewSet(viewsets.ModelViewSet):
    """
    {prefix}/get_wuliu_by_tid: 由tid获取退货物流信息
    """
    queryset = ReturnWuLiu.objects.all()
    serializers_class = serializers.ReturnWuliuSerializer
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    gap_time = 7200  #查询时间间隔 2个小时



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
            return company_id.kd100_express_key
        else:
            logger.warn(company_name)
            return None

    @list_route(methods=['get'])
    def get_wuliu_company_code(self, request):
        company_name = request.GET.get("company_name",None)
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
        content = request.GET
        packetid = content.get("packetid", None)
        company_code = content.get("company_code", None)
        company_name = content.get("company_name", None)
        if not company_code:
            company_code = exp_map.exp_map.get(str(company_name).strip())
        if packetid is None:  # 参数缺失
            return Response({"info":"物流运单号为空了"})
        if not company_code:
            return Response({"info":"物流公司code未获得"})
        if not packetid.isdigit():
            return Response({"info":"物流单号有误,包含非数字"})
        company_name = exp_map.reverse_map().get(company_code, None)
        if not company_name:
            company_name = kdn_wuliu_extra.get_logistics_name(company_code)
        out_sid = packetid
        if company_name:
            logistics_company = company_name
        else:
            return Response({"info":"尚且还不支持"+company_code+"的物流公司查询"})
        if not str(company_name).strip():
            return Response("暂无物流信息")
        company_code = kd100_exp_map.get(str(company_name).strip())
        # 如果我们数据库中记录已经是已签收状态,那么直接返回我们数据库中的物流信息
        tradewuliu = TradeWuliu.get_tradewuliu(packetid,company_code)
        if tradewuliu and tradewuliu.status == 3:
            show_data = kd100_wuliu.fomat_wuliu_data_from_db(tradewuliu)
            return Response(show_data)
        # 我们的记录不是已签收状态,那么直接在线同步查询,并异步更新我们的数据库
        search_result = kd100_wuliu.kd100_instant_query(company_code,packetid)
        if not json.loads(search_result).get("data"):
            return Response("暂无物流信息")
        # print tradewuliu.content
        # print json.dumps(json.loads(search_result).get("data"))
        if not tradewuliu or (tradewuliu and tradewuliu.content != json.dumps(json.loads(search_result).get("data"))):
            create_or_update_tradewuliu.delay(search_result)
        show_data = kd100_wuliu.format_wuliu_data(search_result)
        return Response(show_data)

    def create(self, request, *args, **kwargs):
        """创建本地物流存储"""
        return Response({"code":0})