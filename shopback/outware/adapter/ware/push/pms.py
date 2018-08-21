# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import transaction

from ...mall.pull import inbound, order

from ....models import OutwareInboundOrder, OutwareInboundSku, OutwareSkuStock
from .... import constants
from ....utils import action_decorator

import logging
logger = logging.getLogger(__name__)

@action_decorator(constants.ACTION_PO_CREATE_FEEDBACK['code'])
@transaction.atomic
def update_outware_inbound_by_po_confirm(inbound_code, order_type, dict_obj):
    """ 包含入仓单/销退单到仓确认 """

    # firstly, update outware inbound status and sku qty
    ow_inbound = OutwareInboundOrder.objects.select_for_update().get(inbound_code=inbound_code, order_type=order_type)
    if ow_inbound.status not in (constants.NORMAL, constants.RECEIVED):
        raise Exception('外仓通知单对应内部外仓入仓单状态异常:%s'%inbound_code)

    if not ow_inbound.store_code:
        ow_inbound.store_code = dict_obj.store_code

    ow_inbound.status = constants.ARRIVED
    ow_inbound.save()

    for inbound_sku in dict_obj.inbound_skus:
        ow_sku, state = OutwareInboundSku.objects.get_or_create(
            outware_inboind=ow_inbound,
            sku_code=inbound_sku.sku_code,
            batch_no=inbound_sku.batch_no,
            uni_key=OutwareInboundSku.generate_unikey(ow_inbound.id, inbound_sku.sku_code, inbound_sku.batch_no),
        )
        ow_sku.pull_good_qty = inbound_sku.pull_good_qty
        ow_sku.pull_bad_qty  = inbound_sku.pull_bad_qty
        ow_sku.save()

    # secondly, update outware skustock qty
    for inbound_sku in dict_obj.inbound_skus:
        skustock, state = OutwareSkuStock.objects.get_or_create(
            sku_code=inbound_sku.sku_code
        )
        skustock.push_sku_good_qty += inbound_sku.pull_good_qty
        skustock.push_sku_bad_qty  += inbound_sku.pull_bad_qty

        if state:
            skustock.set_good_available_qty(inbound_sku.pull_good_qty)
            skustock.pull_bad_qty = inbound_sku.pull_bad_qty
        skustock.save()

    try:
        # thirdly , update forecast inbound or salerefund status
        if int(order_type) == constants.ORDER_PURCHASE['code']:
            inbound.update_forecast_inbound_by_outware_inbound(inbound_code, dict_obj)
        elif int(order_type) == constants.ORDER_REFUND['code']:
            order.update_refundproduct_by_outware_inbound(inbound_code, dict_obj)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_inbound, 'message': str(exc)}

    return {'success': True, 'object': ow_inbound, 'message': ''}