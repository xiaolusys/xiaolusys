# coding:utf-8
__author__ = 'yan.huang'
from django.contrib import admin
from django.http import HttpResponseRedirect
from core.admin import BaseModelAdmin
from .models import Complain


class ComplainAdmin(BaseModelAdmin):
    search_fields = ['id', 'user_id']
    list_display = ('id', 'com_type', 'insider_link', 'com_title', 'com_content', 'contact_way', 'created_time',
                    'status', 'custom_serviced', 'reply', 'reply_time_str', 'selfactions')
    list_filter = ['created_time', 'status', 'com_type', 'custom_serviced']
    ordering = ['-created_time']
    actions = ['set_complains_closed']

    class Media:
        css = {"all": ()}

    detail_view = BaseModelAdmin.change_view

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'用户投诉'}
        return self.detailform_view(request, object_id, form_url, extra_context)

    def selfactions(self, obj):
        if obj.status == Complain.CREATED:
            return '''<button type="button" id="respond_{complain_id}" class="respond">回复</button><button type="button" id="close_{complain_id}" class="complain_close">关闭</button>'''.format(
                complain_id=obj.id)
        return ''

    selfactions.allow_tags = True
    selfactions.short_description = u'操作'

    def insider_link(self, obj):
        return '<a href="/admin/users/customer/?id={user_id}" target="_blank">{user_id}</a>'.format(**{
            'user_id': obj.user_id})

    insider_link.allow_tags = True
    insider_link.short_description = u'投诉人'

    def reply_time_str(self, obj):
        return obj.reply_time.strftime('%Y%m%d %H:%M:%S') if obj.reply_time else ''

    reply_time_str.short_description = u'回复时间'

    # 批量关闭
    def set_complains_closed(self, request, queryset):
        for p in queryset:
            if p.status == Complain.CREATED:
                p.status = Complain.CLOSED
                p.save()
        return HttpResponseRedirect(request.get_full_path())

    set_complains_closed.short_description = u'批量关闭'


admin.site.register(Complain, ComplainAdmin)
