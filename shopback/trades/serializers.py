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


class PackageOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageOrder
        fields = ['pid', 'id', 'tid', 'action_type', 'ware_by', 'status', 'sys_status', 'sku_num', 'order_sku_num',
                  'ready_completion', 'seller_id', 'receiver_name', 'receiver_state', 'receiver_city',
                  'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone',
                  'user_address_id', 'buyer_id', 'buyer_nick', 'buyer_message', 'seller_memo', 'sys_memo', 'post_cost',
                  'out_sid', 'logistics_company', 'weight', 'is_qrcode', 'qrcode_msg', 'can_review', 'priority',
                  'purchaser', 'supplier_id', 'operator', 'scanner', 'weighter', 'is_locked', 'is_charged',
                  'is_picking_print', 'is_express_print', 'is_send_sms', 'has_refund', 'created', 'modified',
                  'can_send_time', 'send_time', 'weight_time', 'charge_time', 'remind_time', 'consign_time',
                  'reason_code', 'type']
