# coding=utf-8
import json
import urllib, urllib2
from rest_framework import permissions
from rest_framework import authentication
from rest_framework.response import Response

from common.auth import WeAppAuthentication
from shopback.trades.models import TradeWuliu
from shopback.items.models import Product
import datetime
from . import serializers
from flashsale.restpro.tasks import SaveWuliu_only, SaveWuliu_by_packetid, get_third_apidata, get_third_apidata_by_packetid,get_third_apidata_by_packetid_return,create_or_update_tradewuliu
from rest_framework import viewsets
from rest_framework import renderers
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer, SaleTrade
from rest_framework.decorators import list_route
from shopback import paramconfig as pacg
from rest_framework.views import APIView
from rest_framework.response import Response
import logging
import  json
import datetime
from flashsale.restpro import kdn_wuliu_extra
from shopback.trades.models import TradeWuliu
from flashsale.restpro import exp_map
from flashsale.restpro import wuliu_choice,kd100_wuliu
from shopback.logistics.models import LogisticsCompany
logger = logging.getLogger(__name__)

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

class WuliuViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/get_wuliu_by_tid : 由tid获取物流信息
    """
    queryset = TradeWuliu.objects.all()
    serializer_class = serializers.TradeWuliuSerializer
    # authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    gap_time = 7200  # 查询间隔时间

    @list_route(methods=["get"])
    def get_wuliu_by_packetid(self, request):
        content = request.GET
        packetid = content.get("packetid", None)
        company_code = content.get("company_code", None)
        if packetid is None:  # 参数缺失
            return Response({"info":"物流运单号为空了"})
        if not company_code:
            return Response({"info":"物流公司code未获得"})
        if not packetid.isdigit():
            return Response({"info":"物流单号有误,包含非数字"})
        packetid = str(packetid)
        company_code = str(company_code).strip()
        if company_code not in kd100_exp_map.values():
            kd100_code = LogisticsCompany.objects.filter(code=company_code).first()
            company_code = kd100_code.kd100_express_key
        # 如果我们数据库中记录已经是已签收状态,那么直接返回我们数据库中的物流信息
        tradewuliu = TradeWuliu.get_tradewuliu(packetid)
        if tradewuliu and tradewuliu.status == 3:
            kd100_wuliu.confirm_get_by_state(tradewuliu.out_sid,tradewuliu.status)
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

    @list_route(methods=["post"])
    def push_wuliu_data(self,request):
        content = request.POST
        param = content.get("param")
        print content.get("param"),type(content.get("param"))
        param = json.loads(param)
        print param["status"]
        mointor_status = param.get("status")
        message = param.get("message")
        com = param.get("comOld")
        nu = param.get("nu")
        lastResult = param.get("lastResult")
        lastResult = json.dumps(lastResult)
        print lastResult,type(lastResult)
        out_sid = json.loads(lastResult).get("nu")
        status = json.loads(lastResult).get("state")
        TradeWuliu.create_or_update_tradewuliu(lastResult)
        # if out_sid and status and status == 3:
        #     kd100_wuliu.confirm_get_by_state(out_sid, status)
        logger.warn({'action': "kd100", 'info': "push_wuliu_data:" + str(out_sid)})
        return Response({"result":"true","returnCode":"200","message":u"成功"})







