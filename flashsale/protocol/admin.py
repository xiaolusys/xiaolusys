# coding=utf-8
from django.contrib import admin
from .models import APPFullPushMessge
from django.contrib import messages

import logging

logger = logging.getLogger('django.request')


class APPFullPushMessgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_url', 'platform', 'desc', 'created', 'status')
    list_display_links = ('id', 'target_url',)
    search_fields = ['=id', ]
    list_filter = ('platform', 'status')
    list_per_page = 40

    # -------------- 页面布局 --------------
    fieldsets = (
        ('基本信息:', {
            'classes': ('expand',),
            'fields': (
                'target_url',
                'platform',
                'push_time',
                'desc'
            )
        }),
        ('内部信息:', {
            'classes': ('collapse',),
            'fields': (('cat', 'status', 'regid'),
                       ('params', 'result',))

        }),
    )

    def push_action(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset[0]
            from apis.v1.dailypush.apppushmsg import push_msg_right_now_by_id

            is_push = push_msg_right_now_by_id(obj.id)
            if is_push:
                return self.message_user(request, u'推送成功!')
            return self.message_user(request, u'推送失败!', level=messages.ERROR)
        return self.message_user(request, u'勾选一个推送项', level=messages.WARNING)

    push_action.short_description = u'站点推送'
    actions = ['push_action', ]


admin.site.register(APPFullPushMessge, APPFullPushMessgeAdmin)
