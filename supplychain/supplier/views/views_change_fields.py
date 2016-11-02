# coding=utf-8
from supplychain.supplier.models import SupplierZone, SaleSupplier
from django.views.generic import View
from django.http import HttpResponse
from common.modelutils import update_model_fields
from core.options import log_action, CHANGE
import json


class SupplierFieldsChange(View):
    def post(self, request):
        content = request.REQUEST
        supplier_id = content.get("supplier_id", None)
        zone_id = content.get("zone_id", None)
        supplier_type = content.get("supplier_type", None)
        sup = SaleSupplier.objects.get(id=supplier_id)
        if supplier_id and zone_id:  # 修改地区字段
            try:
                zone = SupplierZone.objects.get(id=zone_id)
                sup.supplier_zone = zone.id
                update_model_fields(sup, update_fields=['supplier_zone'])
                status = {"code": 0}
                log_action(request.user.id, sup, CHANGE, u'修改供应商片区为{0}'.format(zone.name))
            except SupplierZone.DoesNotExist:
                status = {"code": 3}
                return HttpResponse(json.dumps(status), content_type='application/json')
        elif supplier_id and supplier_type:  # 修改类型字段
            supplier_type = int(supplier_type)
            sup.supplier_type = supplier_type
            update_model_fields(sup, update_fields=['supplier_type'])
            log_action(request.user.id, sup, CHANGE,
                       u'修改供应商类型为{0}'.format(SaleSupplier.SUPPLIER_TYPE[supplier_type][1]))
            status = {"code": 0}
        else:
            status = {"code": 1}
        return HttpResponse(json.dumps(status), content_type='application/json')
