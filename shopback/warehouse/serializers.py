# coding=utf-8
from rest_framework import serializers
from shopback.warehouse.models import ReceiptGoods
from shopback.logistics.models import LogisticsCompany


class ExpressCompanySerialize(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        exclude = ()


class ReceiptGoodsSerialize(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%y-%m-%d %H:%M:%S", required=False, read_only=True)
    modified = serializers.DateTimeField(format="%y-%m-%d %H:%M:%S", required=False, read_only=True)
    logistic_company_info = ExpressCompanySerialize(source='logistic_company', read_only=True)
    receipt_type_display = serializers.CharField(source='get_receipt_type_display', read_only=True)

    class Meta:
        model = ReceiptGoods
        exclude = ()

