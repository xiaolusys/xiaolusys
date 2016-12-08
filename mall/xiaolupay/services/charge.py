# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db.models import Q
from django.db import transaction, IntegrityError

from ..apis.v1.conf import UnionPayConf, PINGPP_CREDENTIAL_TPL, PINGPP_CHARGE_TPL
from ..libs.alipay import AliPay, AlipayConf
from ..libs.wxpay import WXPay, WXPayUtil, WXPayConf
from ..libs.alipay.exceptions import AliPayAPIError
from ..libs.wxpay.exceptions import WxPayException
from ..models.charge import ChargeOrder
from ..apis.v1.exceptions import ChannelNotCompleteException
from ..utils import get_time_number

def create_credential(
        order_no='',
        amount=0,
        channel='',
        currency='cny',
        subject='',
        body='',
        extra={},
        client_ip=''
    ):
    credential = PINGPP_CREDENTIAL_TPL[channel].copy()
    if channel in (UnionPayConf.ALIPAY, UnionPayConf.ALIPAY_WAP):
        alipay = AliPay()
        order_amount = amount / AlipayConf.AMOUNT_SETTER
        if channel == UnionPayConf.ALIPAY:
            pay_info = alipay.create_trade_app_pay_url(order_no, order_amount, subject, body)
            credential = {
                "orderInfo": pay_info,
            }
        else:
            credential = alipay.trade_wap_pay(order_no, order_amount, subject, body)

    elif channel in (UnionPayConf.WX, UnionPayConf.WX_PUB):
        credential.update({
            "nonceStr": WXPayUtil.generate_nonce_str(),
        })
        if channel == UnionPayConf.WX:
            wx_config = WXPayConf.wx_configs()
            wxpay = WXPay(**wx_config)
            resp = wxpay.unifiedorder({
                'out_trade_no': order_no,
                'body': subject,
                'total_fee': amount,
                'notify_url': WXPayConf.NOTIFY_URL,
                'trade_type': 'APP',
                'nonce_str': credential['nonceStr'],
            })
            credential.update({
                "timeStamp": get_time_number(),
                "partnerId": wxpay.mch_id,
                "appId": wxpay.app_id,
                "prepayId": resp['prepay_id'],
            })
            sign_dict = {
                'appid': wxpay.app_id,
                'partnerid': wxpay.mch_id,
                'prepayid': resp['prepay_id'],
                'package': credential['packageValue'],
                'noncestr': credential['nonceStr'],
                'timestamp': credential['timeStamp'],
            }
            credential['sign'] = WXPayUtil.generate_signature(sign_dict, wxpay.key)
        else:
            wx_config = WXPayConf.pub_configs()
            wxpay = WXPay(**wx_config)
            resp = wxpay.unifiedorder({
                'out_trade_no': order_no,
                'body': subject,
                'total_fee': amount,
                'notify_url': WXPayConf.NOTIFY_URL,
                'trade_type': 'JSAPI',
                'openid': extra['open_id'],
                'nonce_str': credential['nonceStr'],
            })
            credential.update({
                "timeStamp": '%s' % get_time_number(),
                'package': 'prepay_id=%s' % resp['prepay_id']
            })
            sign_dict = {
                'appId': wxpay.app_id,
                'timeStamp': credential['timeStamp'],
                'nonceStr': credential['nonceStr'],
                'package': credential['package'],
                'signType': credential['signType'],
            }
            credential['paySign'] = WXPayUtil.generate_signature(sign_dict, wxpay.key)
    else:
        raise ChannelNotCompleteException('channel:%s is not completed!' % channel)

    return credential


def create_charge(
            order_no='',
            amount=0,
            channel='',
            currency='cny',
            subject='',
            body='',
            extra= {},
            client_ip='',
        ):
    time_now = datetime.datetime.now()
    with transaction.atomic():
        charge = ChargeOrder.objects.select_for_update().filter(order_no=order_no).first()
        if not charge:
            try:
                charge = ChargeOrder.objects.create(
                    order_no  = order_no,
                    channel   = channel,
                    client_ip = client_ip,
                    amount    = amount,
                    currency  = currency,
                    subject = subject,
                    body    = body,
                    extra   = extra,
                    time_expire = time_now + datetime.timedelta(seconds=UnionPayConf.TIME_EXPIRED)
                )
            except IntegrityError:
                charge = ChargeOrder.objects.filter(order_no=order_no).first()

        if charge.channel != channel:
            charge.channel = channel
            charge.save(update_fields=['channel'])

    charge.get_or_create_credential()
    return charge

@transaction.atomic
def retrieve_or_update_order(order_no, notify_order_info=None):

    filters = Q(order_no=order_no)
    if order_no.isdigit():
        filters |= Q(id=order_no)

    charge_order = ChargeOrder.objects.filter(filters).first()
    if not charge_order:
        return None

    if charge_order.paid:
        return charge_order

    channel = charge_order.channel
    paid_success = False
    time_paid    = datetime.datetime.now()
    transaction_no = ''
    fail_code    = ''
    fail_msg     = ''

    if channel in (UnionPayConf.ALIPAY, UnionPayConf.ALIPAY_WAP):
        alipay = AliPay()
        try:
            resp = notify_order_info or alipay.trade_query(charge_order.order_no)
            paid_success = resp['trade_status'] == AlipayConf.STATUS_SUCCESS
            transaction_no = resp.get('trade_no', '')
            if paid_success:
                time_paid  = resp.get('gmt_payment') or resp.get('send_pay_date') or None
                if time_paid:
                    time_paid = datetime.datetime.strptime(time_paid,'%Y-%m-%d %H:%M:%S')
        except AliPayAPIError, exc:
            fail_code = exc.fail_code
            fail_msg  = exc.fail_msg

    elif channel in (UnionPayConf.WX, UnionPayConf.WX_PUB):
        if channel == UnionPayConf.WX:
            wx_config = WXPayConf.wx_configs()
        else:
            wx_config = WXPayConf.pub_configs()

        wxpay = WXPay(**wx_config)
        resp = notify_order_info or wxpay.orderquery({
            'out_trade_no': charge_order.order_no
        })

        paid_success = resp['return_code'] == 'SUCCESS' and resp.get('time_end')
        fail_code    = not paid_success and resp['return_code'] or ''
        fail_msg     = not paid_success and resp['return_msg'] or ''
        transaction_no = resp.get('transaction_id', '')
        if paid_success:
            time_paid = datetime.datetime.strptime(resp['time_end'],'%Y%m%d%H%M%S') or None

    if paid_success:
        charge_order.confirm_paid(time_paid, transaction_no=transaction_no)
    else:
        charge_order.failure_paid(fail_code, fail_msg, transaction_no=transaction_no)

    return charge_order
