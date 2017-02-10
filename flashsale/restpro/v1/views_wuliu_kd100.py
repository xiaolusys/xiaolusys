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
        company_code = str(company_code)

        # 如果我们数据库中记录已经是已签收状态,那么直接返回我们数据库中的物流信息
        tradewuliu = TradeWuliu.get_tradewuliu(packetid,company_code)
        if tradewuliu and tradewuliu.status == 3:
            return Response(json.loads(tradewuliu.content))
        # 我们的记录不是已签收状态,那么直接在线同步查询,并异步更新我们的数据库
        serarch_result = kd100_wuliu.kd100_instant_query(company_code,packetid)
        serarch_result_dict = json.loads(serarch_result)
        if tradewuliu and tradewuliu.content != json.dumps(serarch_result_dict["data"]):
            create_or_update_tradewuliu.delay(serarch_result)
        return Response(serarch_result_dict)

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
        TradeWuliu.create_or_update_tradewuliu(lastResult)
        return Response({"result":"true","returnCode":"200","message":u"成功"})







