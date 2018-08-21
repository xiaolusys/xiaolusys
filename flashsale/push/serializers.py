# coding: utf-8

from rest_framework import serializers

from . import models


class PushTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PushTopic
        fields = ('id', 'cat', 'device_id', 'platform', 'regid', 'ios_token', 'topic', 'update_time', 'status')
