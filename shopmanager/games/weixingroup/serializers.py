from rest_framework import serializers
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, ActivityUsers
from flashsale.promotion.models.stocksale import StockSale
from flashsale.promotion.models import ActivityEntry


class XiaoluAdministratorSerializers(serializers.ModelSerializer):
    class Meta:
        model = XiaoluAdministrator
        fields = ['user_id', 'username', 'nick', 'head_img_url', 'weixin_qr_img', 'status', 'groups_count',
                  'all_groups_count']


class GroupMamaAdministratorSerializers(serializers.ModelSerializer):
    class Meta:
        model = GroupMamaAdministrator


class MamaGroupsSerializers(serializers.ModelSerializer):
    class Meta:
        model = GroupMamaAdministrator
        fields = ["id", "created", "modified_display", "mama_id", "group_uni_key", "status", "admin", "nick",
                  "head_img_url", 'fans_count',
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
