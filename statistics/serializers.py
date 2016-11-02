# coding=utf-8
from rest_framework import serializers
from statistics.models import SaleStats, ModelStats


class StatsSerializer(serializers.ModelSerializer):
    obsolete_supplier = serializers.BooleanField(source='is_obsolete_supplier', read_only=True)

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
                  'obsolete_supplier')


class StatsAllNumSerializer(serializers.ModelSerializer):
    obsolete_supplier = serializers.BooleanField(source='is_obsolete_supplier', read_only=True)

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
                  'return_goods_num',
                  'no_pay_num',
                  'obsolete_supplier')


class ModelStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelStats
        fields = (
            'model_id',
            'sale_product',
            'schedule_manage_id',
            'upshelf_time',
            'offshelf_time',
            'category',
            'supplier',
            'model_name',
            'category_name',
            'pic_url',
            'supplier_name',
            'pay_num',
            'no_pay_num',
            'cancel_num',
            'out_stock_num',
            'return_good_num',
            'payment',
            'agent_price',
            'cost',
        )


class ModelStatsSimpleSerializer(serializers.ModelSerializer):
    return_good_rate = serializers.SerializerMethodField('calculate_return_good_rate', read_only=True)

    class Meta:
        model = ModelStats
        fields = (
            'model_id',
            'schedule_manage_id',
            'upshelf_time',
            'offshelf_time',
            'pay_num',
            'no_pay_num',
            'cancel_num',
            'out_stock_num',
            'return_good_num',
            'payment',
            'return_good_rate'
        )

    def calculate_return_good_rate(self, obj):
        """
        计算记录款式的退货率
        """
        t = obj.return_good_num + obj.pay_num
        return round(float(obj.return_good_num) / t, 4) if t > 0 else 0