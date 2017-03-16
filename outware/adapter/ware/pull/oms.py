# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import transaction
from outware.fengchao import sdks

from ....models import (
    OutwareSku,
    OutwareOrder,
    OutwareOrderSku,
    OutwareAccount,
    OutwareSupplier,
    OutwareInboundOrder,
    OutwareInboundSku,
)
from .... import constants
from ....utils import action_decorator

import logging
logger = logging.getLogger(__name__)

@action_decorator(constants.ACTION_ORDER_CREATE['code'])
def create_order(order_code, store_code, dict_obj):
    # TODO@MERON 2016.3.11 该版本目前只支持转发商城推送订单, 合单拆分后续改进
    ware_account = OutwareAccount.get_fengchao_account()

    if not dict_obj.receiver_info or not dict_obj.order_items:
        raise Exception('缺少收货地址信息/商品SKU信息:order_no=%s'%order_code)

    order_type = dict_obj.order_type
    with transaction.atomic():
        ow_order = OutwareOrder.objects.create(
            outware_account=ware_account,
            store_code=store_code,
            union_order_code=order_code,
            order_type=order_type,
            extras={'data': dict(dict_obj)},
            uni_key=OutwareOrder.generate_unikey(ware_account.id, order_code),
        )

        for sku_item in dict_obj.order_items:
            sku_order_code = sku_item.sku_order_code
            ow_sku = OutwareSku.objects.filter(sku_code=sku_item.sku_id).first()
            if not ow_sku:
                raise Exception('供应商商品规格信息未录入:sku_code=%s'%sku_item.sku_id)
            OutwareOrderSku.objects.create(
                outware_account=ware_account,
                union_order_code=order_code,
                origin_skuorder_no=sku_order_code,
                sku_code=sku_item.sku_id,
                sku_qty=sku_item.quantity,
                uni_key=OutwareOrderSku.generate_unikey(ware_account.id, sku_order_code),
            )

    try:
        sdks.request_getway(dict(dict_obj), constants.ACTION_ORDER_CREATE['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_order, 'message': str(exc)}

    # 设置为已接单
    ow_order.change_order_status(constants.RECEIVED)

    return {'success': True, 'object': ow_order, 'message': ''}


@action_decorator(constants.ACTION_ORDER_CANCEL['code'])
def cancel_order(order_code):
    # TODO@MERON 2016.3.11 该版本目前只支持转发商城推送订单, 合单拆分后续改进
    ware_account = OutwareAccount.get_fengchao_account()

    ow_order = OutwareOrder.objects.get(union_order_code=order_code)

    try:
        sdks.request_getway({
            'order_number': order_code,
        }, constants.ACTION_ORDER_CANCEL['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_order, 'message': str(exc)}

    # 取消订单
    ow_order.change_order_status(constants.CANCEL)

    return {'success': True, 'object': ow_order, 'message': ''}










