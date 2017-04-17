# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys
import datetime
from flashsale.xiaolumm.models.models_fortune import CarryRecord

import logging
logger = logging.getLogger('celery.handler')

def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@app.task(serializer='pickle')
def task_awardcarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return
    
    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        # 1. 不能同时修改状态和金额
        if record.status != carry.status:
            if carry.status == CarryRecord.CONFIRMED:
                record.confirm()
            if carry.status == CarryRecord.CANCEL:
                record.cancel()
            return

        # 2. 只有预计收益可以修改金额
        if record.carry_num != carry.carry_num:
            if record.status == CarryRecord.PENDING:
                record.changePendingCarryAmount(carry.carry_num)
            return

        return

    if carry.carry_num > 0:
        CarryRecord.create(carry.mama_id, carry.carry_num, CarryRecord.CR_RECOMMEND, carry.carry_description,
                           uni_key=carry.uni_key, status=carry.status)


@app.task(serializer='pickle')
def task_ordercarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return

    from flashsale.xiaolumm.models import OrderCarry
    if carry.status == OrderCarry.STAGING:
        carry_record_status = CarryRecord.PENDING
    elif carry.status == OrderCarry.ESTIMATE:
        carry_record_status = CarryRecord.PENDING
    elif carry.status == OrderCarry.CONFIRM:
        carry_record_status = CarryRecord.CONFIRMED
    elif carry.status == OrderCarry.CANCEL:
        carry_record_status = CarryRecord.CANCEL

    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        if record.status != carry_record_status:
            from flashsale.pay.models.trade import SaleOrder
            from flashsale.pay.models.product import ModelProduct
            from flashsale.xiaolumm.models import XiaoluMama
            sale_order = SaleOrder.objects.filter(oid=carry.order_id).first()
            from shopback.items.models import Product
            products = Product.objects.filter(id=sale_order.item_id)
            product = products[0]
            model_product = product.get_product_model()
            from flashsale.pay.apis.v1.product import get_virtual_modelproduct_from_boutique_modelproduct
            coupon_mp = get_virtual_modelproduct_from_boutique_modelproduct(product.model_id)

            if carry_record_status == CarryRecord.CONFIRMED:
                record.confirm()
                # give elite score
                if model_product and coupon_mp and coupon_mp.products[0].elite_score > 0 and sale_order.payment > 0 and (model_product.is_boutique_product or model_product.product_type == ModelProduct.USUAL_TYPE):
                        from flashsale.coupon.apis.v1.transfer import create_present_elite_score
                        from flashsale.coupon.apis.v1.coupontemplate import get_coupon_template_by_id
                        upper_mama = XiaoluMama.objects.filter(id=carry.mama_id,
                                                               status=XiaoluMama.EFFECT,
                                                               charge_status=XiaoluMama.CHARGED).first()
                        template = get_coupon_template_by_id(id=374)
                        customer = upper_mama.get_mama_customer()
                        transfer_in = create_present_elite_score(customer, int(round(coupon_mp.products[0].elite_score * (sale_order.payment / sale_order.price))), template, None, carry.order_id)

            if carry_record_status == CarryRecord.CANCEL:
                record.cancel()
                # cancel elite score
                if model_product and product.elite_score > 0 and carry.carry_num > 0 and (model_product.is_boutique_product or model_product.product_type == ModelProduct.USUAL_TYPE):
                    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
                    upper_mama = XiaoluMama.objects.filter(id=carry.mama_id,
                                                           status=XiaoluMama.EFFECT,
                                                           charge_status=XiaoluMama.CHARGED).first()
                    customer = upper_mama.get_mama_customer()
                    uni_key_in = "elite_in-%s-%s" % (customer.id, carry.order_id)
                    cts = CouponTransferRecord.objects.filter(uni_key=uni_key_in).first()
                    if cts:
                        cts.transfer_status = CouponTransferRecord.CANCELED
                        cts.save()
        return


    CarryRecord.create(carry.mama_id, carry.carry_num, CarryRecord.CR_ORDER, carry.carry_description,
                       uni_key=carry.uni_key,status=carry_record_status)


@app.task(serializer='pickle')
def task_clickcarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return
    
    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        # 1. 不能同时修改状态和金额
        if record.status != carry.status:
            if carry.status == CarryRecord.CONFIRMED:
                record.confirm()
            if carry.status == CarryRecord.CANCEL:
                record.cancel()
            return

        # 2. 只有预计收益可以修改金额
        if record.carry_num != carry.total_value:
            if record.status == CarryRecord.PENDING:
                record.changePendingCarryAmount(carry.total_value)
            return

        return

    if carry.total_value > 0:
        CarryRecord.create(carry.mama_id, carry.total_value, CarryRecord.CR_CLICK, carry.carry_description,
                           uni_key=carry.uni_key, status=carry.status)
