# coding=utf-8

from rest_framework import serializers

from supplychain.supplier.models import SaleCategory


class SaleCategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = SaleCategory
        fields = ('cid', 'parent_cid', 'name', 'cat_pic', 'grade', 'is_parent', 'sort_order')