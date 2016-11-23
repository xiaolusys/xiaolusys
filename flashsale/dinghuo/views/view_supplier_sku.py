from __future__ import unicode_literals,absolute_import

from .. import supplier_sku
from django.http import HttpResponse
import json
from django.shortcuts import render_to_response

def get_supplier_sku(request,salesupplier_id):
    supplier_sku_data = supplier_sku.get_supplier_sku(salesupplier_id)
    return render_to_response('dinghuo/supplier_sku.html', {'supplier_sku': supplier_sku_data})
    return HttpResponse(json.dumps(supplier_sku_data), status=200,content_type='application/json')


