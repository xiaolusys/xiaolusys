# -*- coding:utf8 -*-
from django.contrib import admin
from .models_freesample import XLFreeSample, XLSampleApply, XLSampleOrder, XLSampleSku, ReadPacket
from .models import XLInviteCode, XLReferalRelationship


class XLFreeSampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'name', 'expiried', 'pic_url', 'sale_url')
    list_display_links = ('id', 'outer_id', )
    search_fields = ['=id', '=outer_id', ]
    list_per_page = 40


admin.site.register(XLFreeSample, XLFreeSampleAdmin)


class XLSampleApplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_customer', 'outer_id', 'sku_code', 'ufrom', 'mobile', 'vipcode', 'status')
    list_filter = ('status', 'ufrom')
    list_display_links = ('id', 'outer_id', )
    search_fields = ['=id', '=outer_id', '=mobile', '=user_openid' ,'=vipcode' ]
    list_per_page = 40


admin.site.register(XLSampleApply, XLSampleApplyAdmin)


class XLSampleOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'xlsp_apply', 'customer_id', 'outer_id', 'sku_code', 'vipcode', 'problem_score', 'status')
    list_filter = ('status',)
    list_display_links = ('id', 'customer_id', )
    search_fields = ['=id', '=customer_id', 'vipcode']
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
    list_display_links = ('id', 'mobile', 'vipcode', )
    search_fields = ['id', 'mobile', 'vipcode', ]
    list_per_page = 40


admin.site.register(XLInviteCode, XLInviteCodeAdmin)


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
