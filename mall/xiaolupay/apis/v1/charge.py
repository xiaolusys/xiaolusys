# coding:utf8
from __future__ import absolute_import, unicode_literals
"""
参考: https://www.pingxx.com/api#charges-支付
"""
from core.apis import DictObject

from ...services.charge import create_charge, retrieve_or_update_order
from ...serializers import ChargeSerializer

class Charge(DictObject):

    @staticmethod
    def create(
            order_no='',
            amount=0,
            channel='',
            subject='',
            body='',
            currency='cny',
            extra= {},
            app=None,  # noqe
            client_ip='127.0.0.1',  # noqe
            **kwargs
        ):
        charge_order = create_charge(
            order_no=order_no,
            amount=int(amount),
            channel=channel,
            currency='cny',
            subject=subject,
            body=body,
            extra=extra,
            client_ip=client_ip,
        )
        charge_data = ChargeSerializer(instance=charge_order).data
        print 'charge_data', charge_data
        return Charge().fresh_form_data(charge_data)

    @staticmethod
    def retrieve(ch_id):
        charge_order = retrieve_or_update_order(ch_id)
        if not charge_order:
            return {}

        charge_data = ChargeSerializer(instance=charge_order).data
        return Charge().fresh_form_data(charge_data)

    @staticmethod
    def all(limit=3, **kwargs):
        return {}

    @property
    def refunds(self):
        # TODO 退款处理逻辑
        from .refund import Refund
        return Refund(charge=self)


