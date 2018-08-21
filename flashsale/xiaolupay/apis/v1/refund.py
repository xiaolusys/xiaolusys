# coding:utf8
"""
参考: https://www.pingxx.com/api#refunds-退款
"""
from core.apis.models import DictObject
from ...services.refund import create_refund, retrieve_or_update_refund
from ...serializers import RefundSerializer

class Refund(DictObject):

    def get_charge_object(self):
        return self._retrieve_params['charge']

    def create(self,
            description='',
            amount=1,
            out_refund_no=None,
        ):
        charge = self.get_charge_object()
        refund_order = create_refund(charge, int(amount), description, out_refund_no)
        refund_data   = RefundSerializer(instance=refund_order).data
        return self.fresh_form_data(refund_data)

    def retrieve(self, refund_no):
        refund_order = retrieve_or_update_refund(refund_no)
        if not refund_order:
            return {}

        refund_data = RefundSerializer(instance=refund_order).data
        return self.fresh_form_data(refund_data)

    def all(self, **kwargs):
        return {}

