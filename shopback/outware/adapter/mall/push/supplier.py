# coding: utf8
from __future__ import absolute_import, unicode_literals

from core.apis import DictObject
from ....adapter.ware.pull import pms

def push_ware_supplier_by_mall_supplier(mall_supplier):

    vendor_code = mall_supplier.vendor_code
    if not vendor_code:
        raise Exception(u'供应商编码不能为空:vendor_name=%s'%mall_supplier.supplier_name)

    params = {
        'vendor_code': vendor_code,
        'vendor_name': mall_supplier.supplier_name,
        'province': mall_supplier.province(),
        'object': 'OutwareSupplier',
    }

    dict_params = DictObject().fresh_form_data(params)
    resp = pms.create_supplier(vendor_code, dict_params)
    return resp

