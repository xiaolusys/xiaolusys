# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse

from .models import JimayAgent, JimayAgentOrder

from shopapp.weixin.models.base import WeixinQRcodeTemplate
from shopapp.weixin.tasks import task_generate_colorful_qrcode

@admin.register(JimayAgent)
class JimayAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'name', 'mobile', 'weixin', 'level', 'parent_agent_link', 'manager', 'modified')
    list_filter = ('level', 'created', 'manager')
    search_fields = ['=id', '=mobile', '=name', '=weixin']

    def parent_agent_link(self, obj):
        if obj.parent_agent_id > 0:
            agent = JimayAgent.objects.filter(id=obj.parent_agent_id).first()
            return '%s(%s)' % (agent and agent.name, agent and agent.id)
        return 0

    parent_agent_link.short_description = '父极代理名称'

    def action_create_certification(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, '一次只能操作一条记录!', level=messages.WARNING)
            return

        agent = queryset.first()
        cert_qr = WeixinQRcodeTemplate.get_agent_cert_templates().first()
        if not cert_qr:
            self.message_user(request, '请先创建证书模板!!!', level=messages.WARNING)
            return

        params = json.loads(cert_qr.params)
        params['texts'][0]['content'] = agent.name
        params['texts'][1]['content'] = agent.idcard_no
        params['texts'][2]['content'] = agent.weixin

        qrcode_task = task_generate_colorful_qrcode.delay(params)
        media_value = qrcode_task.get()
        response = HttpResponse(media_value, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="phone-{name}-id-{id}-{date}.jpg"'.format(
            name=agent.mobile, id=agent.id, date=agent.modified.strftime('%Y%m%d')
        )
        return response

    action_create_certification.short_description = "创建授权证书"
    actions = ['action_create_certification']


@admin.register(JimayAgentOrder)
class JimayAgentOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_no', 'buyer', 'title', 'num', 'total_fee', 'payment', 'address_link', 'status', 'manager', 'pay_time', 'created')
    list_filter = ('status', 'created')
    search_fields = ['=id', '=order_no', '=buyer_id']
    list_per_page = 20
    readonly_fields = ['buyer', 'address']

    def address_link(self, obj):
        ud = obj.address
        return '<a href="/admin/pay/useraddress/{}">{}/{}/{}</a>'.format(
            ud.id, ud.receiver_name, ud.receiver_state, ud.receiver_city)

    address_link.allow_tags = True
    address_link.short_description = '收货人/省/市'

    def get_form(self, request, obj=None, **kwargs):
        form = super(JimayAgentOrderAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj:
            from django.contrib.auth.models import User
            form.base_fields['manager'].queryset = User.objects.filter(is_staff=True, groups__name=u'小鹿推广员')
        return form

