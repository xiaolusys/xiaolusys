# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers

from flashsale.pay.models import BankAccount
from flashsale.pay import constants

bank_img_map = dict([(bk['bank_name'], bk['bank_img']) for bk in constants.BANK_LIST])

class BankAccountSerializer(serializers.ModelSerializer):

    bank_img = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ( 'id', 'user', 'account_no', 'account_name', 'bank_name', 'bank_img', 'created', 'default')

    def get_bank_img(self, obj):
        return bank_img_map.get(obj.bank_name, '')
