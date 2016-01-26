# coding=utf-8
import datetime
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from rest_framework import exceptions
from . import serializers
from flashsale.pay.models_shops import CustomerShops, CuShopPros
from flashsale.pay.models import Customer
from django.shortcuts import get_object_or_404
from shopback.items.models import Product
from django.forms import model_to_dict
from rest_framework.decorators import detail_route, list_route
from . import permissions as perms


class CustomerShopsViewSet(viewsets.ModelViewSet):
    """
    ### 特卖用户店铺接口
    - {prefix} 获取用户店铺的信息
    """
    queryset = CustomerShops.objects.all()
    serializer_class = serializers.CustomerShopsSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_shop(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        exceptions.APIException(u'方法不允许')

    def get_owner_shop(self, request):
        """ 用户个人店铺信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shops = self.queryset.filter(customer=customer.id)  # 获取店铺
        return shops


class CuShopProsViewSet(viewsets.ModelViewSet):
    """
    ### 特卖用户店铺产品接口  
    - {prefix} 获取用户店铺产品的信息  
        `id`: 产品id  
        `status`: 店铺产品状态　1　表示上架　0 表示没有上架  
        `name`: 产品名称  
    - {prefix}/add_pro_to_shop [method:post] 添加商品到店铺  
        `product`: 要添加的产品id  
        :return 0 添加成功  
                1 参数缺失  
                2 添加错误  
    - {prefix}/remove_pro_from_shop [method:post] 下架我的店铺商品  
        `product`: 要下架的产品id  
        :return 0 下架成功  
                1 参数缺失  
    """
    queryset = CuShopPros.objects.all()
    serializer_class = serializers.CuShopProsSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_shop_pros(self, request):
        """ 用户个人店铺产品信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shop = get_object_or_404(CustomerShops, customer=customer.id)  # 获取店铺
        shop_pros = self.queryset.filter(shop=shop.id)
        return shop_pros

    def list(self, request, *args, **kwargs):
        shop_pros = self.get_owner_shop_pros(request).filter(pro_status=CuShopPros.UP_SHELF)
        data = []
        for shop_pro in shop_pros:
            pro = Product.objects.get(id=shop_pro.product)  # 产品信息
            pro_dic = model_to_dict(pro, fields=['name', 'id'])
            pro_dic['status'] = shop_pro.pro_status
            data.append(pro_dic)
        return Response(data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('method no allowed')

    @list_route(methods=['post'])
    def add_pro_to_shop(self, request, *args, **kwargs):
        content = request.REQUEST
        product = content.get('product', None)
        if product is None:
            return Response({"code": 1})  # 参数缺失
        customer = get_object_or_404(Customer, user=request.user)
        pro = get_object_or_404(Product, id=int(product))
        shop, shop_state = CustomerShops.objects.get_or_create(customer=customer.id)
        shop_pros, pro_state = CuShopPros.objects.get_or_create(shop=shop.id, product=pro.id)
        if pro_state:  # 新建成功
            return Response({"code": 0})
        return Response({"code": 2})

    @list_route(methods=['post'])
    def remove_pro_from_shop(self, request):
        content = request.REQUEST
        product = content.get('product', None)
        if product is None:
            return Response({"code": 1})  # 参数缺失
        down_pro = self.get_owner_shop_pros(request).filter(product=product, pro_status=CuShopPros.UP_SHELF)
        down_pro.update(pro_status=CuShopPros.DOWN_SHELF)  # 更新我的店铺产品状态到下架
        return Response({"code": 0})

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    def perform_update(self, serializer):
        raise exceptions.APIException('method not allowed')
