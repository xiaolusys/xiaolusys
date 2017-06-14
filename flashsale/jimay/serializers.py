# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers

from .models import JimayAgentOrder

class JimayAgentOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = JimayAgentOrder
        fields = ('id', 'order_no', 'buyer', 'title', 'pic_path', 'model_id', 'sku_id',
                  'num', 'payment', 'total_fee', 'address', 'status', 'pay_time', 'created')

