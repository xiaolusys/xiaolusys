# -*- coding:utf-8 -*-
from ..models.rank import WeekMamaTeamCarryTotal, WeekMamaCarryTotal
from rest_framework import serializers


class WeekMamaCarryTotalSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='total_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)
    mama_nick = serializers.SerializerMethodField()

    class Meta:
        model = WeekMamaCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')


    def get_mama_nick(self, obj):
        nick = obj.mama_nick
        return len(nick) > 5 and nick[0:5]+'...' or nick


class WeekMamaCarryTotalDurationSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='duration_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)
    total = serializers.IntegerField(source='duration_total', read_only=True)
    total_display = serializers.FloatField(source='duration_total_display', read_only=True)
    mama_nick = serializers.SerializerMethodField()

    class Meta:
        model = WeekMamaCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')

    def get_mama_nick(self, obj):
        nick = obj.mama_nick
        return len(nick) > 5 and nick[0:5] + '...' or nick


class WeekMamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='total_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)
    mama_nick = serializers.SerializerMethodField()

    class Meta:
        model = WeekMamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')

    def get_mama_nick(self, obj):
        nick = obj.mama_nick
        return len(nick) > 5 and nick[0:5] + '...' or nick


class WeekMamaTeamCarryTotalDurationSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(source='duration_rank', read_only=True)
    num = serializers.IntegerField(source='order_num', read_only=True)
    total = serializers.IntegerField(source='duration_total', read_only=True)
    total_display = serializers.FloatField(source='duration_total_display', read_only=True)
    mama_nick = serializers.SerializerMethodField()

    class Meta:
        model = WeekMamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'total', 'num', 'total_display', 'rank')

    def get_mama_nick(self, obj):
        nick = obj.mama_nick
        return len(nick) > 5 and nick[0:5] + '...' or nick
