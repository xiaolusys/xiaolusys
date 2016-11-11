# -*- coding:utf-8 -*-
from django.db import models
from django.contrib import admin
from django.forms import TextInput, Textarea
from .models import XLFreeSample, XLSampleApply, XLSampleOrder, XLSampleSku, ReadPacket, AppDownloadRecord, \
    RedEnvelope, AwardWinner, DownloadMobileRecord, DownloadUnionidRecord, XLInviteCode, XLReferalRelationship, \
    XLInviteCount, ActivityEntry, ActivityProduct
from core.filters import DateFieldListFilter
from core.admin import ApproxAdmin, BaseAdmin, BaseModelAdmin
from flashsale.promotion.models.stocksale import StockSale, ActivityStockSale, BatchStockSale


class ActivityProductInline(admin.TabularInline):
    model = ActivityProduct
    fields = ('product_name', 'product_img', 'model_id', 'start_time', 'end_time',)


class ActivityProductAdmin(ApproxAdmin):
    list_display = ('id', 'activity', 'product_name', 'product_img', 'model_id', 'start_time', 'end_time')

    list_filter = (('start_time', DateFieldListFilter), ('end_time', DateFieldListFilter))
    search_fields = ['product_name', '=model_id', '=activity']
    list_per_page = 25

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 128})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 128})},
    }


admin.site.register(ActivityProduct, ActivityProductAdmin)


class ActivityEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'act_type', 'start_time', 'end_time', 'created', 'remarks', 'is_active', 'order_val')

    list_filter = ('is_active', 'act_type',
                   ('start_time', DateFieldListFilter),
                   ('created', DateFieldListFilter))
    search_fields = ['=id', 'title']
    list_per_page = 25

    inlines = [ActivityProductInline]

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 128})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 128})},
    }

    def remarks(self, obj):
        if isinstance(obj.extras, dict) and obj.extras.has_key('remarks'):
            return obj.extras['remarks']
        else:
            return ""

    remarks.short_description = u'备注'


admin.site.register(ActivityEntry, ActivityEntryAdmin)


class XLFreeSampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'name', 'expiried', 'pic_url', 'sale_url')
    list_display_links = ('id', 'outer_id',)
    search_fields = ['=id', '=outer_id', ]
    list_per_page = 40


admin.site.register(XLFreeSample, XLFreeSampleAdmin)


class XLSampleApplyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'event_id', 'from_customer', 'user_unionid', 'customer_id', 'nick', 'mobile', 'ufrom', 'outer_id',
        'event_imei', 'status', 'modified', 'created')
    list_filter = ('event_id', 'status', 'ufrom', ('created', DateFieldListFilter))
    list_display_links = ('id', 'event_id')
    search_fields = ['=id', '=from_customer', '=customer_id', '=mobile', '=user_unionid']
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
    list_display = ('id', 'from_customer', 'from_mama', 'unionid', 'fans_customer', 'nick', 'mobile', 'status', 'modified', 'created', 'inner_ufrom')
    list_display_links = ('id', 'from_customer')
    list_filter = ('created', 'status', 'inner_ufrom')
    search_fields = ['id', 'mobile', 'from_customer', 'unionid']
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


class DownloadMobileRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_customer",
        "mobile",
        "ufrom",
        "created",
        "modified"
    )
    list_filter = ('ufrom',)
    search_fields = ('from_customer', 'mobile')


admin.site.register(DownloadMobileRecord, DownloadMobileRecordAdmin)


class DownloadUnionidRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_customer",
        "unionid",
        "ufrom",
        "created",
        "modified"
    )
    list_filter = ('ufrom',)
    search_fields = ('from_customer', 'unionid')


admin.site.register(DownloadUnionidRecord, DownloadUnionidRecordAdmin)


class StockSaleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sale_product__name',
        'sale_product_link',
        'product__name',
        'product__link',
        'product__sku_link',
        'quantity',
        'batch',
        'day_batch_num',
        'status',
        'stock_safe'
    )
    list_filter = ('batch', 'day_batch_num', 'status', 'stock_safe')
    search_fields = ('id', 'batch__id', 'sale_product__id', 'sale_product__name', 'product__id', 'product__outerid', 'product__name')
    list_select_related = True
    def lookup_allowed(self, lookup, value):
        if lookup in ['batch__id', 'sale_product__id', 'sale_product__name', 'product__id', 'product__outerid', 'product__name']:
            return True
        return super(StockSaleAdmin, self).lookup_allowed(lookup, value)

    def sale_product__name(self, obj):
        return obj.sale_product.title if obj.sale_product else ''
    sale_product__name.short_description = u'选品名称'

    def product__outerid(self, obj):
        return obj.product.outer_id
    product__outerid.short_description = u'商品编码'

    def product__name(self, obj):
        return obj.product.name
    product__name.short_description = u'商品名称'

    def sale_product_link(self, obj):
        return '<a href="/admin/supplier/saleproduct?id=%s" target="_blank">%s</a>' % (
            obj.sale_product_id, obj.sale_product_id) if obj.sale_product else ''

    sale_product_link.short_description = u'选品id'
    sale_product_link.allow_tags = True
    sale_product_link.admin_order_field = 'sale_product_id'

    def product__link(self, obj):
        return '<a href="/admin/items/product?id=%s" target="_blank">%s</a>' % (
            obj.product_id, obj.product_id)
    product__link.short_description = u'商品id'
    product__link.allow_tags = True
    product__link.admin_order_field = 'product_id'

    def product__sku_link(self, obj):
        return '<a href="/admin/items/productsku?product_id=%s" target="_blank">%s</a>' % (
            obj.product_id, obj.sku_num)
    product__sku_link.short_description = u'商品SKU数'
    product__sku_link.allow_tags = True


admin.site.register(StockSale, StockSaleAdmin)


class ActivityStockSaleAdmin(BaseModelAdmin):
    list_display = (
        'id_link',
        'activity',
        'batch',
        'day_batch_num',
        'onshelf_time',
        'offshelf_time',
        'stock_sales_link',
        'total',
        'product_total',
        'sku_total',
        'stock_total',
    )
    list_filter = ('status', 'onshelf_time')
    search_fields = ('id',)

    def id_link(self, obj):
        return '<a href="%(link)s">%(show_text)d</a>' % {'link': '/admin/promotion/activitystocksale/' + str(obj.id),
                                                         'show_text': obj.id}
    id_link.short_description = u'ID'
    id_link.allow_tags = True

    def stock_sales_link(self, obj):
        link = '/admin/promotion/stocksale?day_batch_num=%s&batch_id=%s' % (obj.day_batch_num, obj.batch_id)
        return '<a href="%(link)s">%(show_text)d</a>' % {'link': link, 'show_text': obj.product_total}
    stock_sales_link.short_description = u'商品总数'
    stock_sales_link.allow_tags = True

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'最后疯抢活动详情',
                         'has_perm_product': request.user.has_perm('promotion.add_activitystocksale'),
                         'has_perm_package': request.user.has_perm('trades.change_packageorder'),
                         }
        return self.detailform_view(request, object_id, form_url, extra_context)
admin.site.register(ActivityStockSale, ActivityStockSaleAdmin)


class BatchStockSaleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status',
        'total',
        'product_total',
        'sku_total',
        'stock_total',
        'expected_time',
    )
    list_filter = ('status',)
    search_fields = ('id', )

admin.site.register(BatchStockSale, BatchStockSaleAdmin)
