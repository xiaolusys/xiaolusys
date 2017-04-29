# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import transaction, IntegrityError

from ....models import (
    OutwareSupplier,
    OutwareAccount,
    OutwareSku,
    OutwareInboundOrder,
    OutwareInboundSku,
    OutwareSkuStock,
)
from shopback.outware.fengchao import sdks

from .... import constants
from ....utils import action_decorator

import logging
logger = logging.getLogger(__name__)

@action_decorator(constants.ACTION_SUPPLIER_CREATE['code'])
def create_supplier(vendor_code, dict_obj):

    dict_obj.vendor_code = vendor_code
    ware_account = OutwareAccount.get_fengchao_account()
    try:
        ow_supplier = OutwareSupplier.objects.create(
            outware_account=ware_account,
            vendor_name=dict_obj.vendor_name,
            vendor_code=dict_obj.vendor_code,
            extras={'data': dict(dict_obj)},
            uni_key=OutwareSupplier.generate_unikey(ware_account.id, vendor_code),
        )
    except IntegrityError:
        ow_supplier = OutwareSupplier.objects.get(
            outware_account=ware_account,
            uni_key=OutwareSupplier.generate_unikey(ware_account.id, vendor_code),
        )

    if ow_supplier.is_pushed_ok:
        return {'success': True, 'object': ow_supplier, 'message': '供应商重复创建自动结束' }

    try:
        sdks.request_getway(dict(dict_obj), constants.ACTION_SUPPLIER_CREATE['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_supplier, 'message': str(exc)}

    return {'success': True, 'object': ow_supplier, 'message': '' }


@action_decorator(constants.ACTION_SKU_CREATE['code'])
def create_sku_and_supplier(sku_code, vendor_code, sku_type, declare_type, dict_obj):
    # 包含sku信息以及与供应商的关系

    ware_account = OutwareAccount.get_fengchao_account()
    ow_supplier = OutwareSupplier.objects.get(outware_account=ware_account, vendor_code=vendor_code)
    action_code = constants.ACTION_SKU_CREATE['code']
    is_batch_mgt  = dict_obj.get('is_batch_mgt', False)
    is_expire_mgt = dict_obj.get('is_xpire_mgt', False)
    is_vendor_mgt = dict_obj.get('vdr_flag', False)

    if not getattr(dict_obj, 'bar_code'):
        raise Exception(u"请传入商品条码(多条码请使用逗号分隔)")

    if is_expire_mgt and dict_obj.shelf_life <= 0:
        raise Exception(u"如启动有效期管理请输入正确的有效期天数")

    try:
        with transaction.atomic():
            # for solution of An error occurred in the current transaction.
            # You can't execute queries until the end of the 'atomic' block
            ow_sku = OutwareSku.objects.create(
                outware_supplier=ow_supplier,
                sku_code=sku_code,
                sku_type=sku_type,
                declare_type=declare_type,
                is_batch_mgt=is_batch_mgt,
                is_expire_mgt=is_expire_mgt,
                is_vendor_mgt=is_vendor_mgt,
                extras={'data': dict(dict_obj)},
                uni_key=OutwareSku.generate_unikey(ow_supplier.id, sku_code),
            )
            ow_skustock, state = OutwareSkuStock.objects.get_or_create(sku_code=sku_code)
    except IntegrityError:
        ow_sku = OutwareSku.objects.get(outware_supplier=ow_supplier, sku_code=sku_code)
        ow_skustock, state = OutwareSkuStock.objects.get_or_create(sku_code=sku_code)

        if ow_skustock.is_action_success(action_code):
            action_code = constants.ACTION_SKU_EDIT['code']

        ow_sku.sku_type = sku_type
        ow_sku.declare_type = declare_type
        # is_batch_mgt and is_expire_mgt, if start ,can't be canceled
        if not ow_sku.is_batch_mgt:
            ow_sku.is_batch_mgt =is_batch_mgt
        if not ow_sku.is_expire_mgt:
            ow_sku.is_expire_mgt = is_expire_mgt
        ow_sku.is_vendor_mgt = is_vendor_mgt
        ow_sku.extras['data'] = dict(dict_obj)
        ow_sku.save()

    # TODO创建sku, 是否推送成功消息保存到skustock记录上
    try:
        resp = sdks.request_getway(dict(dict_obj), action_code, ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_skustock, 'message': str(exc), 'action_code': action_code}

    if resp.get('sku_id'):
        ow_sku.set_ware_sku_code(resp.get('sku_id'))
        ow_sku.save()

    return {'success': True, 'object': ow_skustock, 'message': '', 'action_code': action_code}


@action_decorator(constants.ACTION_UNION_SKU_AND_SUPPLIER['code'])
def union_sku_and_supplier(ow_sku):
    # 创建sku与供应商关联
    ware_account = OutwareAccount.get_fengchao_account()
    ow_supplier  = ow_sku.outware_supplier
    try:
        sdks.request_getway(
            {
                'vendor_name': ow_supplier.vendor_name,
                'vendor_code': ow_supplier.vendor_code,
                'sku_code': ow_sku.sku_code,
                'vdr_provide_barcode': ow_sku.extras.get('vdr_provide_barcode','0')
            },
            constants.ACTION_UNION_SKU_AND_SUPPLIER['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_sku, 'message': str(exc)}
    # 确定sku还有供应商已关联
    ow_sku.finish_unioned()
    ow_sku.save()

    return {'success': True, 'object': ow_sku, 'message': ''}


@action_decorator(constants.ACTION_PO_CREATE['code'])
def create_inbound_order(inbound_code, vendor_code, dict_obj):
    """ 采购入仓单/销退单创建 """
    if not dict_obj.receiver_info or not dict_obj.order_items:
        return {'success': False, 'object': None, 'message': '缺少收货地址信息/或商品SKU信息'}

    ware_account = OutwareAccount.get_fengchao_account()

    order_type = dict_obj.order_type
    ow_supplier = OutwareSupplier.objects.get(outware_account=ware_account, vendor_code=vendor_code)
    with transaction.atomic():
        try:
            # 　TODO@TIPS, use atomic inner for fix django model create bug
            # referl: http://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
            with transaction.atomic():
                ow_inbound = OutwareInboundOrder.objects.create(
                    outware_supplier=ow_supplier,
                    inbound_code=inbound_code,
                    store_code=dict_obj.store_code,
                    order_type=order_type,
                    extras={'data': dict(dict_obj)},
                    uni_key=OutwareInboundOrder.generate_unikey(inbound_code, order_type),
                )
        except IntegrityError:
            ow_inbound = OutwareInboundOrder.objects.get(
                inbound_code=inbound_code,
                order_type=order_type
            )
            if not ow_inbound.is_reproducible:
                return {'success': True, 'object': ow_inbound, 'message': '订单不可重复推送，如果需要修改请先取消'}

            ow_inbound.extras['data'] = dict(dict_obj)
            ow_inbound.save()

        for sku_item in dict_obj.order_items:
            sku_code = sku_item.sku_id
            batch_no = sku_item.batch_code
            ow_sku = OutwareSku.objects.get(outware_supplier=ow_supplier, sku_code=sku_code)
            if ow_sku.is_batch_mgt_on and not batch_no:
                raise Exception(u'SKU商品已启用批次管理，请设置入仓商品的批次号')

            try:
                with transaction.atomic():
                    OutwareInboundSku.objects.create(
                        outware_inboind=ow_inbound,
                        sku_code=sku_code,
                        batch_no=batch_no,
                        push_qty=sku_item.quantity,
                        uni_key=OutwareInboundSku.generate_unikey(ow_inbound.id, sku_code, batch_no),
                    )
            except IntegrityError:
                pass

    # TODO@MERON 入仓单取消后重新创建是否更换inbound_code?
    try:
        sdks.request_getway(dict(dict_obj), constants.ACTION_PO_CREATE['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': ow_inbound, 'message': str(exc)}

    # 确认采购入仓单已接收
    ow_inbound.change_order_status(constants.RECEIVED)

    return {'success': True, 'object': ow_inbound, 'message': ''}



@action_decorator(constants.ACTION_PO_CANCEL['code'])
def cancel_inbound_order(inbound_code, vendor_code, order_type):
    """ 采购入仓单/销退单取消 """
    ware_account = OutwareAccount.get_fengchao_account()

    ow_supplier = OutwareSupplier.objects.get(outware_account=ware_account, vendor_code=vendor_code)
    ow_inbound = OutwareInboundOrder.objects.get(
        outware_supplier=ow_supplier,
        inbound_code=inbound_code,
        order_type=order_type,
    )

    if ow_inbound.is_action_success(constants.ACTION_PO_CREATE['code']):
        try:
            sdks.request_getway({'order_code': inbound_code}, constants.ACTION_PO_CANCEL['code'], ware_account)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            return {'success': False, 'object': ow_inbound, 'message': str(exc)}

    # 确认采购入仓单已接收
    ow_inbound.change_order_status(constants.CANCEL)

    return {'success': True, 'object': ow_inbound, 'message': ''}


def create_return_order(inbound_code, dict_obj):
    # 包含sku信息以及与供应商的关系
    pass



