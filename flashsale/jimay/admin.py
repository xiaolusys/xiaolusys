# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import JimayAgent, JimayAgentOrder, JimayAgentStat
from flashsale.pay.models import UserAddress, Customer
from shopapp.weixin.models.base import WeixinQRcodeTemplate
from shopapp.weixin.tasks import task_generate_colorful_qrcode
from .filters import AgentInviteCountFieldListFilter


@admin.register(JimayAgent)
class JimayAgentAdmin(admin.ModelAdmin):
    list_display = ('id','agent_link', 'parent_agent_link', 'customer_label', 'nick', 'name', 'mobile', 'weixin', 'level',
                    'manager', 'is_graduated', 'modified', 'invite_num', 'sale_num_and_amount')
    list_filter = ('level', 'created', 'manager', 'is_graduated', ('unionid', AgentInviteCountFieldListFilter)) # unionid只是用来做媒介
    search_fields = ['=id', '=mobile', '=parent_agent_id', '=weixin', 'nick', 'name']
    list_per_page = 25

    def agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.id, obj.id)

    agent_link.allow_tags = True
    agent_link.short_description = '代理链接'

    def parent_agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.parent_agent_id, obj.parent_agent_id)

    parent_agent_link.allow_tags =True
    parent_agent_link.short_description = '父级代理链接'

    def invite_num(self, obj):
        return '%s / %s'%(obj.agent_stat.direct_invite_num, obj.agent_stat.indirect_invite_num)

    invite_num.short_description = '直接/间接邀请数'

    def sale_num_and_amount(self, obj):
        return '%s / %.2f' % (obj.agent_stat.direct_salenum, obj.agent_stat.direct_sales * 0.01)

    sale_num_and_amount.short_description = '销售数量/销售额(元)'

    def customer_label(self, obj):
        customer = obj.buyer
        return customer and customer.id or 0

    customer_label.short_description = '用户ID'

    def agent_link(self, obj):
        return '<a href="/admin/jimay/jimayagent/?q=%s">%s &gt;&gt;</a>' % (obj.id, obj.id)

    agent_link.allow_tags = True
    agent_link.short_description = '代理链接'

    def action_create_agent_certification(self, request, queryset):
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
        response['Content-Disposition'] = 'attachment; filename="agent-phone-{name}-id-{id}-{date}.jpg"'.format(
            name=agent.mobile, id=agent.id, date=agent.modified.strftime('%Y%m%d')
        )
        return response

    action_create_agent_certification.short_description = "创建授权证书"

    def action_create_award_certification(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, '一次只能操作一条记录!', level=messages.WARNING)
            return

        agent = queryset.first()
        cert_qr = WeixinQRcodeTemplate.get_agent_award_templates().first()
        if not cert_qr:
            self.message_user(request, '请先创建证书模板!!!', level=messages.WARNING)
            return

        if not agent.is_graduated:
            self.message_user(request, '请修改该学员结业状态及结业时间', level=messages.WARNING)
            return

        start_time = agent.time_graduated_st
        start_end = agent.time_graduated_en

        params = json.loads(cert_qr.params)
        params['texts'][0]['content'] = agent.name
        params['texts'][1]['content'] = str(start_time.year)
        params['texts'][2]['content'] = str(start_time.month)
        params['texts'][3]['content'] = str(start_time.day)
        params['texts'][4]['content'] = str(start_end.month)
        params['texts'][5]['content'] = str(start_end.day)

        qrcode_task = task_generate_colorful_qrcode.delay(params)
        media_value = qrcode_task.get()
        response = HttpResponse(media_value, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="award-phone-{name}-id-{id}-{date}.jpg"'.format(
            name=agent.mobile, id=agent.id, date=agent.modified.strftime('%Y%m%d')
        )
        return response

    action_create_award_certification.short_description = "创建结业证书"

    actions = ['action_create_agent_certification', 'action_create_award_certification']


class JimayAgentOrderForm(forms.ModelForm):
    total_fee = forms.FloatField(label=u'订单原价(元)', min_value=0)
    payment  = forms.FloatField(
        label=u'支付金额(元)', min_value=0,
        help_text="""
            [进货价]
            特约：98元/组
            市级：84元/组
            省级：72元/组
            [运费](一箱等于60组)
            江浙沪皖：10元/盒,30元/箱
            甘肃、宁夏、内蒙、青海：30元/盒,150元/箱
            新疆、西藏：60元/盒,300元/箱
            其它地区(如广州、北京、福建)：20元/盒,90元/箱
        """)
    sys_memo =  forms.CharField(label='备注', required=False, widget=forms.Textarea(attrs={'size': '40'}))
    manager  = forms.ModelChoiceField(
        label='管理员',
        queryset=User.objects.filter(is_staff=True, groups__name=u'小鹿推广员')
    )

    class Meta:
        model = JimayAgentOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(JimayAgentOrderForm, self).__init__(*args, **kwargs)
        self.initial['total_fee'] = self.instance.total_fee * 0.01
        self.initial['payment']   = self.instance.payment * 0.01

    def clean_total_fee(self):
        return int(self.cleaned_data['total_fee'] * 100)

    def clean_payment(self):
        return int(self.cleaned_data['payment'] * 100)


@admin.register(JimayAgentOrder)
class JimayAgentOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_no', 'agent_mobile_label', 'title', 'num', 'total_fee_label', 'payment_label', 'address_link', 'status',
                    'manager', 'pay_time', 'channel', 'created')
    list_filter = ('status', 'channel', 'created')
    search_fields = ['=id', '=order_no', '=buyer__id']
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
            'fields': (('payment',),
                       ('total_fee', 'manager', 'ensure_time'),)
        }),
        (u'财务审核:', {
            'classes': ('expand',),
            'fields': (('pay_time', 'channel'),)
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

    def total_fee_label(self, obj):
        return obj.total_fee * 0.01

    total_fee_label.short_description = '标准售价'

    def payment_label(self, obj):
        return obj.payment * 0.01

    payment_label.so = '实际支付'
    payment_label.short_description = '实际支付'

    def agent_mobile_label(self, obj):
        agent = JimayAgent.objects.filter(mobile=obj.buyer.mobile).first()
        return '%s / %s' % (obj.buyer.mobile, agent and agent.nick)

    agent_mobile_label.short_description = '代理信息'

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super(JimayAgentOrderAdmin, self).get_form(request, obj=obj, **kwargs)
    #     if obj:
    #
    #         form.base_fields['manager'].queryset =
    #     return form

@admin.register(JimayAgentStat)
class JimayAgentStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'direct_invite_num', 'indirect_invite_num', 'direct_salenum', 'direct_sales', 'modified')
    list_filter = ('agent__level', 'modified',)
    search_fields = ['=agent']

