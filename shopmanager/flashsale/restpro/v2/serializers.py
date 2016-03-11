# coding=utf-8
from rest_framework import serializers
from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, \
    ClickCarry, ActiveValue, ReferalRelationship, GroupRelationship


class MamaFortuneSerializer(serializers.ModelSerializer):
    cash_value = serializers.FloatField(source='cash_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'mama_name', 'mam_level', 'cash_value', 'fans_num', 'invite_num',
                  'order_num', 'carry_value', 'active_value_num', 'today_visitor_num')


class CarryRecordSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = CarryRecord
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_type', 'carry_type_name',
                  'status', 'status_display','today_carry', 'modified', 'created')


class OrderCarrySerializer(serializers.ModelSerializer):
    order_value = serializers.FloatField(source='order_value_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    
    class Meta:
        model = OrderCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'order_id', 'order_value', 'carry_num', 'carry_type', 
                  'carry_type_name','sku_name', 'sku_img', 'contributor_nick', 
                  'contributor_img','contributor_id', 'agency_level', 'carry_plan_name',
                  'date_field', 'status','status_display', 'modified', 'created', 'today_carry',)


class AwardCarrySerializer(serializers.ModelSerializer):
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_num', 'carry_type', 'carry_type_name', 'contributor_nick', 
                  'contributor_img','contributor_mama_id', 'carry_plan_name', 'status','status_display', 
                  'today_carry', 'modified', 'created')


class ClickCarrySerializer(serializers.ModelSerializer):
    init_click_price = serializers.FloatField(source='init_click_price_display', read_only=True)
    confirmed_click_price = serializers.FloatField(source='confirmed_click_price_display', read_only=True)
    total_value = serializers.FloatField(source='total_value_display', read_only=True)

    class Meta:
        model = ClickCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'init_click_num', 'init_order_num', 'init_click_price',
                  'init_click_limit', 'confirmed_click_num', 'confirmed_order_num',
                  'confirmed_click_price', 'confirmed_click_limit', 'total_value',
                  'carry_plan_name','date_field', 'uni_key', 'status','status_display', 
                  'today_carry','modified', 'created')


class ActiveValueSerializer(serializers.ModelSerializer):
    value_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = ActiveValue
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'value_num', 'value_type', 'value_type_name','uni_key',
                  'date_field', 'status','status_display', 'today_carry','modified', 'created')


class ReferalRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferalRelationship
        fields = ('referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick', 'referal_to_mama_img',
                  'modified', 'created')


class GroupRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRelationship
        fields = ('leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick',
                  'member_mama_img','modified', 'created')

