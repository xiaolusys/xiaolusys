# -*- coding:utf-8 -*-
from flashsale.xiaolumm.models.message import XlmmMessage
from ..models.models import CashOut, CarryLog, XiaoluMama
from ..models.carry_total import MamaCarryTotal, MamaTeamCarryTotal, ActivityMamaCarryTotal
from ..models.rank import WeekMamaTeamCarryTotal, WeekMamaCarryTotal
from ..models.models_advertis import NinePicAdver
from rest_framework import serializers
from apis.v1.dailypush.ninepic import get_nine_pic_descriptions_by_modelids


class CashOutStatusField(serializers.Field):
    def to_representation(self, obj):
        for choice in CashOut.STATUS_CHOICES:
            if choice[0] == obj:
                return choice[1]
        return ""

    def to_internal_value(self, data):
        return data


class CashOutSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d")
    status = CashOutStatusField()

    class Meta:
        model = CashOut
        fields = ('xlmm', 'value', 'value_money', 'status', 'created')


class CarryLogSerializer(serializers.ModelSerializer):
    carry_date = serializers.DateTimeField(format="%y-%m-%d")

    class Meta:
        model = CarryLog
        fields = ('xlmm', 'order_num', 'buyer_nick', 'value', 'value_money', 'log_type',
                  'log_type_name', 'carry_type', 'carry_type_name', 'status_name', 'carry_date')


class NinePicAdverSerializer(serializers.ModelSerializer):
    # start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    cate_gory_display = serializers.CharField(source='get_cate_gory_display', read_only=True)
    push_status = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.CharField(source='sale_category.name')
    advertisement_type = serializers.IntegerField(source='cate_gory')
    advertisement_type_display = serializers.CharField(source='get_cate_gory_display', read_only=True)

    class Meta:
        model = NinePicAdver
        fields = (
            "id",
            "auther",
            "title",
            "description",
            "cate_gory",
            "pic_arry",
            "start_time",
            "turns_num",
            "is_pushed",
            'push_status',
            "detail_modelids",
            "cate_gory_display",
            "sale_category",
            'category_name',
            'advertisement_type',
            'advertisement_type_display',
            'redirect_url',
            'memo')

    def get_push_status(self, obj):
        # type: (NinePicAdver) -> text_type
        text_map = {
            True: u'已推/不推',
            False: u'将要推送'
        }
        return text_map[obj.is_pushed]


class HistoryDescriptionsNinePicAdverSerializer(serializers.ModelSerializer):
    cate_gory_display = serializers.CharField(source='get_cate_gory_display', read_only=True)
    push_status = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.CharField(source='sale_category.name')
    advertisement_type = serializers.IntegerField(source='cate_gory')
    advertisement_type_display = serializers.CharField(source='get_cate_gory_display', read_only=True)
    history_descriptions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NinePicAdver
        fields = (
            "id",
            "auther",
            "title",
            "description",
            'history_descriptions',
            "cate_gory",
            "pic_arry",
            "start_time",
            "turns_num",
            "is_pushed",
            'push_status',
            "detail_modelids",
            "cate_gory_display",
            "sale_category",
            'category_name',
            'advertisement_type',
            'advertisement_type_display',
            'redirect_url',
            'memo')

    def get_push_status(self, obj):
        # type: (NinePicAdver) -> text_type
        text_map = {
            True: u'已推/不推',
            False: u'将要推送'
        }
        return text_map[obj.is_pushed]

    def get_history_descriptions(self, obj):
        modelids = [i for i in obj.detail_modelids.split(',') if i.isdigit()]
        res = get_nine_pic_descriptions_by_modelids(modelids=modelids)
        return res


class XiaoluMamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = XiaoluMama
        fields = ('id', 'mobile', 'openid', 'province', 'city', 'address', 'referal_from', 'qrcode_link', 'weikefu',
                  'manager', 'cash', 'pending', 'hasale', 'last_renew_type', 'agencylevel', 'target_complete',
                  'lowest_uncoushout', 'user_group', 'charge_time', 'renew_time', 'created', 'modified', 'status',
                  'charge_status', 'progress')


class MamaCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'total', 'total_display', 'num', 'total', 'rank')


class MamaCarryTotalDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'duration_total', 'duration_total_display', 'duration_rank')


class ActivityMamaCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityMamaCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'mobile')


class MamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'mobile', 'num', 'total', 'duration_total', 'rank')


class MamaTeamCarryTotalDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = (
        'mama', 'mama_nick', 'thumbnail', 'mobile', 'duration_total', 'duration_total_display', 'duration_rank')


class ActivityMamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'mobile')


class XlmmMessageSerializers(serializers.ModelSerializer):
    class Meta:
        model = XlmmMessage
        fields = ('id', 'title', 'content_link', 'content', 'dest', 'status', 'read', 'created', 'creator')