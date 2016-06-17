# coding=utf-8
import datetime
import django_filters
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException
from flashsale.xiaolumm.models_advertis import NinePicAdver
from flashsale.xiaolumm import serializers
from supplychain.supplier.models import SaleProductManageDetail
from shopback.items.models import Product


class NinePicAdverViewSet(viewsets.ModelViewSet):
    queryset = NinePicAdver.objects.all().order_by('-start_time')
    serializer_class = serializers.NinePicAdverSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('detail_modelids', 'auther', 'start_time', '=id')

    @list_route(methods=['get'])
    def get_promotion_product(self, request):
        date = request.REQUEST.get('date') or datetime.date.today()
        # 排期日期在未来三天的　需要推广的商品
        pms = SaleProductManageDetail.objects.filter(schedule_manage__sale_time=date,
                                                     is_promotion=True).values("sale_product_id",
                                                                               "name",
                                                                               "pic_path")
        sale_product_ids = map(lambda x: x['sale_product_id'], pms)
        model_ids = Product.objects.filter(sale_product__in=sale_product_ids,
                                           status='normal').values('model_id',
                                                                   'sale_product',
                                                                   'sale_time')
        for p in pms:
            p_id = p['sale_product_id']
            x = filter(lambda x: x['sale_product'] == p_id, model_ids)  # 产品中过滤出来
            if len(x) > 0:
                p.update({'model_id': x[0]['model_id']})
                p.update({'sale_time': x[0]['sale_time']})
        return Response(pms)

    def create(self, request, *args, **kwargs):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        turns_num = self.queryset.filter(start_time__gte=today, start_time__lt=tomorrow).count() + 1
        request.data.update({"turns_num": turns_num})
        request.data.update({"auther": request.user.username})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        pic_arry = request.data.get("pic_arry") or None
        if pic_arry:
            pic_arry = pic_arry.split(',')
            try:
                n = self.queryset.get(id=kwargs.get('pk'))
            except Exception, exc:
                headers = self.handle_exception(exc=exc)
                return Response({}, status=404, headers=headers)
            if len(pic_arry) == n.cate_gory:  # 图片张数不匹配　返回错误
                request.data._mutable = True  # 开启可变
                request.data.update({"pic_arry": pic_arry})
                request.data._mutable = False  # 关闭可变
            else:
                return Response({}, status=400, headers=self.headers)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)