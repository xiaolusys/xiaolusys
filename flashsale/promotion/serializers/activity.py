# coding=utf-8
from rest_framework import serializers
from ..models.activity import ActivityEntry, ActivityProduct


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityEntry


class ActivityProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityProduct
        fields = (
            'id',
            'activity',
            'product_id',
            'model_id',
            'product_name',
            'product_img',
            'location_id',
            'pic_type',
            'get_pic_type_display',
            'jump_url',
        )
