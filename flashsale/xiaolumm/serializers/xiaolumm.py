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
            return round(obj.target_value * 0.01, 2)
        return obj.target_value


class MamaMissionRecordSerializer(serializers.ModelSerializer):

    status_name = serializers.CharField(source='get_status_display', read_only=True)
    finish_value = serializers.SerializerMethodField(read_only=True)
    target_value = serializers.SerializerMethodField(read_only=True)
    award_amount = serializers.SerializerMethodField(read_only=True)
    mission  = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MamaMissionRecord
        fields = ('id', 'mission', 'mama_id', 'year_week', 'target_value', 'finish_value',
                  'award_amount', 'finish_time', 'status', 'status_name')

    def get_finish_value(self, obj):
        if obj.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return round(obj.finish_value * 0.01, 2)
        return obj.finish_value

    def get_target_value(self, obj):
        if obj.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return round(obj.target_value * 0.01, 2)
        return obj.target_value

    def get_award_amount(self, obj):
        return round(obj.award_amount * 0.01, 2)

    def get_mission(self, obj):
        mission = obj.mission
        target_value = obj.target_value
        award_amount = obj.award_amount
        if mission.kpi_type == MamaMission.KPI_AMOUNT:
            target_value = round(target_value * 0.01, 2)

        return {
            'id': mission.id,
            'name': obj.get_mission_name(),
            'kpi_type': mission.kpi_type,
            'target_value': target_value,
            'award_amount': award_amount
        }