# coding=utf-8
from rest_framework import serializers
from statistics.models import SaleStats


class StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleStats
        fields = ('id',
                  'parent_id',
                  'current_id',
                  'date_field',
                  'name',
                  'pic_path',
                  'num',
                  'payment',
                  'status',
                  'get_status_display',
                  'timely_type',
                  'get_timely_type_display',
                  'record_type',
                  'get_record_type_display')


class StatsAllNumSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleStats
        fields = ('id',
                  'parent_id',
                  'current_id',
                  'date_field',
                  'name',
                  'pic_path',
                  'num',
                  'payment',
                  'status',
                  'get_status_display',
                  'timely_type',
                  'get_timely_type_display',
                  'record_type',
                  'get_record_type_display',
                  "paid_num",
                  'cancel_num',
                  'out_stock_num',
                  'return_goods_num')