# coding=utf-8
import datetime
import json
import collections
import random
from django.conf import settings
from django.core.cache import cache
from django.forms import model_to_dict
from rest_framework import serializers
from flashsale.restpro import constants

from flashsale.xiaolumm.models_fortune import (
    MamaFortune,
    CarryRecord,
    OrderCarry,
    AwardCarry,
    ClickCarry,
    ActiveValue,
    ReferalRelationship,
    GroupRelationship,
    UniqueVisitor,
    DailyStats,
)

from flashsale.xiaolumm.models_rebeta import AgencyOrderRebetaScheme, calculate_price_carry
from flashsale.xiaolumm.models import XiaoluMama
from shopback.items.models import Product
from flashsale.pay.models import Customer


class MamaFortuneSerializer(serializers.ModelSerializer):
    cash_value = serializers.FloatField(source='cash_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    extra_info = serializers.SerializerMethodField('gen_extra_info', read_only=True)

    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'mama_name', 'mama_level', 'mama_level_display', 'cash_value',
                  'fans_num', 'invite_num', 'order_num', 'carry_value', 'active_value_num',
                  'carry_pending_display', 'carry_confirmed_display', 'carry_cashout_display',
                  'mama_event_link', 'history_last_day', 'today_visitor_num', 'modified', 'created',
                  "extra_info")

    def gen_extra_info(self, obj):
        customer = self.context['customer']
        xlmm = self.context['xlmm']
        invite_url = constants.MAMA_INVITE_AGENTCY_URL.format(**{'site_url': settings.M_SITE_URL})
        surplus_days = (xlmm.renew_time - datetime.datetime.now()).days if xlmm.renew_time else 0
        surplus_days = max(surplus_days, 0)
        next_level_exam_url = 'http://m.xiaolumeimei.com/mall/activity/exam'
        xlmm_next_level = xlmm.next_agencylevel_info()
        could_cash_out = 1
        tmp_des = []
        if obj.cash_num_display() < 100.0:
            tmp_des.append(u'余额不足')
            could_cash_out = 0
        if obj.active_value_num < 100:
            tmp_des.append(u'活跃度不足')
            could_cash_out = 0
        cashout_reason = u' '.join(tmp_des) + u'不能提现'

        return {
            "invite_url": invite_url,
            "agencylevel": xlmm.agencylevel,
            "agencylevel_display": xlmm.get_agencylevel_display(),
            "surplus_days": surplus_days,
            "next_agencylevel": xlmm_next_level[0],
            "next_agencylevel_display": xlmm_next_level[1],
            "next_level_exam_url": next_level_exam_url,
            "thumbnail": customer.thumbnail if customer else '',
            "could_cash_out":could_cash_out,
            "cashout_reason": cashout_reason
        }


class CarryRecordSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = CarryRecord
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num', 'carry_type', 'carry_type_name', "carry_description",
                  'status', 'status_display', 'today_carry', 'date_field',
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
                  'carry_type_name', 'sku_name', 'sku_img', 'contributor_nick', "carry_description",
                  'contributor_img', 'contributor_id', 'agency_level', 'carry_plan_name',
                  'date_field', 'status', 'status_display', 'modified', 'created', 'today_carry',)


class AwardCarrySerializer(serializers.ModelSerializer):
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num', 'carry_type', 'carry_type_name', 'contributor_nick',
                  "carry_description", 'contributor_img', 'contributor_mama_id', 'carry_plan_name',
                  'status', 'status_display', 'today_carry', 'date_field', 'modified', 'created')


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
                  'init_click_limit', 'confirmed_order_num', 'confirmed_click_price',
                  'confirmed_click_limit', 'total_value', 'carry_value', 'carry_num', 'carry_description',
                  'carry_plan_name', 'date_field', 'uni_key', 'status', 'status_display',
                  'today_carry', 'modified', 'created')


class ActiveValueSerializer(serializers.ModelSerializer):
    value_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = ActiveValue
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'value_num', 'value_type', 'value_type_name', 'uni_key', 'value_description',
                  'date_field', 'status', 'status_display', 'today_carry', 'modified', 'created')


class AwardCarry4ReferalRelationshipSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('carry_value', 'carry_type', 'carry_type_name', 'status',
                  'status_display')


class ReferalRelationshipSerializer(serializers.ModelSerializer):
    referal_to_mama_nick = serializers.CharField(source='referal_to_mama_nick_display', read_only=True)
    referal_award = AwardCarry4ReferalRelationshipSerializer(source='get_referal_award', read_only=True)

    class Meta:
        model = ReferalRelationship
        fields = ('referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick',
                  'referal_to_mama_img', 'referal_award', 'modified', 'created')


class GroupRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRelationship
        fields = ('leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick',
                  'member_mama_img', 'modified', 'created')


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


class ProductSimpleSerializerV2(serializers.ModelSerializer):
    level_info = serializers.SerializerMethodField('agencylevel_info', read_only=True)
    shop_product_num = serializers.SerializerMethodField('shop_products_info', read_only=True)

    class Meta:
        model = Product
        extra_kwargs = {'in_customer_shop': {}, 'shop_product_num': {}}
        fields = ('id', 'pic_path', 'name', 'std_sale_price', 'agent_price', 'remain_num',
                  'in_customer_shop', 'shop_product_num',
                  "level_info")

    @property
    def agency_rebate_info(self):
        if not hasattr(self, '_agency_rebate_info_'):
            rebate = AgencyOrderRebetaScheme.objects.get(status=AgencyOrderRebetaScheme.NORMAL, is_default=True)
            self._agency_rebate_info_ = model_to_dict(rebate)
            return self._agency_rebate_info_
        return self._agency_rebate_info_

    def mama_agency_level_info(self, user):
        default_info = collections.defaultdict(agencylevel=XiaoluMama.INNER_LEVEL,
                                               agencylevel_desc=XiaoluMama.AGENCY_LEVEL[0][1],
                                               next_agencylevel=XiaoluMama.A_LEVEL,
                                               next_agencylevel_desc=XiaoluMama.AGENCY_LEVEL[2][1])
        customer = Customer.objects.filter(user=user).exclude(status=Customer.DELETE).first()
        if not customer:
            return default_info
        xlmm = customer.getXiaolumm()
        if not xlmm:
            return default_info
        next_agencylevel, next_agencylevel_desc = xlmm.next_agencylevel_info()
        default_info.update({
            "agencylevel": xlmm.agencylevel,
            "agencylevel_desc": xlmm.get_agencylevel_display(),
            "next_agencylevel": next_agencylevel,
            "next_agencylevel_desc": next_agencylevel_desc
        })
        return default_info

    def agencylevel_info(self, obj):
        user = self.context['request'].user
        info = self.mama_agency_level_info(user)
        sale_num = obj.remain_num * 19 + random.choice(xrange(19))
        sale_num_des = '{0}人在卖'.format(sale_num)
        rebate = self.agency_rebate_info
        rebet_amount = calculate_price_carry(info['agencylevel'], obj.agent_price, rebate['price_rebetas'])
        rebet_amount_des = '佣 ￥{0}.00'.format(rebet_amount)
        next_rebet_amount = calculate_price_carry(info['next_agencylevel'], obj.agent_price, rebate['price_rebetas'])
        next_rebet_amount_des = '佣 ￥{0}.00'.format(next_rebet_amount)
        info.update({
            "sale_num": sale_num,
            "sale_num_des": sale_num_des,
            "rebet_amount": rebet_amount,
            "rebet_amount_des": rebet_amount_des,
            "next_rebet_amount": next_rebet_amount,
            "next_rebet_amount_des": next_rebet_amount_des
        })
        return info

    def shop_products_info(self, obj):
        shop_products_num = self.context['shop_product_num']
        return shop_products_num


from flashsale.promotion.models import AppDownloadRecord

class AppDownloadRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = AppDownloadRecord
        fields = ('headimgurl', 'nick', 'mobile', 'note', 'modified', 'created')
