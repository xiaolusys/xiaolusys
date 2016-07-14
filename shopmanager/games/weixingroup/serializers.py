from rest_framework import serializers
from django.forms import model_to_dict
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, ActivityUsers
from flashsale.promotion.models import ActivityEntry


class XiaoluAdministratorSerializers(serializers.ModelSerializer):
    # district = serializers.CharField(source='district.district_no', read_only=True)

    class Meta:
        model = XiaoluAdministrator


class GroupMamaAdministratorSerializers(serializers.ModelSerializer):
    class Meta:
        model = GroupMamaAdministrator


class MamaGroupsSerializers(serializers.ModelSerializer):

    class Meta:
        model = GroupMamaAdministrator
        fields = ["id", "created", "modified", "mama_id", "group_uni_key", "status", "admin", "nick", "head_img_url",
                  "union_id", "open_id"]


class GroupFansSerializers(serializers.ModelSerializer):
    class Meta:
        model = GroupFans


class ActivityEntrySerializers(serializers.ModelSerializer):
    class Meta:
        model = ActivityEntry


class ActivityUsersSerializers(serializers.ModelSerializer):
    class Meta:
        model = ActivityUsers
