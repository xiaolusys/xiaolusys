# coding: utf8
from __future__ import absolute_import, unicode_literals

import time
from django.conf import settings
from rest_framework import serializers
from .models.charge import ChargeOrder
from .models.refund import RefundOrder

class ChargeSerializer(serializers.ModelSerializer):

    credential = serializers.SerializerMethodField()
    refunds = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    time_paid = serializers.SerializerMethodField()
    time_expire = serializers.SerializerMethodField()

    amount_settle = serializers.SerializerMethodField()
    time_settle = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    app = serializers.SerializerMethodField()
    failure_msg = serializers.SerializerMethodField()
    failure_code = serializers.SerializerMethodField()

    class Meta:
        model = ChargeOrder
        fields = (
            "id",
            "order_no", # do
            "extra", # do
            "livemode",
            "currency",
            "time_expire", # do
            "subject", # do
            "channel", # do
            "body", #do
            "credential",
            "client_ip", #do
            "description",
            "amount_refunded",
            "refunded",
            "paid",
            "time_paid",
            "refunds",
            "created",  # do
            "transaction_no",
            "amount", # do
            "app",
            "time_settle",
            "metadata",
            "object",
            "amount_settle", #do
            "failure_msg",
            "failure_code",
        )

    def get_credential(self, obj):
        return {
                "object": "credential",
                obj.channel: obj.credential
            }

    def get_refunds(self, obj):
        return {
            "url": "/v1/charges/%s/refunds"%obj.order_no,
            "has_more": False,
            "object": "list",
            "data": []
        }

    def get_created(self, obj):
        return obj.created and time.mktime(obj.created.timetuple())

    def get_time_paid(self, obj):
        return obj.time_paid and time.mktime(obj.time_paid.timetuple())

    def get_time_expire(self, obj):
        return obj.time_expire and time.mktime(obj.time_expire.timetuple())

    def get_amount_settle(self, obj):
        return 100

    def get_time_settle(self, obj):
        return None

    def get_object(self, obj):
        return 'charge'

    def get_app(self, obj):
        return 'app_LOOajDn9u9WDjfHa'

    def get_failure_msg(self, obj):
        return ''

    def get_failure_code(self, obj):
        return ''

    def get_metadata(self, obj):
        return {"color": "red"}


class RefundSerializer(serializers.ModelSerializer):

    order_no = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    time_succeed = serializers.SerializerMethodField()

    class Meta:
        model = RefundOrder
        fields = (
            "id",
            "object",
            "order_no",
            "amount",
            "succeed",
            "status",
            "created",
            "time_succeed",
            "description",
            "failure_code",
            "failure_msg",
            "charge",
            "charge_order_no",
            "transaction_no",
            "funding_source",
        )

    def get_order_no(self, obj):
        return obj.refund_no

    def get_object(self, obj):
        return 'refund'

    def get_created(self, obj):
        return obj.created and time.mktime(obj.created.timetuple())

    def get_time_succeed(self, obj):
        return obj.time_succeed and time.mktime(obj.time_succeed.timetuple())