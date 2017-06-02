# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse

from .models import JimayAgent

from shopapp.weixin.models.base import WeixinQRcodeTemplate
from shopapp.weixin.utils import generate_colorful_qrcode

@admin.register(JimayAgent)
class JimayAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'name', 'mobile', 'weixin', 'level', 'parent_agent_id', 'modified')
    list_filter = ('level', 'created')
    search_fields = ['=id', '=mobile', '=name', '=weixin']

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

        media_stream = generate_colorful_qrcode(params)
        response = HttpResponse(media_stream.getvalue(), content_type='application/octet-stream')
        media_stream.close()
        response['Content-Disposition'] = 'attachment; filename=cf-{name}-{id}-{date}.csv'.format(
            name=agent.name, id=agent.id, date=agent.modified.strftime('%Y%m%d')
        )
        return response

    action_create_certification.short_description = "创建授权证书"
    actions = ['action_create_certification']