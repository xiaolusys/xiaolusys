# coding: utf-8
from django.test import TestCase
from flashsale.pay.models.product import ModelProduct

from .mipush import (
    mipush_of_android,
)


class PushTestCase(TestCase):

    def test_push_product_to_customer(self):
        customer_id = 913405
        model_id = 1
        model = ModelProduct.objects.get(id=model_id)
        target_url = 'com.jimei.xlmm://app/v1/products?product_id=http://m.xiaolumeimei.com/mall/product/details/%s' % model_id
        msg = '您收藏的商品%s上架了，点击查看>>' % model.name
        mipush_of_android.push_to_account(customer_id, {'target_url': target_url}, description=msg)
