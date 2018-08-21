from shopapp.calendar.models import StaffEvent
from rest_framework import serializers


class MainStaffEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffEvent
        fields = ('curuser', 'staffs',)
        exclude = ('url',)


class StaffEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffEvent
        fields = ('id', 'creator', 'executor', 'start', 'end', 'interval_day', 'title', 'type', 'created', 'modified',
                  'is_finished')
        exclude = ('url',)
