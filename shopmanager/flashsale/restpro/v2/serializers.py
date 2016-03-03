# coding=utf-8
from rest_framework import serializers
from flashsale.xiaolumm.models_fortune import MamaFortune


class MamaFortuneSerializer(serializers.ModelSerializer):
    cash = serializers.FloatField(source='cash_display', read_only=True)
    carry = serializers.FloatField(source='carry_display', read_only=True)

    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'mama_name', 'mam_level', 'cash', 'fans_num', 'invite_num', 'order_num', 'carry',
                  'active_value_num', 'today_visitor_num')
