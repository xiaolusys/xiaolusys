# coding:utf8

from ...services.wx_transfer import transfer, WeixinTransfersAPI
from ...services.transfer import create_transfer, retrieve_or_update_transfer

from core.apis.models import DictObject

class Transfer(DictObject):

    @staticmethod
    def create(
            order_code,
            channel,
            amount,
            desc,
            mch_id='',
            time_out=24 * 60 * 60,
            extras=None,
        ):
        """
        ###### sandpay:
        extras: {
            'productId': '',
            'accAttr': '',
            'tranTime': '',
            'accType': '',
            'currencyCode': '',
            'noticeUrl': '',
        }
        """
        transfer_order = create_transfer(
            order_code,
            channel,
            amount,
            desc,
            mch_id=mch_id,
            time_out=time_out,
            extras=extras,
        )
        api_dict = transfer_order.to_apidict()
        return Transfer().fresh_form_data(api_dict)

    @staticmethod
    def retrieve(order_code):
        transfer_order = retrieve_or_update_transfer(order_code)
        api_dict = transfer_order.to_apidict()
        return Transfer().fresh_form_data(api_dict)



