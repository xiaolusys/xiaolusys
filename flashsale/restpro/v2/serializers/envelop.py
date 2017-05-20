# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers

from flashsale.pay.models import Envelop, BankAccount
from flashsale.pay import constants

bank_img_map = dict([(bk['bank_name'], bk['bank_img']) for bk in constants.BANK_LIST])

class BankAccountSerializer(serializers.ModelSerializer):

    bank_img = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ( 'id', 'user', 'account_no', 'account_name', 'bank_name', 'bank_img', 'created', 'default')

    def get_bank_img(self, obj):
        return bank_img_map.get(obj.bank_name, '')


class EnvelopSerializer(serializers.ModelSerializer):

    platform_name = serializers.SerializerMethodField()
    state         = serializers.SerializerMethodField()
    amount        = serializers.SerializerMethodField()
    service_fee   = serializers.SerializerMethodField()
    bank_card     = BankAccountSerializer(read_only=True)

    class Meta:
        model = Envelop
        fields = ( 'id', 'customer_id', 'amount', 'platform', 'platform_name', 'recipient', 'receiver',
                   'service_fee', 'state', 'fail_msg', 'bank_card', 'created', 'send_time', 'success_time')

    def get_platform_name(self, obj):
        return obj.get_platform_display()

    def get_state(self, obj):
        if obj.status == Envelop.WAIT_SEND:
            return 'apply'
        elif obj.status == Envelop.CONFIRM_SEND:
            if obj.send_status == Envelop.RECEIVED:
                return 'success'
            else:
                return 'pending'
        else:
            return 'pending'

    def get_amount(self, obj):
        return obj.amount * 0.01

    def get_service_fee(self, obj):
        if obj.platform == Envelop.SANDPAY:
            return 1
        return 0

