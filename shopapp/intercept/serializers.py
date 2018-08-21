__author__ = "kaineng.fang"
from rest_framework import serializers
from .models import InterceptTrade


class InterceptTradeSerializer(serializers.ModelSerializer):
    """ docstring for ProductList ModelResource """

    class Meta:
        model = InterceptTrade
        fields = ('success', 'redirect_url')
        exclude = ('url',)
