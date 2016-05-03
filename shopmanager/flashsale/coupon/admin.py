# coding=utf-8
from django.contrib import admin
from flashsale.coupon.models import CouponTemplate, OrderShareCoupon, UserCoupon, TmpShareCoupon


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
            'fields': (('coupon_type', 'target_user', 'scope_type'),
                       'extras')
        }),
    )

    list_display = (
        'id', 'title', 'value', 'is_random_val', 'coupon_type', 'scope_type', 'has_released_count', 'has_used_count',
        'status')

    list_filter = ('coupon_type', 'scope_type', )
    search_fields = ['=id', ]
    date_hierarchy = 'created'


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
            'fields': (('coupon_no', 'trade_tid'),
                       ('coupon_type', 'ufrom'),
                       ('extras', ))
        }),
    )

    list_display = ('id', 'title', "customer_id", "uniq_id", 'finished_time', 'expires_time')

    list_filter = ('coupon_type', )
    search_fields = ['=id', '=template_id']
    date_hierarchy = 'created'


admin.site.register(UserCoupon, UserCouponAdmin)


class TmpShareCouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile', 'share_coupon_id', 'status')

    list_filter = ('created', )
    search_fields = ['=id', '=mobile', '=share_coupon_id']
    date_hierarchy = 'created'


admin.site.register(TmpShareCoupon, TmpShareCouponAdmin)
