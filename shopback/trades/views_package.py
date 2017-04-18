# coding=utf-8
import json
from rest_framework import generics, permissions, renderers, viewsets, status as rest_status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseBadRequest
from shopback.trades.models import PackageOrder, PackageSkuItem
from shopback.trades.serializers import PackageOrderSerializer
from flashsale.restpro.v2.serializers.packageskuitem_serializers import PackageSkuItemSerializer
from shopback.trades.forms import PackageOrderEditForm, PackageOrderWareByForm, PackageOrderNoteForm, PackageOrderLogisticsCompanyForm
from shopback.items.models import ProductSku
from shopback.logistics.models import LogisticsCompany
from shopback.trades.serializers import LogisticsCompanySerializer
from rest_framework import filters
from shopback.trades.constants import PO_STATUS


class PackageSkuItemViewSet(viewsets.ModelViewSet):
    queryset = PackageSkuItem.objects.all()
    serializer_class = PackageSkuItemSerializer
    renderer_classes = (renderers.JSONRenderer,)
    filter_fields = ('package_order_pid',)


class PackageOrderViewSet(viewsets.ModelViewSet):
    """
    api : trades/package_order
    """
    queryset = PackageOrder.objects.all()
    serializer_class = PackageOrderSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filter_fields = ('pid', 'out_sid', 'sys_status','ware_by')
    search_fields = ('pid', 'out_sid', 'receiver_mobile')
    ordering = ('pid',)

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        logistics_company = LogisticsCompany.objects.filter(name__in=["韵达快递","邮政小包"])
        return Response({
            'ware_by': PackageOrder.WARE_CHOICES,
            'sys_status': PO_STATUS.CHOICES,
            'logistics_company': [[i.id,i.name] for i in logistics_company]
        })
    @list_route(methods=['get'])
    def new(self, request, format='html'):
        package = PackageOrder()
        logistics_companys = LogisticsCompany.objects.filter(type=1)
        logistics_companys = LogisticsCompanySerializer(logistics_companys, many=True).data
        return Response({'package': package, 'logistics_companys': logistics_companys},
                        template_name="trades/package_by_hand.html")

    @list_route(methods=['post'])
    def edit(self, request, pk, format='html'):
        form = PackageOrderEditForm(request)
        package = get_object_or_404(PackageOrder, pk=pk)
        package = PackageOrderSerializer(package).data
        return Response(package, template_name=u"finance/bill_detail.html")

    @list_route(methods=['post'])
    def new_create(self, request, *args, **kwargs):
        form = PackageOrderEditForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())
        psis = json.loads(request.POST.get('psis'))
        if not psis:
            return HttpResponseBadRequest(u'创建包裹必须填入sku')
        ware_by = form.cleaned_data['ware_by']
        receiver_mobile = form.cleaned_data['receiver_mobile']
        receiver_name = form.cleaned_data['receiver_name']
        receiver_state = form.cleaned_data['receiver_state']
        receiver_city = form.cleaned_data['receiver_city']
        receiver_district = form.cleaned_data['receiver_district']
        receiver_address = form.cleaned_data['receiver_address']
        user_address_id = form.cleaned_data['user_address_id']
        logistics_company = form.cleaned_data['logistics_company']
        psi_dict = {}
        for psi_line in psis:
            sku = ProductSku.objects.get(id=psi_line[0])
            psi_dict[sku.id] = [sku, int(psi_line[1])]
        package = PackageOrder.create_handle_package(
            ware_by, receiver_mobile, receiver_name, receiver_state, receiver_city,
                              receiver_district, receiver_address, logistics_company, user_address_id)
        for sku_id in psi_dict:
            psi = PackageSkuItem.create_by_hand(psi_dict[sku_id][0],
                                                psi_dict[sku_id][1],
                                                package.pid,
                                                package.id,
                                                package.receiver_mobile,
                                                package.ware_by)
        serializer = self.get_serializer(package)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def change_wareby(self, request, *args, **kwargs):
        form = PackageOrderWareByForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())
        ware_by = form.cleaned_data['ware_by']
        pid = form.cleaned_data['pid']
        package = get_object_or_404(PackageOrder, pid=pid)
        package.ware_by = ware_by
        package.save()
        return Response({'status': 'success'})

    def retrieve(self, request, *args, **kwargs):
        package_order = self.get_object()
        package_order = self.get_serializer(package_order).data
        logistics_companys = LogisticsCompany.objects.filter(type=1)
        logistics_companys = LogisticsCompanySerializer(logistics_companys, many=True).data
        return Response({'package_order': package_order, 'logistics_companys': logistics_companys},
                        template_name="trades/package_order.html")

    @list_route(methods=['post'])
    def change_note(self, request, *args, **kwargs):
        form = PackageOrderNoteForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())
        note = form.cleaned_data['note']
        pid = form.cleaned_data['pid']
        package = get_object_or_404(PackageOrder, pid=pid)
        package.seller_memo = note
        package.save()
        return Response({'res': 'success'})

    @list_route(methods=['post'])
    def change_logistics_company(self, request, *args, **kwargs):
        form = PackageOrderLogisticsCompanyForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())
        logistics_company_id = form.cleaned_data['logistics_company_id']
        pid = form.cleaned_data['pid']
        package = get_object_or_404(PackageOrder, pid=pid)
        package.logistics_company_id = logistics_company_id
        package.save()
        return Response({'res': 'success'})

    @list_route(methods=['post'])
    def change_to_prepare(self, request, *args, **kwargs):
        pid = request.POST.get('pid') or request.data.get("pid")
        package = get_object_or_404(PackageOrder, pid=pid)
        if package.sys_status in [PackageOrder.WAIT_SCAN_WEIGHT_STATUS, PackageOrder.WAIT_CHECK_BARCODE_STATUS]:
            package.sys_status = PackageOrder.WAIT_PREPARE_SEND_STATUS
            package.save()
            return Response({'res': 'success'})
        else:
            return HttpResponseBadRequest(u"必须是待扫描或者待称重状态")


