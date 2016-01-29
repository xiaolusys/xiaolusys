# -*- coding:utf-8 -*-
import os
import re
import urllib
import time
import datetime

from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse

from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework.views import APIView

from flashsale.pay.models import Customer
from flashsale.promotion.models import XLReferalRelationship

import logging
logger = logging.getLogger('django.request')

class InviteReletionshipView(APIView):
    """ 用户活动邀请粉丝列表 """
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get(self, request, format=None):

        user     = request.user
        customer = get_object_or_404(Customer,user=request.user)
        
        relationships = XLReferalRelationship.objects.filter(referal_uid=customer.id)
        referal_uids  = [rf[0] for rf in relationships.values_list('referal_from_uid')]
        customers     = Customer.objects.filter(id__in=referal_uids,status=Customer.NORMAL)
        info_list     = customers.values_list(['id','nick','thumbnail'])
        
        return Response(info_list)



