# -*- coding:utf-8 -*-
from models import CashOut, CarryLog, XiaoluMama, NinePicAdver
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
        fields = ('xlmm', 'value', 'value_money', 'status', 'created')


class CarryLogSerializer(serializers.ModelSerializer):
    carry_date = serializers.DateTimeField(format="%y-%m-%d")

    class Meta:
        model = CarryLog
        fields = ('xlmm', 'order_num', 'buyer_nick', 'value', 'value_money', 'log_type',
                  'log_type_name', 'carry_type', 'carry_type_name', 'status_name', 'carry_date')


class NinePicAdverSerializer(serializers.ModelSerializer):
    # start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    cate_gory_display = serializers.CharField(source='get_cate_gory_display', read_only=True)

    class Meta:
        model = NinePicAdver
        fields = (
            "id",
            "auther",
            "title",
            "description",
            "cate_gory",
            "pic_arry",
            "start_time",
            "turns_num",
            "is_pushed",
            "detail_modelids",
            "cate_gory_display")
