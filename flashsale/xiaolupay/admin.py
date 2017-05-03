# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from .models.charge import ChargeOrder, Credential
from .models.refund import RefundOrder
from .models.weixin_red_envelope import WeixinRedEnvelope
from .models.weixin_transfers import WeixinTransfers

@admin.register(ChargeOrder)
class ChargeOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_no', 'channel', 'amount', 'paid', 'refunded', 'failure_code', 'failure_msg', 'time_paid', 'created', 'transaction_no')
    ordering = ['-id']
    list_filter = ['paid', 'channel', 'time_paid', 'created']
    search_fields = ['=id', '=order_no', '=transaction_no']


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_no', 'channel', 'extra', 'created')
    ordering = ['-id']
    list_filter = ['channel', 'created']
    search_fields = ['=order_no']


@admin.register(RefundOrder)
class RefundOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'refund_no', 'amount', 'status', 'time_succeed', 'failure_code', 'failure_msg', 'charge_order_no', 'funding_source', 'modified','created')
    ordering = ['-id']
    list_filter = ['succeed', 'status', 'created', 'time_succeed']
    search_fields = ['=refund_no', '=charge_order_no']

    readonly_fields = ['charge']


@admin.register(WeixinRedEnvelope)
class WeixinRedEnvelopeAdmin(admin.ModelAdmin):
    list_display = ('id', 'mch_billno', 'total_amount', 'total_num', 'wishing', 'act_name', 'return_code', 'result_code', 'err_code',
                    'status', 'send_time', 'refund_time', 'rcv_time', 'modified','created')
    ordering = ['-id']
    list_filter = ['status', 'send_time', 'refund_time', 'rcv_time']
    search_fields = ['=mch_billno', '=send_listid']

    readonly_fields = ['send_listid']


@admin.register(WeixinTransfers)
class WeixinTransfersAdmin(admin.ModelAdmin):
    list_display = ('id', 'mch_billno', 'openid', 'name', 'amount', 'return_code', 'result_code', 'err_code')
    ordering = ['-id']
    list_filter = ['created']
    search_fields = ['=mch_billno', '=payment_no']

    readonly_fields = ['payment_no']



