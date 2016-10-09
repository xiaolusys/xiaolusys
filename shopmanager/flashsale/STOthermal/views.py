# -*- coding:utf-8 -*-

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets,authentication,permissions
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.decorators import detail_route,list_route
import STOthermal_extra
import constant_extra
import json
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
        cancel_exp_number = STOthermal_extra.cancel_exp_number(cp_code=cp_code,waybill_code=waybill_code)
        if cancel_exp_number:
            STOThermal.objects.filter(waybill_code = waybill_code).delete()
            return Response("运单号取消成功")
        else:
            return Response("运单号取消失败")

    @list_route(methods=['get'])
    def get_exp_number(self,request):
        a = {'param_waybill_cloud_print_apply_new_request': json.dumps(constant_extra.param_waybill_cloud_print_apply_new_request)}
        thermal_info = STOthermal_extra.get_exp_template(**a)
        if thermal_info:
            STOThermal.objects.create(print_data=thermal_info['print_data'],waybill_code=thermal_info['waybill_code'],operation_user=request.user)
            return Response(thermal_info)
        else:
            return Response("申请运单号失败")


