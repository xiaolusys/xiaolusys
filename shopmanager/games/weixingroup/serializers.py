from rest_framework import serializers
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, Activity, ActivityUsers


class XiaoluAdministratorSerializers(serializers.ModelSerializer):
    # district = serializers.CharField(source='district.district_no', read_only=True)

    class Meta:
        model = XiaoluAdministrator


class GroupMamaAdministratorSerializers(serializers.ModelSerializer):

    class Meta:
        model = GroupMamaAdministrator


class GroupFansSerializers(serializers.ModelSerializer):

    class Meta:
        model = GroupFans


class ActivitySerializers(serializers.ModelSerializer):
    class Meta:
        model = Activity


class ActivityUsersSerializers(serializers.ModelSerializer):
    class Meta:
        model = ActivityUsers