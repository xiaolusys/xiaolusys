# -*- encoding:utf8 -*-
import urllib
from urlparse import urlparse, parse_qs
from django.http import HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.forms import model_to_dict

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.decorators import detail_route
from rest_framework.views import APIView

from flashsale.pay.models import Customer, District, UserAddress
from flashsale.pay.options import getDistrictTree

import logging

logger = logging.getLogger('django.request')

ADDRESS_PARAM_KEY_NAME = 'addrid'


class AddressList(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)

    template_name = "pay/maddresslist.html"

    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):

        customer = get_object_or_404(Customer, user=request.user)

        address_list = []
        addresses = UserAddress.normal_objects.filter(cus_uid=customer.id)
        for address in addresses:
            address_list.append(model_to_dict(address))

        origin_addrid = None
        origin_url = request.GET.get('origin_url', )
        if origin_url:
            o = urlparse(origin_url)
            query = parse_qs(o.query)

            if ADDRESS_PARAM_KEY_NAME in query:
                origin_addrid = query.pop(ADDRESS_PARAM_KEY_NAME)[0]

            origin_url = origin_url.split('?')[0] + '?' + urllib.urlencode(query, doseq=True)

        return Response({'results': address_list,
                         'origin_url': origin_url,
                         'origin_addrid': origin_addrid and int(origin_addrid)})

    def post(self, request, format=None):

        user = request.user
        content = request.POST

        customers = Customer.objects.normal_customer.filter(user=user)
        if customers.count() == 0:
            return HttpResponseForbidden('NOT EXIST')

        cus_uid = customers[0].id
        params = {}
        for k, v in content.iteritems():
            params[k] = v

        params['cus_uid'] = cus_uid
        params.pop('csrfmiddlewaretoken')
        params.pop('pk')

        addr_defualt = params.get('default', None)
        if addr_defualt == 'on':
            params['default'] = True
            UserAddress.normal_objects.filter(cus_uid=cus_uid).update(default=False)
        else:
            params['default'] = False

        uaddr = UserAddress.objects.create(**params)
        uaddr_dict = model_to_dict(uaddr)

        return Response(uaddr_dict)


class UserAddressDetail(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)

    template_name = "pay/address_block.html"

    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):

        pk = request.GET.get('pk')
        user_id = request.user.id
        if pk:
            uaddr = get_object_or_404(UserAddress, pk=pk, cus_uid=user_id)

            uaddr_dict = model_to_dict(uaddr)

            form_action = reverse('address_ins')
        else:
            uaddr_dict = {}

            form_action = reverse('address_list')

        if format and format.lower() != 'json':
            uaddr_dict.update({'form_action': form_action})

        prov_list = District.objects.filter(grade=District.FIRST_STAGE)
        uaddr_dict['province_list'] = prov_list

        return Response(uaddr_dict)

    def post(self, request, format=None):

        user_id = request.user.id
        content = request.POST
        pk = content.get('pk')

        uaddr = get_object_or_404(UserAddress, pk=pk, cus_uid=user_id)

        for k, v in content.iteritems():
            if k == 'default':
                v = v and True or False
            hasattr(uaddr, k) and setattr(uaddr, k, v)

        uaddr.save()

        return Response({'success': True})


class DistrictList(APIView):
    renderer_classes = (JSONRenderer,)

    # template_name = "pay/address_block.html"
    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        province = request.GET.get('p')

        district_tree = getDistrictTree(province=province)

        return Response([province, district_tree])
