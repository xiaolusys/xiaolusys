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
logger = logging.getLogger(__name__)
class KdnViewSet(APIView):
    def get(self, request, *args, **kwargs):
        return Response(True)
    def post(self, request, *args, **kwargs):
        EBusinessID = request.POST.get("EBusinessID", 1)
        PushTime = request.POST.get("PushTime", 1)
        Count = request.POST.get("Count", 1)
        Data = request.POST.get("Data", 1)
        DataSign = request.POST.get("DataSign", 1)
        RequestData = request.POST.get("RequestData", 1)
        RequestType = request.POST.get("RequestType", 1)
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
