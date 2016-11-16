# coding=utf-8
from rest_framework import serializers
from models import *
from shopback.users.models import User


class MergeTradeSerializer(serializers.ModelSerializer):
    """ docstring for RefundResource """

    class Meta:
        model = MergeTrade
        #         fields =  ('id','tid','buyer_nick','type','shipping_type','user',
        #             'buyer_message','seller_memo','sys_memo','pay_time','modified'
        #             ,'created','consign_time','out_sid','status','sys_status',
        #             'receiver_name')
        exclude = ()


class LogisticsCompanySerializer(serializers.ModelSerializer):
    """ docstring for RefundResource """

    class Meta:
        model = LogisticsCompany
        # fields = (
        exclude = ()


class MergeOrderSerializer(serializers.ModelSerializer):
    ware_by = serializers.IntegerField(source='get_ware_by', read_only=True)

    class Meta:
        model = MergeOrder
        fields = ('id', 'oid', 'title', 'price', 'num', 'outer_id', 'outer_sku_id', 'payment',
                  'sku_properties_name', 'pic_path', 'created', 'pay_time', 'out_stock', 'is_merge',
                  'is_rule_match', 'is_reverse_order', 'gift_type', 'status', 'sys_status', 'ware_by')


# 2015-7-27  User

class UserSerializer(serializers.ModelSerializer):
    """ User  to json """

    class Meta:
        model = User
        exclude = ()
