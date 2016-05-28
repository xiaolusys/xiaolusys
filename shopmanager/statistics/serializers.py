# coding=utf-8
from rest_framework import serializers
from statistics.models import SaleStats


class StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleStats