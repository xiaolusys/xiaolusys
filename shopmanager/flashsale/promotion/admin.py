# -*- coding:utf-8 -*-
from django.contrib import admin
from .models_freesample import XLFreeSample, XLSampleApply, XLSampleOrder, XLSampleSku, ReadPacket, AppDownloadRecord, \
    RedEnvelope, AwardWinner
from .models import XLInviteCode, XLReferalRelationship, XLInviteCount


class XLFreeSampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'name', 'expiried', 'pic_url', 'sale_url')
    list_display_links = ('id', 'outer_id',)
    search_fields = ['=id', '=outer_id', ]
    list_per_page = 40


admin.site.register(XLFreeSample, XLFreeSampleAdmin)


class XLSampleApplyAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'event_id', 'from_customer', 'user_openid', 'customer_id', 'mobile', 'ufrom', 'outer_id', 'status', 'created')
    list_filter = ('event_id', 'status', 'ufrom')
    list_display_links = ('id', 'event_id')
    search_fields = ['=id', '=from_customer', '=customer_id', '=mobile', '=user_openid']
    list_per_page = 40


admin.site.register(XLSampleApply, XLSampleApplyAdmin)


class XLSampleOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'xlsp_apply', 'customer_id', 'outer_id', 'sku_code', 'vipcode', 'created',
        'problem_score', 'award_status', 'status')
    list_filter = ('status', 'award_status')
    list_display_links = ('id', 'customer_id',)
    search_fields = ['=id', '=customer_id', 'vipcode', '=xlsp_apply']
    list_per_page = 40


admin.site.register(XLSampleOrder, XLSampleOrderAdmin)


class XLSampleSkuAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_product', 'sku_code', 'sku_name')
    list_display_links = ('id', 'sample_product',)
    search_fields = ['sample_product', 'sku_code', 'sku_name']
    list_per_page = 40


admin.site.register(XLSampleSku, XLSampleSkuAdmin)


class XLInviteCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile', 'vipcode', 'expiried', 'code_type', 'max_usage', 'usage_count')
    list_filter = ('code_type',)
    list_display_links = ('id', 'mobile', 'vipcode',)
    search_fields = ['id', 'mobile', 'vipcode', ]
    list_per_page = 40


admin.site.register(XLInviteCode, XLInviteCodeAdmin)


class XLInviteCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'apply_count', 'invite_count', 'click_count')
    search_fields = ['id', 'customer__mobile', 'customer__openid']
    list_per_page = 40

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('customer',)
        return self.readonly_fields


admin.site.register(XLInviteCount, XLInviteCountAdmin)


class XLReferalRelationshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'referal_uid', 'referal_from_uid')
    list_display_links = ('id', 'referal_uid', 'referal_from_uid')
    search_fields = ['id', 'referal_uid', 'referal_from_uid']
    list_per_page = 40


admin.site.register(XLReferalRelationship, XLReferalRelationshipAdmin)


class ReadPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'value', 'status', 'content', 'created')
    list_display_links = ('id', 'customer')
    list_filter = ('created', 'status')
    search_fields = ['id', 'customer']
    list_per_page = 40


admin.site.register(ReadPacket, ReadPacketAdmin)


class AppDownloadRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_customer', 'openid', 'mobile', 'status', 'modified', 'created')
    list_display_links = ('id', 'from_customer')
    list_filter = ('created', 'status')
    search_fields = ['id', 'mobile', 'from_customer']
    list_per_page = 40


admin.site.register(AppDownloadRecord, AppDownloadRecordAdmin)


class RedEnvelopeAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'value', 'description', 'friend_img', 'friend_nick', 'type', 'status')
    list_filter = ('type', 'status')
    search_fields = ('customer_id', 'friend_nick')


admin.site.register(RedEnvelope, RedEnvelopeAdmin)


class AwardWinnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'customer_nick', 'event_id', 'invite_num', 'status')
    list_filter = ('status',)
    search_fields = ('customer_id', 'customer_nick')


admin.site.register(AwardWinner, AwardWinnerAdmin)
