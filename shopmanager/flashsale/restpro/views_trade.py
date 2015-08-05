#-*- coding:utf8 -*-
import datetime
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status

from flashsale.pay.models import SaleTrade,SaleOrder,Customer,ShoppingCart

from . import permissions as perms
from . import serializers 
from django.db.models import F
from django.forms.models import model_to_dict
from shopback.items.models import Product, ProductSku


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    ###特卖购物车REST API接口：
    - {prefix}/pk/delete_carts: 删除;
    - {prefix}/pk/plus_product_carts: 增加一件;
    - {prefix}/pk/minus_product_carts: 减少一件;
    - {prefix}/show_carts_num: 显示购物车数量;
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = serializers.ShoppingCartSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(buyer_id=customer.id)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = []
        for a in queryset:
            temp_dict = model_to_dict(a)
            pro = Product.objects.filter(id=a.item_id)
            temp_dict["std_sale_price"] = pro[0].std_sale_price if pro else 0
            data.append(temp_dict)
        return Response(data)

    def create(self, request, *args, **kwargs):
        data = request.data
        customer_user = Customer.objects.filter(user=request.user)
        if customer_user.count() == 0:
            return Response({"result": "0"}) #登录过期

        product_id = data.get("item_id", None)
        buyer_id = customer_user[0].id
        sku_id = data.get("sku_id", None)
        num = data.get("num", 0)
        sku = get_object_or_404(ProductSku, pk=sku_id)
        # lock_success = Product.objects.isQuantityLockable(sku, num) #限购功能
        # if product_id and buyer_id and sku_id and lock_success:
        if product_id and buyer_id and sku_id:
            shop_cart = ShoppingCart.objects.filter(item_id=product_id, buyer_id=buyer_id, sku_id=sku_id)
            if shop_cart.count() > 0:
                shop_cart_temp = shop_cart[0]
                shop_cart_temp.num += int(num) if num else 0
                shop_cart_temp.save()
                return Response({"result": "1"}) #购物车已经有了

            new_shop_cart = ShoppingCart()
            new_shop_cart.buyer_id = buyer_id
            for k, v in data.iteritems():
                if v:
                    hasattr(new_shop_cart, k) and setattr(new_shop_cart, k, v)
            new_shop_cart.buyer_nick = customer_user[0].nick if customer_user[0].nick else ""
            new_shop_cart.price = sku.agent_price
            new_shop_cart.total_fee = sku.agent_price * int(num) if sku.agent_price else 0
            new_shop_cart.sku_name = sku.properties_alias if len(sku.properties_alias) > 0 else sku.properties_name
            new_shop_cart.pic_path = sku.product.pic_path
            new_shop_cart.title = sku.product.name
            new_shop_cart.save()

            return Response({"result": "2"}) #购物车没有
        else:
            return Response({"result": "error"})  #未知错误

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def show_carts_num(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        count = 0
        for item in queryset:
            count += item.num
        return Response({"result": count})

    @detail_route(methods=['post', 'delete'])
    def delete_carts(self, request, pk=None):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data="OK", status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def plus_product_carts(self, request, pk=None):
        # cart_item = get_object_or_404(ShoppingCart, pk=pk)
        # sku = get_object_or_404(ProductSku, pk=cart_item.sku_id)
        # lock_success = Product.objects.isQuantityLockable(sku, cart_item.num+1)
        # if lock_success:
        update_status = ShoppingCart.objects.filter(id=pk).update(num=F('num') + 1)
        # else:
        #     return Response('0')
        return Response({"status": update_status})

    @detail_route(methods=['post'])
    def minus_product_carts(self, request, pk=None):
        temp_shop = ShoppingCart.objects.filter(id=pk)
        if temp_shop.count() == 0:
            return Response("error")
        if temp_shop[0].num == 1:
            return Response("can not minus")
        update_status = ShoppingCart.objects.filter(id=pk).update(num=F('num') - 1)
        return Response({"status": update_status})


class SaleOrderViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单明细REST API接口：
    - {path}/details[.formt]:获取订单及商品明细；
    """
    queryset = SaleOrder.objects.all()
    serializer_class = serializers.SaleOrderSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer)
    
    def get_queryset(self,request,pk=None):
        """
        获取订单明细QS
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
 
        queryset = self.queryset.filter(sale_trade=pk)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset
    
    def list(self, request, pk, *args, **kwargs):
        """ 
        获取用户订单列表 
        """
        queryset = self.filter_queryset(self.get_queryset(request,pk))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        customer = get_object_or_404(Customer,user=request.user)
        strade   = get_object_or_404(SaleTrade,id=pk,buyer_id=customer.id)
        strade_dict = serializers.SaleTradeSerializer(strade,context={'request': request}).data
        
        queryset = self.filter_queryset(self.get_queryset(request,pk))
        serializer = self.get_serializer(queryset, many=True)
        
        strade_dict['orders'] = serializer.data
        
        return Response(strade_dict)
    

class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单REST API接口：
    - {path}/wait_pay[.formt]:获取待支付订单；
    - {path}/wait_send[.formt]:获取待发货订单；
    """
    queryset = SaleTrade.objects.all()
    serializer_class = serializers.SaleTradeSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    paginate_by = 25
    page_query_param = 'page_size'
    max_paginate_by = 100
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id).order_by('-created')
    
    def list(self, request, *args, **kwargs):
        """ 获取用户订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def waitpay(self, request, *args, **kwargs):
        """ 获取用户待支付订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status=SaleTrade.WAIT_BUYER_PAY)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def waitsend(self, request, *args, **kwargs):
        """ 获取用户待发货订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @list_route(methods=['post'])
    def pingpp_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_destroy(self, instance):
        if instance.status != SaleTrade.WAIT_BUYER_PAY:
            raise Exception(u'订单不在待付款状态')
        instance.status = SaleTrade.TRADE_CLOSED_BY_SYS
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data={"ok": True})
