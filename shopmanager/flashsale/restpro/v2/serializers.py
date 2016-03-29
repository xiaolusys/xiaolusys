# coding=utf-8
from rest_framework import serializers
from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, \
    ClickCarry, ActiveValue, ReferalRelationship, GroupRelationship, UniqueVisitor, DailyStats


class MamaFortuneSerializer(serializers.ModelSerializer):
    cash_value = serializers.FloatField(source='cash_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'mama_name', 'mama_level', 'mama_level_display', 'cash_value', 
                  'fans_num', 'invite_num','order_num', 'carry_value', 'active_value_num', 
                  'carry_pending_display', 'carry_confirmed_display', 'carry_cashout_display',
                  'mama_event_link', 'history_last_day', 'today_visitor_num', 'modified', 'created')


class CarryRecordSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    
    class Meta:
        model = CarryRecord
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num', 'carry_type', 'carry_type_name',"carry_description",
                  'status', 'status_display','today_carry', 'date_field', 
                  'modified', 'created')


class OrderCarrySerializer(serializers.ModelSerializer):
    order_value = serializers.FloatField(source='order_value_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    contributor_nick = serializers.CharField(source='contributor_nick_display', read_only=True)
    
    class Meta:
        model = OrderCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'order_id', 'order_value', 'carry_value', 'carry_num', 'carry_type', 
                  'carry_type_name','sku_name', 'sku_img', 'contributor_nick', "carry_description",
                  'contributor_img','contributor_id', 'agency_level', 'carry_plan_name',
                  'date_field', 'status','status_display', 'modified', 'created', 'today_carry',)


class AwardCarrySerializer(serializers.ModelSerializer):
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num',  'carry_type', 'carry_type_name', 'contributor_nick', 
                  "carry_description",'contributor_img','contributor_mama_id', 'carry_plan_name', 
                  'status','status_display', 'today_carry', 'modified', 'created')


class ClickCarrySerializer(serializers.ModelSerializer):
    init_click_price = serializers.FloatField(source='init_click_price_display', read_only=True)
    confirmed_click_price = serializers.FloatField(source='confirmed_click_price_display', read_only=True)
    total_value = serializers.FloatField(source='total_value_display', read_only=True)
    carry_value = serializers.FloatField(source='total_value_display', read_only=True)
    carry_num = serializers.FloatField(source='total_value_display', read_only=True)

    class Meta:
        model = ClickCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'click_num', 'init_order_num', 'init_click_price',
                  'init_click_limit', 'confirmed_order_num','confirmed_click_price',
                  'confirmed_click_limit', 'total_value','carry_value', 'carry_num', 'carry_description',
                  'carry_plan_name','date_field', 'uni_key', 'status','status_display', 
                  'today_carry','modified', 'created')


class ActiveValueSerializer(serializers.ModelSerializer):
    value_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = ActiveValue
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'value_num', 'value_type', 'value_type_name','uni_key','value_description',
                  'date_field', 'status','status_display', 'today_carry','modified', 'created')


class ReferalRelationshipSerializer(serializers.ModelSerializer):
    referal_to_mama_nick = serializers.CharField(source='referal_to_mama_nick_display', read_only=True)
    class Meta:
        model = ReferalRelationship
        fields = ('referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick', 
                  'referal_to_mama_img', 'modified', 'created')


class GroupRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRelationship
        fields = ('leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick',
                  'member_mama_img','modified', 'created')


class UniqueVisitorSerializer(serializers.ModelSerializer):
    visitor_nick = serializers.CharField(source='nick_display', read_only=True)
    class Meta:
        model = UniqueVisitor
        fields = ('mama_id', 'visitor_nick', 'visitor_img', 'visitor_description', 'uni_key', 'modified', 'created')



from flashsale.xiaolumm.models_fans import XlmmFans

class XlmmFansSerializer(serializers.ModelSerializer):
    fans_nick = serializers.CharField(source='nick_display', read_only=True)
    class Meta:
        model = XlmmFans
        fields = ('fans_nick', 'fans_thumbnail', 'fans_description', 'created')


class DailyStatsSerializer(serializers.ModelSerializer):
    order_num = serializers.IntegerField(source='today_order_num', read_only=True)
    visitor_num = serializers.IntegerField(source='today_visitor_num', read_only=True)
    carry = serializers.FloatField(source='today_carry_num_display', read_only=True)
    today_carry_num = serializers.FloatField(source='today_carry_num_display', read_only=True)
    class Meta:
        model = DailyStats
        
