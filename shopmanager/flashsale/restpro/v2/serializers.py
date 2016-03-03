# coding=utf-8
from rest_framework import serializers
from flashsale.xiaolumm.models_fortune import MamaFortune


class MamaFortuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaFortune
