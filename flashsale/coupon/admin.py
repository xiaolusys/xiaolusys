# coding=utf-8
from django.contrib import admin
from django.db.models import Sum
from core.options import log_action, CHANGE
from core.filters import DateFieldListFilter
from flashsale.xiaolumm.models import MamaDailyAppVisit
from flashsale.coupon.models import CouponTemplate, OrderShareCoupon, UserCoupon, TmpShareCoupon, CouponTransferRecord, \
    TransferCouponDetail
from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_id


class CouponTemplateAdmin(admin.ModelAdmin):
    fieldsets = (
        (u'标题信息:', {
            'classes': ('expand',),
            'fields': (('title', 'description', 'status'), )
        }),
        (u'数值信息:', {
            'classes': ('expand',),
            'fields': (('value', 'is_random_val', 'has_released_count', 'prepare_release_num'),)
        }),
        (u'时间信息:', {
            'classes': ('expand',),
            'fields': (('release_start_time', 'release_end_time', 'use_deadline'), )
        }),
        (u'其他信息:', {
            'classes': ('expand',),
            'fields': (('coupon_type', 'target_user', 'scope_type', 'is_flextime'),
                       'extras')
        }),
    )

    list_display = (
        'id', 'title', 'value', 'is_random_val', 'coupon_type', 'scope_type', 'has_released_count', 'has_used_count',
        'status', 'release_start_time', 'release_end_time', 'use_deadline', 'template_no')

    list_filter = ('coupon_type', 'scope_type', )
    search_fields = ['=id', ]
    date_hierarchy = 'created'

    def sync_coupon_value(self, request, queryset):
        # type: (HttpRequest, List[CouponTemplate]) -> HttpResponse
        """同步 未使用的优惠券 金额 与 模板相同
        """
        from .apis.v1.usercoupon import sync_coupon_value_by_template

        total_update_count = 0
        for tpl in queryset.filter(status=CouponTemplate.SENDING):
            c = sync_coupon_value_by_template(tpl)
            total_update_count += c
        return self.message_user(request, '共更新%s条记录' % total_update_count)

    sync_coupon_value.short_description = '同步优惠券金额与模板相同'
    actions = ['sync_coupon_value']


admin.site.register(CouponTemplate, CouponTemplateAdmin)


class OrderShareCouponAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'template_id', 'share_customer', 'share_start_time',
        'share_end_time', 'release_count', "has_used_count",
        'status')

    list_filter = ('share_end_time', 'share_start_time')
    search_fields = ['=id', '=share_customer', '=template_id']
    date_hierarchy = 'created'


admin.site.register(OrderShareCoupon, OrderShareCouponAdmin)


class UserCouponAdmin(admin.ModelAdmin):
    fieldsets = (
        (u'标题信息:', {
            'classes': ('expand',),
            'fields': (('template_id', 'title', 'customer_id', 'value', 'status'), )
        }),

        (u'时间信息:', {
            'classes': ('expand',),
            'fields': (('finished_time', 'start_use_time', 'expires_time'), )
        }),

        (u'其他信息:', {
            'classes': ('expand',),
            'fields': (('coupon_no', 'trade_tid', 'uniq_id'),
                       ('coupon_type', 'ufrom', 'is_pushed', 'is_chained', 'is_buyed'),
                       ('extras', ))
        }),
    )

    list_display = ('id', 'title', "customer_id", 'status', "uniq_id", 'finished_time',
                    'expires_time', 'is_pushed', 'is_chained', 'is_buyed', 'modified', 'created')

    list_filter = ('coupon_type', 'is_chained', 'is_buyed','status', 'expires_time', 'finished_time', ('created', DateFieldListFilter))
    search_fields = ['=id', '=template_id', '=customer_id']


admin.site.register(UserCoupon, UserCouponAdmin)


class TmpShareCouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile', 'share_coupon_id', 'value', 'status')

    list_filter = ('created', )
    search_fields = ['=id', '=mobile', '=share_coupon_id']
    date_hierarchy = 'created'


admin.site.register(TmpShareCoupon, TmpShareCouponAdmin)


class CouponTransferRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'coupon_from_mama_id', 'last_visit', 'from_mama_nick', 'coupon_to_mama_id', 'is_new',
                    'to_mama_nick', 'template_id', 'template_name',
                    'coupon_value', 'coupon_num', 'transfer_type', 'transfer_status_show', 'total_num',
                    'status', 'uni_key', 'date_field',
                    'init_from_mama_id', 'order_no', 'product_id', 'elite_score', 'to_mama_manager', 'modified',
                    'created')
    list_filter = ('transfer_type', 'transfer_status', 'status', ('created', DateFieldListFilter))
    search_fields = ['=coupon_from_mama_id', '=coupon_to_mama_id']
    list_per_page = 20

    def template_name(self, obj):
        ct = CouponTemplate.objects.filter(id=obj.template_id).first()
        if ct:
            return ct.title
        return ''

    def total_num(self, obj):
        res = CouponTransferRecord.objects.filter(
            date_field=obj.date_field, transfer_type=obj.transfer_type,
            transfer_status=obj.transfer_status).aggregate(n=Sum('coupon_num'))
        return res['n'] or 0

    def last_visit(self, obj):
        visit = MamaDailyAppVisit.objects.filter(mama_id=obj.coupon_from_mama_id).order_by('-created').first()
        if not visit:
            return ''
        return visit.date_field

    def is_new(self, obj):
        c = CouponTransferRecord.objects.filter(
            date_field__lt=obj.date_field, coupon_to_mama_id=obj.coupon_to_mama_id,
            transfer_status=CouponTransferRecord.DELIVERED).first()
        if not c:
            return 'NEW'
        return ''

    def transfer_status_show(self, obj):
        # type : (CouponTransferRecord) -> text_type
        if obj.transfer_status == CouponTransferRecord.PENDING and \
                (obj.transfer_type == CouponTransferRecord.OUT_CASHOUT or obj.transfer_type == CouponTransferRecord.OUT_CASHOUT_COIN):  # 待审核 和 类型为 退券换钱
            et = 'style="padding: 0px 6px" type="button"'
            html1 = '<input class="returnT%s" %s onclick="agreeReturnTransfer(%s)" value="通过">' % (obj.id, et, obj.id )
            html2 = '<input class="returnT%s" %s onclick="rejectReturnTransfer(%s)" value="拒绝">' % (obj.id, et, obj.id )
            return ''.join([html1, html2])
        return obj.get_transfer_status_display()

    transfer_status_show.allow_tags = True
    transfer_status_show.short_description = u"流通状态"

    def to_mama_manager(self, obj):
        # type : (CouponTransferRecord) -> text_type
        if not obj.coupon_to_mama_id:
            return u''
        mm = get_mama_by_id(obj.coupon_to_mama_id)
        if not mm or not mm.mama_manager:
            return u''
        return mm.mama_manager.last_name + mm.mama_manager.first_name

    to_mama_manager.allow_tags = True
    to_mama_manager.short_description = u"归属管理员"

    class Media:
        js = (
            '/static/jquery/jquery-2.1.1.min.js',
            "/static/layer-v1.9.2/layer/layer.js",
            '/static/coupon/js/transferCoupon.js',
            "/static/layer-v1.9.2/layer/extend/layer.ext.js",
        )


admin.site.register(CouponTransferRecord, CouponTransferRecordAdmin)


class TransferCouponDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'transfer_id', 'transfer_type', 'from_to_mama_id', 'coupon_id', 'template_id',
                    'current_customer',
                    'modified', 'created')
    list_filter = ('transfer_type', )
    search_fields = ['=transfer_id', '=coupon_id']
    list_per_page = 50

    def from_to_mama_id(self, obj):
        return u'%s => %s' % (obj.transfer.coupon_from_mama_id, obj.transfer.coupon_to_mama_id)

    from_to_mama_id.allow_tags = True
    from_to_mama_id.short_description = u"From => To"

    def current_customer(self, obj):
        return obj.usercoupon.customer_id

    current_customer.allow_tags = True
    current_customer.short_description = u"优惠券当前用户"

    def template_id(self, obj):
        return obj.usercoupon.template_id

    template_id.allow_tags = True
    template_id.short_description = u"模板id"


admin.site.register(TransferCouponDetail, TransferCouponDetailAdmin)

