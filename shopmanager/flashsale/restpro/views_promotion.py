# -*- coding:utf-8 -*-

from django.shortcuts import get_object_or_404

from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import viewsets 

from flashsale.pay.models import Customer
from flashsale.promotion.models import XLReferalRelationship

import logging
logger = logging.getLogger('django.request')

class InviteReletionshipView(viewsets.ViewSet):
    """ 用户活动邀请粉丝列表 """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        user     = request.user
        customer = get_object_or_404(Customer,user=user)
        relationships = XLReferalRelationship.objects.filter(referal_from_uid=customer.id)
        referal_uids  = [rf[0] for rf in relationships.values_list('referal_uid')]
        customers     = Customer.objects.filter(id__in=referal_uids,status=Customer.NORMAL)
        info_list     = customers.values_list('id','nick','thumbnail')
        
        return Response(info_list)



