# -*- coding:utf-8 -*-
from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('cid', 'parent_cid', 'is_parent', 'name', 'status', 'sort_order')
