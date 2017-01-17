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
from shopback.trades.forms import PackageOrderEditForm


class PackageOrderViewSet(viewsets.ModelViewSet):
    queryset = PackageOrder.objects.all()
    serializer_class = PackageOrderSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)

    @list_route(methods=['get'])
    def new(self, request, format='html'):
        package = PackageOrder()
        package = PackageOrderSerializer(package).data
        return Response(package, template_name=u"trades/package_by_hand.html")

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
        psis = json.loads(form.cleaned_data['psis'])
        if not psis:
            return HttpResponseBadRequest(u'创建包裹必须填入sku')
        package = PackageOrder.create_handle_package(

        )
        for psi_dict in psis:
            psi = PackageSkuItem.create_by_hand(psi_dict['sku'],
                                                psi_dict['num'],
                                                package.package_order_pid,
                                                package.package_order_id,
                                                package.receiver_mobile,
                                                package.ware_by)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=rest_status.HTTP_201_CREATED, headers=headers)

