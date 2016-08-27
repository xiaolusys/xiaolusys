# -*- coding:utf-8 -*-

from rest_framework import serializers

from flashsale.xiaolumm.models import MamaMission, MamaMissionRecord

class MamaMissionSerializer(serializers.ModelSerializer):
    target_value = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = MamaMission
        fields = ('id', 'name', 'kpi_type', 'target_value', 'award_amount')

    def get_target_value(self, obj):
        if obj.kpi_type == MamaMission.KPI_AMOUNT:
            return obj.target_value / 100.0
        return obj.target_value

class MamaMissionRecordSerializer(serializers.ModelSerializer):

    mission = MamaMissionSerializer(read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    finish_value = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MamaMissionRecord
        fields = ('id', 'mission', 'mama_id', 'year_week', 'finish_value', 'finish_time', 'status', 'status_name')

    def get_finish_value(self, obj):
        if obj.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return obj.finish_value / 100.0
        return obj.finish_value


class GroupMissionRecordSerializer(serializers.ModelSerializer):

    mission = MamaMissionSerializer(read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    finish_value = serializers.SerializerMethodField(read_only=True)
    group_finish_value = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MamaMissionRecord
        fields = ('id', 'mission', 'mama_id', 'year_week', 'finish_value', 'group_finish_value', 'finish_time', 'status', 'status_name')

    def get_finish_value(self, obj):
        if obj.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return obj.finish_value / 100.0
        return obj.finish_value

    def get_group_finish_value(self, obj):
        group_value = obj.get_group_finish_value()
        if obj.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return group_value / 100.0
        return group_value