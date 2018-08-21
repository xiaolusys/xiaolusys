# coding: utf8
from __future__ import absolute_import, unicode_literals

import logging
import datetime
from django.db import transaction, IntegrityError

from ..libs.sandpay import Sandpay, SandpayConf

from signals import signal_card_transfer, create_signal_message
from ..models.transfer import TransferOrder
from .. import conf

logger = logging.getLogger(__name__)

def create_transfer(
        order_code,
        channel,
        amount,
        desc,
        mch_id='',
        time_out=24 * 60 * 60,
        extras=None,
    ):
    # TODO@meron.2017.5.17 暂未集成微信转账
    uni_key  = TransferOrder.gen_uni_key(order_code)
    order_code = TransferOrder.format_order_code(order_code)
    with transaction.atomic():
        transfer = TransferOrder.objects.select_for_update().filter(uni_key=uni_key).first()
        if not transfer:
            try:
                transfer = TransferOrder.objects.create(
                    order_code=order_code,
                    channel=channel,
                    amount=amount,
                    desc=desc,
                    mch_id=mch_id,
                    time_out=time_out,
                    extras={ channel: extras or {}},
                    uni_key=uni_key
                )
            except IntegrityError:
                transfer = TransferOrder.objects.filter(uni_key=uni_key).first()

    # request for transfer
    transfer.start_transfer()
    return transfer

def start_transfer(transfer_order):
    channel = transfer_order.channel
    if channel == conf.SANDPAY:
        sandpay = Sandpay(
                SandpayConf.AC_MERCHANT,
                transfer_order.mch_id
            )
        data = transfer_order.sandpay_data

        resp = sandpay.agent_pay(**data)
        logger.debug({
            'action': 'sandpay_transfer_start',
            'action_time': datetime.datetime.now(),
            'order_code': transfer_order.order_code,
            'resp': resp
        })
        if resp['resultFlag'] == SandpayConf.RFLAG_SUCCESS:
            transfer_order.status = TransferOrder.SUCCESS
            transfer_order.success_time = transfer_order.success_time or datetime.datetime.now()
        elif resp['resultFlag'] == SandpayConf.RFLAG_FAIL:
            transfer_order.status = TransferOrder.FAIL

        transfer_order.return_code = resp.get('respCode')
        transfer_order.return_msg = resp.get('respDesc')
        transfer_order.tran_code  = resp.get('sandSerial')
        transfer_order.extras['response'] = resp
        transfer_order.save()

    if transfer_order.is_success():
        transfer_order.confirm_completed()

    if transfer_order.is_fail():
        transfer_order.confirm_fail()

    return transfer_order.is_success()

def retrieve_or_update_transfer(order_code):
    uni_key = TransferOrder.gen_uni_key(order_code)
    transfer_order = TransferOrder.objects.filter(uni_key=uni_key).first()
    if transfer_order.is_success() or transfer_order.is_fail():
        return transfer_order

    channel = transfer_order.channel
    if channel == conf.SANDPAY:
        sandpay = Sandpay(
            SandpayConf.AC_MERCHANT,
            transfer_order.mch_id
        )

        resp = sandpay.query_order(transfer_order.order_code, transfer_order.order_time)
        if resp['resultFlag'] == SandpayConf.RFLAG_SUCCESS:
            transfer_order.status = TransferOrder.SUCCESS
            transfer_order.success_time = transfer_order.success_time or datetime.datetime.now()
        elif resp['resultFlag'] == SandpayConf.RFLAG_FAIL:
            transfer_order.status = TransferOrder.FAIL

        transfer_order.return_code = resp.get('respCode')
        transfer_order.return_msg = resp.get('respDesc')
        transfer_order.tran_code = resp.get('sandSerial')
        transfer_order.extras['response'] = resp
        transfer_order.save()

    if transfer_order.is_success():
        transfer_order.confirm_completed()

    if transfer_order.is_fail():
        transfer_order.confirm_fail()

    return transfer_order