# -*- coding:utf-8 -*-

import json

from rest_framework import viewsets,authentication,permissions
from rest_framework.decorators import detail_route,list_route
from rest_framework.response import Response

import STOthermal_extra
import constant_extra
from models import STOThermal


class STOThermalSet(viewsets.ViewSet):
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['get'])
    def delivery_address(self, request):
        cp_code = request.GET.get('cp_code',None)
        address = STOthermal_extra.get_delivery_address(cp_code=cp_code)
        return Response(address)

    @detail_route(methods=['post'])
    def cancel_exp_number(self, request, pk):
        cp_code = request.POST.get('cp_code', None)
        waybill_code = request.POST.get('waybill_code', None)
        cancel_exp_number = STOthermal_extra.cancel_exp_number(cp_code=cp_code, waybill_code=waybill_code)
        if cancel_exp_number:
            STOThermal.objects.filter(waybill_code = waybill_code).delete()
            return Response("运单号取消成功")
        else:
            return Response("运单号取消失败")

    @list_route(methods=['get'])
    def get_exp_number(self,request):
        detail = request.GET.get('detail')
        province = request.GET.get('province')
        name = request.GET.get('name')
        mobile = request.GET.get('mobile')
        trade_id= request.GET.get('trade_id')
        print_info = json.dumps(constant_extra.param_waybill_cloud_print_apply_new_request)
        print_info = print_info.replace("wojia",detail)
        print_info = print_info.replace("shanghai",province)
        print_info = print_info.replace("denghui",name)
        print_info = print_info.replace("15800972458",mobile)
        print_info = print_info.replace("132112", trade_id)
        a = {'param_waybill_cloud_print_apply_new_request': print_info}
        thermal_info = STOthermal_extra.get_exp_template(**a)
        if thermal_info:
            sto = STOThermal.objects.filter(waybill_code=thermal_info['waybill_code'])
            if sto.first():
                sto.update(print_data=thermal_info['print_data'],operation_user=request.user)
            else:
                STOThermal.objects.create(print_data=thermal_info['print_data'],waybill_code=thermal_info['waybill_code'],operation_user=request.user)
            return Response(thermal_info)
        else:
            return Response("申请运单号失败")


