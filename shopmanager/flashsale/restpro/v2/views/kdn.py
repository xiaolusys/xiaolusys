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
from ...tasks import kdn_sub
from flashsale.restpro import wuliu_choice
from flashsale.restpro.tasks import kdn_get_push
# from flashsale.restpro.kdn_wuliu_extra import kdn_get_push

logger = logging.getLogger(__name__)


class KdnView(APIView):
    def get(self, request, *args, **kwargs):
        logistics_company = request.GET.get("logistics_company",None)
        out_sid = request.GET.get("out_sid",None)
        company_code = request.GET.get("company_code",None)
        if company_code:
            logistics_company = exp_map.reverse_map().get(company_code,None)
        assert logistics_company is not None,'物流公司不能为空'
        assert out_sid is not None, '物流单号不能为空'
        tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid)
        # status = tradewuliu.first().get_status_display()
        # format_exp_info = {
        #     "status": status,
        #     "name": tradewuliu.first().logistics_company,
        #     "errcode":tradewuliu.first().errcode,
        #     "id":"",
        #     "message":"",
        #     "content":tradewuliu.first().content,
        #     "out_sid":tradewuliu.first().out_sid
        # }
        result = wuliu_choice.result_choice[len(tradewuliu)](logistics_company,
                                                             out_sid,
                                                             tradewuliu.first())
        return Response(result)
        # if len(tradewuliu) == 1:
        #     return Response(kdn_wuliu_extra.format_content(**format_exp_info))
        # if len(tradewuliu) == 0:
        #     wuliu_info = {"expName":logistics_company,"expNo":out_sid}
        #     # kdn_wuliu_extra.kdn_subscription(**wuliu_info)
        #     kdn_sub.delay(rid=None,expName=logistics_company,expNo=out_sid)
        #     return Response("物流信息暂未获得")
        # if len(tradewuliu) > 1:
        #     for k,v in exp_map.iteritems():
        #         if k.startswith(logistics_company.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')):
        #             logistics_company = k
        #             break
        #     tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid,logistics_company=logistics_company)
        #     return Response(kdn_wuliu_extra.format_content(**format_exp_info))

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
        print ShipperCode
        write_info = {
            "out_sid": write_info['LogisticCode'],
            "logistics_company": exp_map.reverse_map().get(write_info['ShipperCode'], None),
            "status": write_info['State'],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": write_info['Traces']
        }
        print write_info['logistics_company']
        logger.info(write_info)
        try:
            kdn_get_push.delay(**write_info)
        except Exception, e:
            print Exception,e
            return Response({"Success": False, "EBusinessID": str(1264368),
                             "UpdateTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Reason": "数据库写入失败"})

        # return Response({"EBusinessID":EBusinessID,"PushTime":PushTime,"Count":Count,
        #                  "Data":Data,"DataSign":DataSign,"RequestData":RequestData,"RequestType":RequestType})
        return Response({"Success":True,"EBusinessID":str(1264368),"UpdateTime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Reason":""})
