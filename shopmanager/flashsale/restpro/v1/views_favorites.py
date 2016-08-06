# encoding=utf8
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions

from flashsale.pay.models.favorites import Favorites
from flashsale.pay.models.product import ModelProduct
from flashsale.pay.models.user import Customer
from flashsale.pay.models.shoppingcart import ShoppingCart
from shopback.items.models import Product
from . import serializers


class FavoritesViewSet(viewsets.ModelViewSet):
    """
    ## GET /rest/v1/favorites 获取用户商品收藏列表

    ## POST /rest/v1/favorites 添加收藏
    ### params:
    - `model_id` modelproduct id

    ## DELETE /rest/v1/favorites 取消收藏
    ### params:
    - `model_id`
    """

    queryset = Favorites.objects.all()
    serializer_class = serializers.FavoritesSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)
        shelf_status = request.GET.get('shelf_status', None)

        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})  # 登录过期

        queryset = self.queryset.filter(customer_id=customer.id).order_by('-created')

        result = []
        if shelf_status:
            for qs in queryset:
                if qs.model.shelf_status == shelf_status:
                    result.append(qs)
        else:
            result = queryset

        queryset = self.paginate_queryset(result)
        serializers = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializers.data)

    def create(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)
        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})  # 登录过期

        model_id = request.data.get('model_id', None)
        if not model_id:
            return Response({"code": 1, "info": u"参数错误"})

        modelproduct = ModelProduct.objects.filter(id=model_id).first()
        if not modelproduct:
            return Response({"code": 1, "info": u"参数错误,没有该商品"})

        favorite = Favorites.objects.filter(customer_id=customer.id, model_id=model_id)
        if favorite.count() > 0:
            return Response({"code": 1, "info": u"添加失败，商品已经收藏"})

        head_imgs = modelproduct.head_imgs.splitlines()
        head_img = head_imgs[0] if head_imgs else ''

        favorite = Favorites()
        favorite.customer = customer
        favorite.model = modelproduct
        favorite.name = modelproduct.name
        favorite.head_img = head_img
        favorite.lowest_agent_price = modelproduct.lowest_agent_price
        favorite.lowest_std_sale_price = modelproduct.lowest_std_sale_price
        favorite.save()
        return Response({"code": 0, "info": u"添加成功"})

    def delete(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)
        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})

        model_id = request.data.get('model_id', None) or request.query_params.get('model_id')
        if not model_id:
            return Response({"code": 1, "info": u"参数错误"})

        Favorites.objects.filter(customer_id=customer.id, model_id=model_id).delete()
        return Response({"code": 0, "info": u"取消收藏成功"})
