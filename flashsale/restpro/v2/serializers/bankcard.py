# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers
from rest_framework import validators

from flashsale.pay.models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ( 'id', 'user', 'account_no', 'account_name', 'bank_name', 'created', 'default')

