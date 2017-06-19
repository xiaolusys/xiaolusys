# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import authentication
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import generics, mixins

from core.rest import exceptions

from flashsale.pay.models import Customer, UserAddress, ModelProduct
from flashsale.jimay.models import JimayAgent, JimayAgentOrder
from flashsale.jimay import serializers
from flashsale.jimay.tasks import task_generate_jimay_agent_certification
from shopback.items.models import Product, ProductSku


class JimayWeixinAgent(mixins.ListModelMixin,
                        viewsets.GenericViewSet):

    queryset = JimayAgent.objects.all()
    serializer_class = serializers.JimayAgentSerializer  # Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('该方法未实现')

    @list_route(methods=['get'])
    def relationship(self, request, *args, **kwargs):
        buyer = get_object_or_404(Customer, user=request.user)
        buyer_agent  = JimayAgent.objects.filter(mobile=buyer.mobile).first()
        if not buyer_agent:
            return Response({})

        resp = { 'id': buyer_agent.id, 'parent_agent': {} }
        parent_agent = JimayAgent.objects.filter(id=buyer_agent.parent_agent_id).first()
        sub_agents   = JimayAgent.objects.filter(parent_agent_id=buyer_agent.id)

        resp['sub_agents'] = serializers.JimayAgentSerializer(sub_agents, many=True).data
        if parent_agent:
            resp['parent_agent'] = serializers.JimayAgentSerializer(parent_agent).data

        return Response(resp)

    @list_route(methods=['get'])
    def certificate(self, request, *args, **kwargs):
        buyer = get_object_or_404(Customer, user=request.user)
        buyer_agent = JimayAgent.objects.filter(mobile=buyer.mobile).first()
        if not buyer_agent:
            return Response({})

        certification_url = buyer_agent.certification
        if not certification_url:
            task_result = task_generate_jimay_agent_certification(buyer_agent.id)
            certification_url = task_result.get()

        return Response({'certification': certification_url})



class JimayWeixinAgentOrder(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    queryset = JimayAgentOrder.objects.all()
    serializer_class = serializers.JimayAgentOrderSerializer  # Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )

    def get_agentorder_qs(self, request):
        buyer = Customer.objects.filter(user=request.user).first()
        return self.queryset.filter(buyer=buyer)

    def get_buyer_address(self, buyer, address_id):
        if not buyer or not address_id:
            return None
        return UserAddress.objects.filter(cus_uid=buyer.id, id=address_id).first()

    def list(self, request, *args, **kwargs):
        queryset = self.get_agentorder_qs(request)
        queryset = queryset.order_by('-created')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, *args, **kwargs):
        instance = self.get_agentorder_qs(request).filter(id=pk).first()
        if not instance:
            raise Http404('未找到该订单')
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data.dict()
        buyer = get_object_or_404(Customer, user=request.user)

        if not JimayAgentOrder.is_createable(buyer):
            return Response({'code': 1, 'info': '你有未完成订货单，如果长时间未处理请联系管理员'})

        data['buyer']  = buyer.id
        data['status'] = JimayAgentOrder.ST_CREATE
        buyer_address = self.get_buyer_address(buyer, data.get('address'))
        if not buyer_address:
            return Response({'code': 2, 'info': '请填写收货地址'})

        product_sku = ProductSku.objects.get(id=data['sku_id'])
        data['total_fee'] = int(int(data['num']) * product_sku.agent_price * 100)
        data['title']     = '%s/%s' % (product_sku.product.product_model.name, product_sku.name)
        data['pic_path']  = product_sku.product.pic_path

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'code': 0, 'info': '', 'order': serializer.data})

    @list_route(methods=['GET'])
    def pay_info(self, request, *args, **kwargs):
        buyer = get_object_or_404(Customer, user=request.user)
        product_sku   = ProductSku.objects.get(id=287874)
        model_product = product_sku.product.product_model
        return Response({
            'order_no': JimayAgentOrder.gen_unique_order_no(),
            'buyer': {
                'id': buyer.id,
                'nick': buyer.nick,
                'head_img': buyer.thumbnail,
            },
            'item': {
                'model_id': model_product.id,
                'title': model_product.name,
                'sku_name': product_sku.name,
                'pic_path': model_product.head_img(),
                'sku_id': product_sku.id,
                'num': 1,
                'agent_price': round(product_sku.agent_price, 2),
                'total_fee': round(product_sku.agent_price * 1, 2),
                'post_fee': 0
            }
        })