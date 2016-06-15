# coding=utf-8
import os, urlparse

from django.conf import settings
from django.forms import model_to_dict

from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import viewsets

from flashsale.pay.models_custom import BrandEntry, BrandProduct
from flashsale.pay.serializes import BrandProductSerializer


class PromotionGoodsViewSet(viewsets.ModelViewSet):
    queryset = BrandProduct.objects.all()
    serializer_class = BrandProductSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def get_goods_pics_by_promotionid(self, request):
        content = request.REQUEST
        promotion_id = content.get('promotion_id', None)
        act_pics = self.queryset.filter(id=promotion_id).order_by("location_id")
        if act_pics:
            serializer = self.get_serializer(act_pics, many=True)
            return Response(serializer.data)
        else:
            return Response([])

    def get_desc_pics_by_promotionid(self, request):
        content = request.REQUEST
        promotion_id = content.get('promotion_id', None)
        desc_pics = BrandEntry.filter(id=promotion_id)
        if desc_pics:
            return Response(desc_pics.extra_pics)
        else:
            return Response([])

    @list_route(methods=['post'])
    def save_pics(self, request):

        content = request.REQUEST
        arr = content.get("arr", None)
        act_id = content.get("promotion_id", None)
        data = eval(arr)  # json字符串转化

        brand = BrandEntry.objects.filter(id=act_id).first()
        # BrandProduct.objects.filter(brand=brand).delete()
        brand.brand_products.delete()
        brand.extra_pic = '[]'
        brand.save()

        extra_pic = []
        for da in data:
            # activity_id = int(da['activity_id'])
            pic_type = int(da['pic_type'])
            if pic_type == 3:
                model_id = int(da['model_id'])
                product_name = da['product_name']
                pic_path = da['pic_path']
                location_id = int(da['location_id'])
                pics = BrandProduct.objects.create(brand=brand,
                                                   model_id=model_id,
                                                   product_name=product_name,
                                                   product_img=pic_path,
                                                   location_id=location_id)

                pics.save()
            else:
                extra_pic.append(da)
        if extra_pic.length > 0:
            import json
            brand.extra_pic = json.dump(extra_pic)
            print brand.extra_pic
            brand.save()
        return Response({"code": 0, "info": ""})
