# -*- coding:utf-8 -*-

from rest_framework import serializers


# from .models import Category

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')

# class CategorySerializer(serializers.ModelSerializer):
#      
#     class Meta:
#     
#         model = Category
#         fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
#         fields = ('parent_cid' ,'is_parent' ) 


class TimeOrderStatSerializer(serializers.ModelSerializer):
    """ docstring for TradeResource ModelResource """

    class Meta:
        fields = ('df', 'dt', 'nicks', 'cat_by', 'type', 'xy', ('charts', 'ChartSerializer'))
        exlcude = ('url',)


class ChartsSerializer(serializers.ModelSerializer):
    """ docstring for TradeResource ModelResource """

    class Meta:
        fields = (('charts', 'ChartSerializer'), ('item_dict', None), ('skus', None))
        # exclude = ('url',)


class BaseSerializer(serializers.ModelSerializer):
    """ docstring for TradeResource ModelResource """

    class Meta:
        # fields = (('charts','ChartSerializer'),('item_dict',None))
        exclude = ('url',)
