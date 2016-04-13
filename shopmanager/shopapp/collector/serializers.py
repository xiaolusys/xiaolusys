from rest_framework import serializers
import decimal
import inspect
import types


class SearchSerializer(serializers.ModelSerializer):
    """ docstring for SearchResource ModelResource """

    fields = (('charts', 'ChartSerializer'), ('item_dict', None), ('skus', None))
    # exclude = ('url',)


class RankSerializer(serializers.ModelSerializer):
    """ docstring for SearchResource ModelResource """

    exclude = ('url',)


class ChartsSerializer(serializers.ModelSerializer):
    """ docstring for TradeResource ModelResource """

    fields = (('charts', 'ChartSerializer'), ('item_dict', None), ('skus', None))
    # exclude = ('url',)


class BaseResource(serializers.ModelSerializer):
    """ docstring for TradeResource ModelResource """

    # fields = (('charts','ChartSerializer'),('item_dict',None))
    exclude = ('url',)
