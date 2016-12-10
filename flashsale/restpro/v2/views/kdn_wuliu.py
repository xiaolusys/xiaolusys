# -*- coding:utf-8 -*-

import logging
import  json
import datetime

from rest_framework import generics
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route

from flashsale.restpro.tasks import  get_third_apidata, get_third_apidata_by_packetid

logger = logging.getLogger(__name__)

class KdnViewSet(APIView):

    def get(self, request, *args, **kwargs):
        return Response(True)

    def post(self, request, *args, **kwargs):
        EBusinessID = request.data.get("EBusinessID", 1)
        PushTime = request.data.get("PushTime", 1)
        Count = request.data.get("Count", 1)
        Data = request.data.get("Data", 1)
        DataSign = request.data.get("DataSign", 1)
        RequestData = request.data.get("RequestData", 1)
        RequestType = request.data.get("RequestType", 1)
        logger.info({
            'action': 'push.kdn',
            "EBusinessID":EBusinessID,
            "PushTime":PushTime,
            "Count": Count,
            "Data": json.dumps(Data),
            "DataSign": DataSign,
            "RequestData":json.dumps(RequestData),
            "RequestType": RequestType
        })
        # return Response({"EBusinessID":EBusinessID,"PushTime":PushTime,"Count":Count,
        #                  "Data":Data,"DataSign":DataSign,"RequestData":RequestData,"RequestType":RequestType})
        return Response({"Success":True,"EBusinessID":str(1264368),"UpdateTime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Reason":""})


class LuntanPushViewSet(viewsets.ViewSet):

    @detail_route(methods=['post'])
    def at_push(self, request, pk):
        return Response(pk)



from shopback.trades.models import TradeWuliu
from shopback.items.models import Product
import datetime
from ..serializers import kdn_wuliu_serializer

from rest_framework import viewsets

from rest_framework.decorators import list_route
from shopback import paramconfig as pacg
from flashsale.restpro import exp_map
from flashsale.restpro import kdn_wuliu_extra

API_key = "b2983220-a56b-4e28-8ca0-f88225ee2e0b"
API_key_info = {"EBusinessID":"1264368","API_key":API_key,"requestType":"1008","DataType":"2"}
class WuliuViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/get_wuliu_by_tid : 由tid获取物流信息
    """
    queryset = TradeWuliu.objects.all()
    serializer_class = kdn_wuliu_serializer.TradeWuliuSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    gap_time = 7200  # 查询间隔时间


    @list_route(methods=['get'])
    def get_by_kdn(self, request):
        logistics_company = request.GET.get("logistics_company",None)
        out_sid = request.GET.get("out_sid",None)
        assert logistics_company is not None,'物流公司不能为空'
        assert out_sid is not None, '物流单号不能为空'
        tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid)
        if len(tradewuliu) == 1:
            return Response(kdn_wuliu_extra.format_content(tradewuliu.first().content))
        if len(tradewuliu) == 0:
            wuliu_info = {"expName":logistics_company,"expNo":out_sid}
            kdn_wuliu_extra.kdn_subscription(**wuliu_info)
            kdn_wuliu_extra.kdn_subscription_sub(**wuliu_info)
            return Response("物流信息暂未获得")
        if len(tradewuliu) > 1:
            for k,v in exp_map.iteritems():
                if k.startswith(logistics_company.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')):
                    logistics_company = k
                    break
            tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid,logistics_company=logistics_company)
            return Response(tradewuliu.first().content)

    @list_route(methods=['get'])
    def get_wuliu_by_tid(self, request):
        content = request.GET
        tid = content.get("tid", None)
        if tid is None:  # 参数缺失
            return Response({"code": 1})
        trade = kdn_wuliu_extra.get_trade(tid)
        message = kdn_wuliu_extra.get_status_message(trade)
        if message is not None:
            return Response(message)
        else:
            queryset = self.queryset.filter(tid=trade.tid).order_by(
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
                    res = kdn_wuliu_extra.packet_data(queryset)
                    return Response(res)
                else:  # 更新物流
                    get_third_apidata.delay(trade)
                    res = kdn_wuliu_extra.packet_data(queryset)
                    return Response(res)
            else:  # 更新物流
                get_third_apidata.delay(trade)
                res = kdn_wuliu_extra.packet_data(queryset)
                return Response(res)

    # @list_route(methods=['get'])
    # def get_wuliu_by_packetid(self, request):
    #     content = request.GET
    #     packetid = content.get("packetid", None)
    #     company_code = content.get("company_code", None)
    #     if packetid is None:  # 参数缺失
    #         return Response([])
    #
    #     queryset = self.queryset.filter(out_sid=packetid).order_by(
    #         "-time")  # 这里要按照物流信息时间倒序
    #     if queryset.exists():
    #         last_wuliu = queryset[0]
    #         last_time = last_wuliu.created  # 数据库中最新的记录时间
    #         now = datetime.datetime.now()  # 现在时间
    #         gap_time = (now - last_time).seconds
    #         if gap_time <= self.gap_time or (last_wuliu.status in (pacg.RP_ALREADY_SIGN_STATUS,
    #                                                                pacg.RP_REFUSE_SIGN_STATUS,
    #                                                                pacg.RP_CANNOT_SEND_STATUS,
    #                                                                pacg.RP_INVALID__STATUS,
    #                                                                pacg.RP_OVER_TIME_STATUS,
    #                                                                pacg.RP_FAILED_SIGN_STATUS)):
    #             # 属性定义的请求间隙 或者是物流信息是　已经签收了 疑难单　无效单　签收失败则不更新展示数据库中的数据
    #             res = kdn_wuliu_extra.packet_data(queryset)
    #             return Response(res)
    #         else:  # 更新物流
    #             get_third_apidata_by_packetid.delay(packetid, company_code)
    #             res = kdn_wuliu_extra.packet_data(queryset)
    #             return Response(res)
    #     else:  # 更新物流
    #         get_third_apidata_by_packetid.delay(packetid, company_code)
    #         res = kdn_wuliu_extra.packet_data(queryset)
    #         return Response(res)

    def create(self, request, *args, **kwargs):
        """ 创建本地物流信息存储 """
        return Response({"code": 0})
