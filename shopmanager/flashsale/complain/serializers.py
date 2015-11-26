# -*- coding:utf-8 -*-
__author__ = 'timi06'
from rest_framework import serializers
from .models import Complain


class ComplainSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Complain

        fields = ('id', 'com_type', 'com_title', 'com_content', 'contact_way', 'created_time',
                  'custom_serviced', 'reply', 'reply_time')
