# -*- coding:utf-8 -*-
import os
import json
import datetime
import hashlib
import urlparse
import random
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.http import HttpResponse
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
import logging
import  json
import datetime
from flashsale.restpro import kdn_wuliu_extra
from shopback.trades.models import TradeWuliu
from flashsale.restpro import exp_map
logger = logging.getLogger(__name__)

class KdnView(APIView):
    def get(self, request, *args, **kwargs):
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
            return Response("物流信息暂未获得")
        if len(tradewuliu) > 1:
            for k,v in exp_map.iteritems():
                if k.startswith(logistics_company.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')):
                    logistics_company = k
                    break
            tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid,logistics_company=logistics_company)
            return Response(kdn_wuliu_extra.format_content(tradewuliu.first().content))

    def post(self, request, *args, **kwargs):
        content = request.POST
        DataSign = content.get("DataSign", None)
        RequestData = content.get("RequestData", None)
        RequestData = json.loads(RequestData)
        Count = RequestData["Count"]
        PushTime = RequestData["PushTime"]
        EBusinessID = RequestData["EBusinessID"]
        Success = RequestData["Data"][0]["Success"]
        LogisticCode = RequestData["Data"][0]["LogisticCode"]
        ShipperCode = RequestData["Data"][0]["ShipperCode"]
        State = RequestData["Data"][0]["State"]
        Traces = RequestData["Data"][0]["Traces"]
        print RequestData
        write_info = {
            'action': 'push.kdn',
            "EBusinessID":EBusinessID,
            "PushTime":PushTime,
            "Count": Count,
            "LogisticCode" : LogisticCode,
            "ShipperCode" : ShipperCode,
            "Traces": json.dumps(Traces),
            "DataSign": DataSign,
            "State": State
                    }
        kdn_wuliu_extra.kdn_get_push(**write_info)
        logger.info(write_info)
        # return Response({"EBusinessID":EBusinessID,"PushTime":PushTime,"Count":Count,
        #                  "Data":Data,"DataSign":DataSign,"RequestData":RequestData,"RequestType":RequestType})
        return Response({"Success":True,"EBusinessID":str(1264368),"UpdateTime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Reason":""})
