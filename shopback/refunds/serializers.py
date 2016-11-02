# coding:utf-8
from rest_framework import serializers

from .models import RefundProduct, Refund
from shopback.trades.models import MergeTrade


# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')


class RefundProductSerializer(serializers.ModelSerializer):
    """ docstring for RefundProductResource """

    class Meta:
        model = RefundProduct
        #         fields = ('buyer_nick','buyer_mobile','buyer_phone','trade_id','out_sid','company','oid',
        #                   'outer_id','outer_sku_id','num','title','property','can_reuse','is_finish','created','modified','memo')
        exclude = ()


class RefundSerializer(serializers.ModelSerializer):
    """ docstring for RefundResource """

    class Meta:
        model = Refund
        # fields = (
        exclude = ()


class MergeTradeSerializer(serializers.ModelSerializer):
    """ docstring for RefundResource """

    class Meta:
        model = MergeTrade
        # fields = (
        exclude = ()
