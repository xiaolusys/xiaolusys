# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import JimayAgent, JimayAgentOrder, JimayAgentStat
from flashsale.pay.models import UserAddress
from shopapp.weixin.models.base import WeixinQRcodeTemplate
from shopapp.weixin.tasks import task_generate_colorful_qrcode

@admin.register(JimayAgent)
class JimayAgentAdmin(admin.ModelAdmin):
    list_display = ('id','agent_link', 'parent_agent_link', 'nick', 'name', 'mobile', 'weixin', 'level',
                    'manager', 'modified', 'direct_invite_num', 'indirect_invite_num')
    list_filter = ('level', 'created', 'manager')
    search_fields = ['=id', '=mobile', '=parent_agent_id', '=weixin']
    list_per_page = 25

    def agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.id, obj.id)

    agent_link.allow_tags = True
    agent_link.short_description = '代理链接'

    def parent_agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.parent_agent_id, obj.parent_agent_id)

    parent_agent_link.allow_tags =True
    parent_agent_link.short_description = '父级代理链接'

    def direct_invite_num(self, obj):
        return obj.agent_stat.direct_invite_num

    direct_invite_num.short_description = '直接邀请数'

    def indirect_invite_num(self, obj):
        return obj.agent_stat.indirect_invite_num

    indirect_invite_num.short_description = '间接邀请数'

    def agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.id, obj.id)

    agent_link.allow_tags = True
    agent_link.short_description = '代理链接'

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


class JimayAgentOrderForm(forms.ModelForm):
    sys_memo =  forms.CharField(label='备注', required=False, widget=forms.Textarea(attrs={'size': '40'}))
    manager  = forms.ModelChoiceField(
        label='管理员',
        queryset=User.objects.filter(is_staff=True, groups__name=u'小鹿推广员')
    )

    class Meta:
        model = JimayAgentOrder
        fields = '__all__'


@admin.register(JimayAgentOrder)
class JimayAgentOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_no', 'buyer', 'title', 'num', 'total_fee', 'payment', 'address_link', 'status', 'manager', 'pay_time', 'created')
    list_filter = ('status', 'created')
    search_fields = ['=id', '=order_no', '=buyer_id']
    list_per_page = 20
    readonly_fields = ['buyer', 'address']

    form = JimayAgentOrderForm
    # -------------- 页面布局 --------------
    fieldsets = (
        (u'订单基本信息:', {
            'classes': ('expand',),
            'fields': (
                ('order_no', 'title'),
                ('model_id', 'sku_id', 'num', ),
                ('status', 'sys_memo'),
                ('buyer','address',)
            )
        }),
        (u'运营审核:', {
            'classes': ('expand',),
            'fields': (('total_fee', 'payment', 'manager', 'ensure_time',),)
        }),
        (u'财务审核:', {
            'classes': ('expand',),
            'fields': (('pay_time',),)
        }),
        (u'仓库审核:', {
            'classes': ('expand',),
            'fields': (('logistic', 'logistic_no', 'send_time'),)
        }),
    )

    def address_link(self, obj):
        ud = obj.address
        return '<a href="/admin/pay/useraddress/{}">{}/{}/{}</a>'.format(
            ud.id, ud.receiver_name, ud.receiver_state, ud.receiver_city)

    address_link.allow_tags = True
    address_link.short_description = '收货人/省/市'

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super(JimayAgentOrderAdmin, self).get_form(request, obj=obj, **kwargs)
    #     if obj:
    #
    #         form.base_fields['manager'].queryset =
    #     return form

@admin.register(JimayAgentStat)
class JimayAgentStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'direct_invite_num', 'indirect_invite_num', 'direct_sales', 'indirect_sales', 'modified')
    list_filter = ('agent__level', 'modified',)
    search_fields = ['=agent']

