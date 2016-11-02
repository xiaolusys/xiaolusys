# coding=utf-8
from rest_framework import serializers
from flashsale.finance.models import Bill, BillRelation


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = (
        'type', 'status', 'creater', 'plan_amount', 'amount', 'pay_method', 'pay_taobao_link', 'receive_account',
        'receive_name', 'pay_account', 'transcation_no', 'attachment', 'delete_reason', 'note', 'supplier_id')


class BillRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillRelation
        fields = ('bill_id', 'content_type', 'object_id', 'type')
