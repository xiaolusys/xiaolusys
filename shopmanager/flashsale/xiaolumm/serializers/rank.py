# -*- coding:utf-8 -*-
from ..models.rank import WeekMamaTeamCarryTotal, WeekMamaCarryTotal
from rest_framework import serializers


class WeekMamaCarryTotalSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='total_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)

    class Meta:
        model = WeekMamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')


class WeekMamaCarryTotalDurationSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='duration_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)

    class Meta:
        model = WeekMamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'duration_total', 'num', 'duration_total_display', 'rank')


class WeekMamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='total_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)

    class Meta:
        model = WeekMamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')


class WeekMamaTeamCarryTotalDurationSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='duration_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)

    class Meta:
        model = WeekMamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'duration_total', 'num', 'duration_total_display', 'rank')
