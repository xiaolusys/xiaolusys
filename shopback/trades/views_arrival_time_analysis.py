# coding=utf-8
import json
from rest_framework import generics, permissions, renderers, viewsets, status as rest_status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404
from shopback.trades.models import PackageOrder, PackageSkuItem, TradeWuliu
from shopback.trades.serializers import PackageOrderSerializer
from shopback.trades.forms import PackageOrderEditForm
from rest_framework import  authentication
import datetime,copy
from django.http import HttpResponse
from django.shortcuts import render


class ArrivalTimeViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = PackageSkuItem.objects.all()

    # @list_route(methods=['post'])
    # def gen_by_supplier(self, request):
    #     supplier_id = int(request.POST.get('supplier_id') or 0)
    #     supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
    #     returngoods = ReturnGoods.generate_by_supplier(supplier.id, request.user.username)
    #     return Response('OK')

    @list_route(methods=['get'])
    def get_3day_delay(self,request):
        delay_day = request.GET.get('delay_day',3)
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        if start_time and end_time:
            start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d")
            end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d")

        deadline = (datetime.datetime.now() - datetime.timedelta(days=delay_day)).strftime("%Y-%m")
        deadline = datetime.datetime.strptime(deadline,"%Y-%m")
        delay_packageskuitem = []
        if start_time and end_time:
            delay_packageskuitem = PackageSkuItem.get_no_receive_psi_by_weight_time(start_time,min(end_time,datetime.datetime.now() - datetime.timedelta(days=delay_day),end_time))
        else:
            delay_packageskuitem = PackageSkuItem.get_no_receive_psi_by_weight_time(deadline,datetime.datetime.now() - datetime.timedelta(days=delay_day))
        print delay_packageskuitem
        return render(request, "wuliu_analysis/arrival_goods_analysis.html", {'delay_packageskuitem': delay_packageskuitem})

    @detail_route(methods=['post'])
    def set_sys_note(self, request, pk):
        sys_note = request.POST.get("sys_note")
        PackageSkuItem.set_sys_note(pk,sys_note)

    # @detail_route(methods=['get'])
    # def psi_has_pid(self, request, pk):
    #     content = request.POST
    #     returngoods_id = content.get("returngoods_id", None)
    #     return_good = ReturnGoods.objects.get(id=returngoods_id)
    #     rg_detail = return_good.rg_details.all()
    #     pid_count = 0
    #     for i in rg_detail:
    #         if i.get_psi() and i.get_psi().package_order_pid:
    #             pid_count = pid_count + 1
    #     if pid_count == len(rg_detail):
    #         info = {"status": True, "info": u"全部都已生成了packageOrder"}
    #     elif pid_count == 0:
    #         info = {"status": False, "info": u"这个退货单里面的记录并没有生成任何一个packageorder"}
    #     else:
    #         info = {"status": True, "info": u"这个退货单里面的记录有些有packageorder有些没有"}
    #     return HttpResponse(json.dumps(info), content_type="application/json", status=200)

    # @detail_route(methods=['get'])
    # def create_psi_by_rgdetail(self, request, pk):
    #     return Response(pk)
    #
    # @detail_route(methods=['post'])
    # def create_psi_by_rgdetail(self, request, pk):
    #     content = request.POST
    #     returngoods_id = pk
    #     return_goods = ReturnGoods.objects.get(id=returngoods_id)
    #     supplier_addr = return_goods.get_supplier_addr()
    #     if not supplier_addr:
    #         return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不存在,请填写供应商地址信息"}),
    #                             content_type="application/json",
    #                             status=200)
    #     elif not supplier_addr.is_complete():
    #         return HttpResponse(json.dumps({"status": False, "reason": "供应商信息不完整,请完善供应商地址信息"}),
    #                             content_type="application/json",
    #                             status=200)
    #     packages = return_goods.create_or_update_package()
    #     return HttpResponse(json.dumps({"status":True, "package_order": [package.id for package in packages]}),
    #                         content_type="application/json", status=200)