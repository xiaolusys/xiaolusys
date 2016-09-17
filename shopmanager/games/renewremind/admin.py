# coding=utf-8
import datetime
from django.contrib import admin
from django.shortcuts import redirect
from games.renewremind.models import RenewRemind
import constants


class RenewRemindAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_name', 'service_provider', 'start_service_time',
                    'expire_time', 'principal', 'is_trace')

    search_fields = ('project_name', 'service_provider', 'principal')
    list_filter = ['principal', 'is_trace', 'expire_time']

    def renew_a_sevice(self, request, queryset):
        """ 更新一个服务续费记录 """
        origin_url = request.get_full_path()
        if queryset.count() > 1:
            self.message_user(request, u'超过一个服务,不予更新!')
            return redirect(origin_url)
        renew_remind = queryset[0]
        if not renew_remind.is_trace:
            self.message_user(request, u'非跟踪记录,不予更新!')
            return redirect(origin_url)
        now = datetime.datetime.now()
        now_after = now + datetime.timedelta(days=constants.REMIND_BEFOREHAND_DAYS)  # 60天后的时间
        if renew_remind.expire_time > now_after:  # 过早更新不允许
            self.message_user(request, u'过早更新(提前超过60天了),不予更新!')
            return redirect(origin_url)
        # 将被更新的记录去除追踪标记
        renew_remind.is_trace = False
        renew_remind.save()

        # 生成新的记录用于新的追踪
        self.message_user(request, u'请手动更新服务截止时间,并填写续费金额!')
        renew_remind.pk = None
        renew_remind.is_trace = True
        renew_remind.save()
        origin_url = '/admin/renewremind/renewremind/{0}'.format(renew_remind.id)
        return redirect(origin_url)

    renew_a_sevice.short_description = u'更新付费记录'
    actions = ['renew_a_sevice', ]


admin.site.register(RenewRemind, RenewRemindAdmin)

