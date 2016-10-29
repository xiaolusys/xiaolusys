# coding=utf-8
import datetime
import django_filters

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from flashsale.xiaolumm import serializers
from flashsale.xiaolumm.models.models_advertis import NinePicAdver
from shopback.items.models import Product
from supplychain.supplier.models import SaleProductManageDetail
from apis.v1.dailypush.ninepic import create_nine_pic_advertisement, \
    update_nine_pic_advertisement_by_id, delete_nine_pic_advertisement_by_id, get_nine_pic_descriptions_by_modelids


class NinepicFilter(filters.FilterSet):
    title = django_filters.CharFilter(name="title", lookup_type='contains')
    description = django_filters.CharFilter(name="description", lookup_type='contains')
    time_start = django_filters.DateFilter(name="start_time", lookup_type='gte')
    time_end = django_filters.DateFilter(name="start_time", lookup_type='lte')
    detail_modelids = django_filters.CharFilter(name="detail_modelids", lookup_type='contains')

    class Meta:
        model = NinePicAdver
        fields = ['id',
                  'sale_category_id',
                  'time_start',
                  'time_end',
                  'detail_modelids',
                  'title',
                  'description']


class NinePicAdverViewSet(viewsets.ModelViewSet):
    queryset = NinePicAdver.objects.all().order_by('-start_time')
    serializer_class = serializers.NinePicAdverSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('detail_modelids', 'auther', 'start_time', '=id')
    filter_class = NinepicFilter

    @list_route(methods=['get'])
    def get_promotion_product(self, request):
        date = request.REQUEST.get('date') or datetime.date.today()
        # 排期日期在未来三天的　需要推广的商品
        pms = SaleProductManageDetail.objects.filter(schedule_manage__sale_time=date,
                                                     today_use_status=SaleProductManageDetail.NORMAL,
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
        a = sorted(pms, key=lambda k: k['sale_product_id'], reverse=True)  # 按照选品id　排序
        return Response(a)

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        from supplychain.supplier.models import SaleCategory

        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL, is_parent=True)
        return Response({
            'is_pushed': [{'name': '稍后推送', 'value': False}, {'name': '不推送', 'value': True}],
            'categorys': categorys.values_list('id', 'name', 'parent_cid', 'is_parent', 'sort_order'),
        })

    @detail_route(methods=['get'])
    def get_descriptions_by_modelids(self, request, *args, **kwargs):
        modelids = kwargs.get('pk').split(',')
        print "modelids:", modelids
        res = get_nine_pic_descriptions_by_modelids(modelids=modelids)
        return Response(res)

    def create(self, request, *args, **kwargs):
        try:
            auther = request.user.username
            title = request.data.pop('title')
            start_time = datetime.datetime.strptime(request.data.pop('start_time'),
                                                    '%Y-%m-%d %H:%M:%S')
            n = create_nine_pic_advertisement(auther, title, start_time, **request.data)
        except Exception as e:
            raise exceptions.APIException(e.message)
        serializer = self.get_serializer(n)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        update_nine_pic_advertisement_by_id(int(kwargs.get('pk')), **request.data)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        delete_nine_pic_advertisement_by_id(int(kwargs.get('pk')))
        return Response(status=status.HTTP_204_NO_CONTENT)
