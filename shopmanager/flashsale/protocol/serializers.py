# coding=utf-8
from rest_framework import serializers
from flashsale.protocol.models import APPFullPushMessge


class APPPushMessgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = APPFullPushMessge