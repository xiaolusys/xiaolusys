# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db import transaction
from django.db.models import Q

from ..models.refund import RefundOrder
from ..models.charge import ChargeOrder
from ..libs.alipay import AliPay, AlipayConf, AliPayException
from ..libs.wxpay import WXPay, WXPayConf

import logging
logger = logging.getLogger(__name__)

@transaction.atomic
def create_refund(charge, refund_amount, description, out_refund_no):

    refund_order = RefundOrder.objects.create(
        refund_no = out_refund_no or charge.order_no,
        amount=refund_amount,
        description=description,
        failure_code='',
        failure_msg='',
        charge_id=charge.id,
        charge_order_no=charge.order_no,
    )
    channel = charge.channel
    refund_success = False
    time_succeed   = None
    refund_amount  = 0
    transaction_no = ''
    if channel in (ChargeOrder.ALIPAY, ChargeOrder.ALIPAY_WAP):
        alipay = AliPay()
        resp = alipay.trade_refund(charge.order_no,
                                   refund_amount / AlipayConf.AMOUNT_SETTER,
                                   refund_reason=description,
                                   out_request_no=out_refund_no)
        refund_success = resp['code'] == '10000'
        refund_amount = refund_success and int(resp['refund_fee'] * AlipayConf.AMOUNT_SETTER) or 0
        if refund_success:
            time_succeed  = datetime.datetime.strptime(resp['gmt_refund_pay'],'%Y-%m-%d %H:%M:%S')


    elif channel in (ChargeOrder.WX, ChargeOrder.WX_PUB, ChargeOrder.WEAPP):
        if channel == ChargeOrder.WX:
            wx_config = WXPayConf.wx_configs()
        elif channel == ChargeOrder.WX_PUB:
            wx_config = WXPayConf.pub_configs()
        else:
            wx_config = WXPayConf.we_configs()

        wxpay = WXPay(**wx_config)
        resp = wxpay.refund({
            'out_trade_no': charge.order_no,
            'out_refund_no': out_refund_no,
            'total_fee': charge.amount,
            'refund_fee': refund_amount
        })
        refund_success = resp['return_code'] == 'SUCCESS' and resp['result_code'] == 'SUCCESS'
        refund_amount  = refund_success and int(resp['refund_fee']) or 0
        time_succeed   = datetime.datetime.now()
        transaction_no = resp.get('transaction_id', '')

    if refund_success:
        charge_order = ChargeOrder.objects.get(id=charge.id)
        charge_order.confirm_refund(refund_amount)

        refund_order.confirm_refunded(time_succeed, transaction_no=transaction_no)

    return refund_order

@transaction.atomic
def retrieve_or_update_refund(refund_no, notify_refund_info=None):

    filters = Q(refund_no=refund_no)
    if refund_no.isdigit():
        filters |= Q(id=refund_no)

    refund_order = RefundOrder.objects.filter(filters).first()
    if not refund_order:
        return None

    if not refund_order.status == RefundOrder.PENDING:
        return refund_order


    channel = refund_order.charge.channel
    refund_success = False
    refund_amount  = 0
    time_successed = datetime.datetime.now()
    transaction_no = ''

    if channel in (ChargeOrder.ALIPAY, ChargeOrder.ALIPAY_WAP):
        alipay = AliPay()
        try:
            resp = notify_refund_info or alipay.trade_fastpay_refund_query(refund_order.charge_order_no, refund_order.refund_no)
            refund_success = resp['code'] == '10000'
            refund_amount = refund_success and int(resp['refund_amount'] * AlipayConf.AMOUNT_SETTER) or 0
        except AliPayException, exc:
            logger.error('%s'%exc, exc_info=True)

    elif channel in (ChargeOrder.WX, ChargeOrder.WX_PUB, ChargeOrder.WEAPP):
        if channel == ChargeOrder.WX:
            wx_config = WXPayConf.wx_configs()
        elif channel == ChargeOrder.WX_PUB:
            wx_config = WXPayConf.pub_configs()
        else:
            wx_config = WXPayConf.we_configs()

        wxpay = WXPay(**wx_config)
        resp = notify_refund_info or wxpay.refundquery({
            'out_refund_no': refund_order.refund_no
        })

        refund_success = resp['return_code'] == 'SUCCESS' and resp['result_code'] == 'SUCCESS'
        transaction_no = resp.get('transaction_id', '')
        if refund_success:
            for i in range(int(resp['refund_count'])):
                refund_amount += int(resp['refund_fee_%s'%i])

    if refund_success:
        charge = ChargeOrder.objects.get(id=refund_order.charge.id)
        charge.confirm_refund(refund_amount)

        refund_order.confirm_refunded(time_successed, transaction_no=transaction_no)

    return refund_order
