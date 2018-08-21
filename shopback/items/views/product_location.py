# coding=utf-8
__author__ = 'yan.huang'
from shopback.items.models import Product, ProductSku, ProductLocation
from shopback.archives.models import DepositeDistrict
from shopback.items.serializers import ProductLocationSerializer
from shopback.items.forms import ProductLocationForm
from django.shortcuts import get_object_or_404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework import viewsets, permissions, authentication
from rest_framework.decorators import detail_route, list_route


class ProductLocationViewSet(viewsets.ModelViewSet):
    """
    - 本类可以合并到ProductViewSet,但考虑到 1ProductViewSet过大 2库位和商品是多对多关系，可能从库位角度设置商品 故不进行合并。
    - 本类与ProductDistrictView有少许重复，ProductDistrictView设计不清应该重构。
    - `get`  获取商品关联库位
    - set_product_location: `post` 创建用户的投诉条目　　
        -  product     商品id
        -  district   　库位id
        -  sku  skuid
    """
    queryset = ProductLocation.objects.all()
    serializer_class = ProductLocationSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['POST'])
    def set_product_location(self, request):
        form = ProductLocationForm(request.POST)
        if not form.is_valid():
            return exceptions.ValidationError(form.error_message)
        product_id = form.cleaned_data['product']
        product = get_object_or_404(Product, id=product_id)
        district_no = form.cleaned_data['district']
        district = DepositeDistrict.get_by_name(district_no)
        if not district:
            return exceptions.ValidationError(u"库位不存在，请注意库位名格式,如1货区1货架1货位1=1-1")
        res = ProductLocation.set_product_district(product, district)
        return Response([i.id for i in res])
