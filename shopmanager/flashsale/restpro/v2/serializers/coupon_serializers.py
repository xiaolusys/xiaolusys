# coding=utf-8

from rest_framework import serializers

from flashsale.coupon.models import (
    CouponTransferRecord,
)


class CouponTransferRecordSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CouponTransferRecord
        fields = ('id', 'coupon_from_mama_id', 'from_mama_thumbnail', 'from_mama_nick', 'coupon_to_mama_id',
                  'to_mama_thumbnail', 'to_mama_nick', 'template_id', 'product_img', 'coupon_value', 'coupon_num',
                  'transfer_type', 'transfer_status', 'status', 'uni_key', 'date_field', 'month_day', 'elite_level',
                  'hour_minute', 'transfer_status_display', 'is_cancelable', 'is_processable', 'modified', 'created')





