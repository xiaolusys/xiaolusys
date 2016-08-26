# -*- coding:utf-8 -*-

from rest_framework import serializers

from flashsale.xiaolumm.models import MamaMission, MamaMissionRecord

class MamaMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaMission
        fields = ('id', 'name', 'kpi_type', 'target_value', 'award_amount')

class MamaMissionRecordSerializer(serializers.ModelSerializer):

    mission = MamaMissionSerializer(read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MamaMissionRecord
        fields = ('id', 'mission', 'mama_id', 'year_week', 'finish_value', 'finish_time', 'status', 'status_name')

class GroupMissionRecordSerializer(serializers.ModelSerializer):

    mission = MamaMissionSerializer(read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    group_finish_value = serializers.IntegerField(source='get_group_finish_value', read_only=True)

    class Meta:
        model = MamaMissionRecord
        fields = ('id', 'mission', 'mama_id', 'year_week', 'finish_value', 'group_finish_value', 'finish_time', 'status', 'status_name')