# coding: utf8
from __future__ import absolute_import, unicode_literals

from copy import deepcopy
from django.db import transaction, IntegrityError
from django.conf import settings
from shopback.outware.fengchao import sdks

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
def create_order(order_code, store_code, order_type, dict_obj):
    # TODO@MERON 2016.3.11 该版本目前只支持转发商城推送订单, 合单拆分后续改进
    ware_account = OutwareAccount.get_fengchao_account()

    if not dict_obj.receiver_info or not dict_obj.order_items:
        raise Exception('缺少收货地址信息/商品SKU信息:order_no=%s'%order_code)

    action_code = constants.ACTION_ORDER_CREATE['code']
    if order_type == constants.SOURCE_TYPE_CROSSBOADER['code']:
        action_code = constants.ACTION_CROSSORDER_CREATE['code']
        if not all([dict_obj.declare_type,
                   dict_obj.order_person_idname,
                   dict_obj.order_person_idcard]):
            raise Exception('跨境订单需要传入报关方式以及用户身份信息:order_no=%s'%order_code)
    else:
        dict_obj.order_type = order_type
    # format order_code
    order_code = dict_obj.order_number = OutwareOrder.format_order_code(
        order_code, prefix=ware_account.order_prefix)
    with transaction.atomic():
        try:
            #　TODO@TIPS, use atomic inner for fix django model create bug
            with transaction.atomic():
                ow_order = OutwareOrder.objects.create(
                    outware_account=ware_account,
                    store_code=store_code,
                    union_order_code=order_code,
                    order_type=order_type,
                    order_source=constants.ORDER_SALE['code'],
                    extras={'data': dict(dict_obj)},
                    uni_key=OutwareOrder.generate_unikey(ware_account.id, order_code, order_type),
                )
        except IntegrityError:
            ow_order = OutwareOrder.objects.get(
                outware_account=ware_account,
                union_order_code=order_code,
                order_type=order_type
            )
            if not ow_order.is_reproducible:
                return {'success': True, 'object': ow_order, 'message': '订单不可重复推送'}

            ow_order.extras['data'] = dict(dict_obj)
            ow_order.save()

        for sku_item in dict_obj.order_items:
            sku_order_code = sku_item.sku_order_code
            ow_sku = OutwareSku.objects.filter(sku_code=sku_item.sku_id).first()
            if not ow_sku:
                raise Exception('供应商商品规格信息未录入:sku_code=%s'%sku_item.sku_id)
            try:
                with transaction.atomic():
                    OutwareOrderSku.objects.create(
                        outware_account=ware_account,
                        union_order_code=order_code,
                        origin_skuorder_no=sku_order_code,
                        sku_code=sku_item.sku_id,
                        sku_qty=sku_item.quantity,
                        uni_key=OutwareOrderSku.generate_unikey(ware_account.id, sku_order_code),
                    )
            except IntegrityError:
                ow_ordersku = OutwareOrderSku.objects.get(
                    outware_account=ware_account,
                    origin_skuorder_no=sku_order_code,
                    sku_code=sku_item.sku_id
                )
                if not ow_ordersku.is_reproducible:
                    raise Exception('该SKU订单已存在，请先取消后重新创建:sku_order_code=%s' % sku_order_code)

                ow_ordersku.is_valid = True
                ow_ordersku.union_order_code = order_code
                ow_ordersku.sku_qty = sku_item.quantity
                ow_ordersku.save()

    # create fengchao order
    try:
        sdks.request_getway(dict(dict_obj), action_code, ware_account)
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

    ware_order_code = OutwareOrder.format_order_code(order_code, prefix=ware_account.order_prefix)
    ow_order = OutwareOrder.objects.get(union_order_code=ware_order_code)
    action_code = constants.ACTION_ORDER_CREATE['code']

    if ow_order.is_action_success(action_code):
        try:
            sdks.request_getway({
                'order_number': ware_order_code,
            }, constants.ACTION_ORDER_CANCEL['code'], ware_account)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            return {'success': False, 'object': ow_order, 'message': str(exc)}

    # 取消订单
    ow_order.change_order_status(constants.CANCEL)

    return {'success': True, 'object': ow_order, 'message': ''}










