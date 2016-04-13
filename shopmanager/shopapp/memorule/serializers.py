__author__ = "kaineng.fang"
from rest_framework import serializers


class TradeRuleSerializer(serializers.ModelSerializer):
    """ docstring for TradeRuleResource ModelResource """

    class Meta:
        exclude = ('url',)
