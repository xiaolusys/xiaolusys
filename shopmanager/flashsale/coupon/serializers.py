# coding=utf-8
from rest_framework import serializers
from flashsale.coupon.models import CouponTemplate, UserCoupon, OrderShareCoupon


class CouponTemplateSerialize(serializers.ModelSerializer):
    class Meta:
        model = CouponTemplate


class UserCouponSerialize(serializers.ModelSerializer):
    coupon_value = serializers.FloatField(source='value', read_only=True)
    valid = serializers.BooleanField(source='is_valid_template', read_only=True)
    poll_status = serializers.IntegerField(source='status', read_only=True)
    use_fee = serializers.FloatField(source='min_payment', read_only=True)
    use_fee_des = serializers.CharField(source='use_fee_des', read_only=True)
    pros_desc = serializers.CharField(source='scope_type_desc', read_only=True)
    start_time = serializers.DateTimeField(source='start_use_time', read_only=True)

    class Meta:
        model = UserCoupon
        fields = (
            'coupon_type', "coupon_type_display", "title", 'customer', "coupon_no", "coupon_value", "valid",
            "poll_status", "deadline", "start_use_time", "sale_trade", "status", "created",
            "use_fee", "use_fee_des", "pros_desc", "start_time")


class OrderShareCouponSerialize(serializers.ModelSerializer):
    class Meta:
        model = OrderShareCoupon
