#-*- coding:utf-8 -*-
from models import CashOut, CarryLog, XiaoluMama
from rest_framework import serializers

class CashOutStatusField(serializers.Field):
    def to_representation(self, obj):
        for choice in CashOut.STATUS_CHOICES:
            if choice[0] == obj:
                return choice[1]
        return ""
    
    def to_internal_value(self, data):
        return data


class CashOutSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d")
    status = CashOutStatusField()
    class Meta:
        model = CashOut
        fields = ('xlmm', 'value','value_money', 'status', 'created')


class CarryLogSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d")
    class Meta:
        model = CarryLog
        fields = ('xlmm', 'order_num', 'buyer_nick', 'value', 'value_money',
                  'log_type_name','carry_type_name', 'status_name', 'created')
        
        


        
