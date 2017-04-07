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
from shopback.trades.forms import PackageOrderEditForm, PackageOrderWareByForm, PackageOrderNoteForm, PackageOrderLogisticsCompanyForm
from shopback.items.models import ProductSku
from shopback.logistics.models import LogisticsCompany
from shopback.trades.serializers import LogisticsCompanySerializer
from shopback.trades.perms import perm_package_order



class PackageOrderCViewSet(viewsets.ModelViewSet):
    queryset = PackageOrder.objects.all()
    serializer_class = PackageOrderSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perm_package_order.IsOwnerGroup)
    renderer_classes = (renderers.JSONRenderer,)

    @detail_route(methods=["post"])
    def edit_sys_memo(self, request, pk):
        sys_memo = request.POST.get("sys_memo")
        pid = pk
        package_order = PackageOrder.objects.filter(pid=pid).update(sys_memo=sys_memo)
        return Response(True)

    @list_route(methods=["get"])
    def get_packageorder(self, request):
        p = PackageOrder.objects.filter()[1:10].values()
        return Response(list(p))


