# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import transaction

from outware.models import OutwareOrder, OutwarePackage, OutwarePackageSku, OutwareAccount, OutwareSkuStock, OutwareInboundSku
from outware.adapter.mall.pull import inbound, order
from .... import constants
from ....utils import action_decorator

import logging
logger = logging.getLogger(__name__)

@action_decorator(constants.ACTION_ORDER_SEND_FEEDBACK['code'])
@transaction.atomic
def update_outware_order_by_order_delivery(order_code, order_type, dict_obj):
    """ 包含入仓单/销退单到仓确认 """

    ware_account = OutwareAccount.get_fengchao_account()
    ow_package   = None
    for package in dict_obj.packages:
        # firstly, update outware package status and sku qty
        ow_package, state = OutwarePackage.objects.get_or_create(
            outware_account=ware_account,
            carrier_code=package.carrier_code,
            logistics_no=package.logistics_no,
            uni_key=OutwarePackage.generate_unikey(ware_account.id, package.logistics_no, package.carrier_code)
        )

        if not state:
            return

        ow_package.package_order_code = order_code
        ow_package.package_type = order_type
        ow_package.store_code   = package.store_code
        ow_package.save()

        for item in package.package_items:
            OutwarePackageSku.objects.create(
                package=ow_package,
                sku_code=item.sku_code,
                batch_no=item.batch_no,
                sku_qty=item.sku_qty,
                uni_key=OutwarePackageSku.generate_unikey(item.sku_code, item.batch_no, ow_package.id)
            )

        # secondly, update outware skustock qty
        for item in package.package_items:
            inbound_sku = OutwareInboundSku.objects.filter(batch_no=item.batch_no, sku_code=item.sku_code).first()
            if not inbound_sku:
                logger.error('未找到出库包裹商品对应的入库批次:batch_no=%s, sku_code=%s'%(item.batch_no, item.sku_code))
                continue
            skustock, state = OutwareSkuStock.objects.get_or_create(
                sku_code=inbound_sku.sku_code
            )
            # TODO 目前库存控制默认只支持所有的正品数量, 如果要处理次品问题需要对订单做处理
            skustock.minus_good_available_qty(item.sku_qty)
            skustock.save()
    try:
        # thirdly , update saletrade or return store status
        if order_type == constants.ORDER_SALE:
            inbound.update_return_store_by_outware_packages(order_code, dict_obj)
        else:
            order.update_saletrade_by_outware_packages(order_code, dict_obj)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_package, 'message': str(exc)}

    return {'success':True, 'object': ow_package, 'message':''}

@action_decorator(constants.ACTION_ORDER_STATE_FEEDBACK['code'])
@transaction.atomic
def update_outware_order_by_order_state_change(order_code, order_status):

    ow_order = OutwareOrder.objects.filter(order_code=order_code)
    success = ow_order.change_order_status(order_status)

    return {'success': True, 'object': ow_order,
            'message': not success and 'unchangeable status: %s(cur: %s)'%(
                dict(OutwareOrder.STATUS_CHOICES).get(order_code), ow_order.get_status_display()) or ''}

