# -*- coding:utf-8 -*-
from django.contrib import admin
from .models import APPFullPushMessge
import logging
from flashsale.xiaolumm import util_emoji
from django.contrib import messages
from flashsale.protocol.tasks import task_site_push

logger = logging.getLogger('django.request')


class APPFullPushMessgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_url', 'platform', 'desc', 'created', 'status')
    list_display_links = ('id', 'target_url',)
    search_fields = ['=id', ]
    list_filter = ('platform', 'status')
    list_per_page = 40

    # -------------- 页面布局 --------------
    fieldsets = (('基本信息:', {
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
                                ('result',))

                 }),)

    # def save_model(self, request, obj, form, change):
    # """
    # Given a model instance save it to the database.
    #     """
    #     try:
    #         from flashsale.push import mipush
    #         from flashsale.protocol import get_target_url
    #         resp = {}
    #         params = {'target_url': get_target_url(obj.target_url, obj.params)}
    #
    #         desc = util_emoji.match_emoji(obj.desc)
    #
    #         if obj.platform == APPFullPushMessge.PL_IOS:
    #             resp = mipush.mipush_of_ios.push_to_all(params, description=desc)
    #         else:
    #             resp = mipush.mipush_of_android.push_to_all(params, description=desc)
    #     except Exception, exc:
    #         logger.error(exc.message or 'app push error', exc_info=True)
    #         resp = {'error': exc.message}
    #     success = resp.get('result')
    #     if success and success.lower() == 'ok':
    #         obj.status = APPFullPushMessge.SUCCESS
    #         self.message_user(request, u"=======, %s用户全推成功." % obj.get_platform_display())
    #     else:
    #         self.message_user(request, u"xxxxxxx 很抱歉,%s用户全推失败!xxxxxxxx" % obj.get_platform_display())
    #     obj.result = resp
    #     obj.save()

    def push_action(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset[0]
            if not obj.push_time:
                return self.message_user(request, u'没有设置推送时间前不予手动推送', level=messages.WARNING)
            try:
                task_site_push.delay(obj)
                return self.message_user(request, u'推送成功')
            except Exception, exc:
                logger.error(exc.message or 'Site push error', exc_info=True)
                resp = {'error': exc.message}
                obj.result = resp
                obj.save()

        return self.message_user(request, u'勾选一个推送项', level=messages.WARNING)

    push_action.short_description = u'站点推送'
    actions = ['push_action', ]


admin.site.register(APPFullPushMessge, APPFullPushMessgeAdmin)
