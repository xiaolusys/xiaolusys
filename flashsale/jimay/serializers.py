# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers
from .models import JimayAgentOrder, JimayAgent
from flashsale.pay.models import UserAddress

class CustomAddressField(serializers.Field):
    def get_queryset(self):
        return UserAddress.objects.all()

    def to_representation(self, instance):
        if not instance:
            return {}
        address = instance
        moblile = address.receiver_mobile
        return {
            'id': address.id,
            'receiver_name': address.receiver_name,
            'full_address': address.full_address_string,
            'receiver_mobile': moblile and '%s****%s' % (moblile[0:3], moblile[7:]) or '',
        }

    def to_internal_value(self, data):
        return UserAddress.objects.filter(id=data).first()

class JimayAgentSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(source='buyer.thumbnail', read_only=True)
    class Meta:
        model = JimayAgent
        fields = ('id', 'nick', 'name', 'thumbnail', 'mobile', 'level', 'created')



class JimayAgentOrderSerializer(serializers.ModelSerializer):

    address = CustomAddressField()

    class Meta:
        model = JimayAgentOrder
        fields = ('id', 'order_no', 'buyer', 'title', 'pic_path', 'model_id', 'sku_id',
                  'num', 'payment', 'total_fee', 'address', 'status', 'pay_time', 'created')

    # def get_address(self, obj):
    #     if not obj.address:
    #         return {}
    #     address = obj.address
    #     moblile = address.receiver_mobile
    #     return {
    #         'id': address.id,
    #         'receiver_name': address.receiver_name,
    #         'full_address': address.full_address_string,
    #         'receiver_mobile': moblile and '%s****%s' % (moblile[0:3], moblile[7:]) or '',
    #     }
