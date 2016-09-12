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
import kdn_wuliu_extra
logger = logging.getLogger(__name__)
class KdnView(APIView):
    def get(self, request, *args, **kwargs):
        State = request.GET.get("Data",None)
        print State
        return Response(State)

    def post(self, request, *args, **kwargs):
        content = request.POST
        EBusinessID = content.get("EBusinessID", 1)
        PushTime = content.get("PushTime", 1)
        Count = content.get("Count", 1)
        Data = content.get('Data', 1)
        State = content.get("State", None)
        ShipperCode = content.get("ShipperCode",None)
        LogisticCode = content.get("LogisticCode",None)
        DataSign = content.get("DataSign", 1)
        RequestData = content.get("RequestData", 1)
        RequestType = content.get("RequestType", 1)
        # write_info = {"out_sid":LogisticCode,
        #               "logistics_company":ShipperCode,
        #               "status":State,
        #               "content":Data[0]["Traces"][0]}
        # print write_info
        # kdn_wuliu_extra.kdn_get_push(**write_info)
        logger.info({
            'action': 'push.kdn',
            "EBusinessID":EBusinessID,
            "PushTime":PushTime,
            "Count": Count,
            "Data": json.dumps(Data),
            "DataSign": DataSign,
            "State": State,
            "RequestData":json.dumps(RequestData),
            "RequestType": RequestType
        })
        return Response({"EBusinessID":EBusinessID,"PushTime":PushTime,"Count":Count,
                         "Data":Data,"DataSign":DataSign,"RequestData":RequestData,"RequestType":RequestType})
        # return Response({"Success":True,"EBusinessID":str(1264368),"UpdateTime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Reason":""})
