# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.contrib import messages

from .models import FundBuyerAccount, FundNotifyMsg

@admin.register(FundBuyerAccount)
class FundBuyerAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'buyer_name', 'mobile', 'buy_amount', 'settled_earned_profit', 'annual_yield_rate',
                    'total_buy_amount', 'text_current_profit', 'last_buy_date', 'valid_profit_days', 'total_buy_amount','total_earned_profit', 'created')
    list_filter = ('status','last_buy_date', 'created')
    search_fields = ['=id', '=buyer_name', '=mobile']
    readonly_fields = ['customer_id','mobile', 'openid']
    list_per_page = 100

    def text_current_profit(self, obj):
        return '%d'%(obj.settled_earned_profit + obj.buy_amount * obj.annual_yield_rate / 365 * obj.valid_profit_days * 0.01)

    text_current_profit.allow_tags = True
    text_current_profit.short_description = "当前总收益(新购前收益+新购后收益)"


@admin.register(FundNotifyMsg)
class FundNotifyMsgAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund_buyer', 'send_type', 'pre_send_message', 'is_send','send_time', 'created')
    list_filter = ('send_type', 'is_send', 'send_time', 'created')
    search_fields = ['=id', '=fund_buyer__mobile']
    list_per_page = 40


    def pre_send_message(self, obj):
        return u'''<pre>%s</pre>'''%obj.get_notify_message()

    pre_send_message.allow_tags = True
    pre_send_message.short_description = "消息内容"


    def action_send_mass_message(self,  request, queryset):
        from django.conf import settings
        from shopapp.weixin.apis.wxpubsdk import WeiXinAPI

        wx_api = WeiXinAPI()
        wx_api.setAccountId(appKey=settings.WX_HGT_APPID)

        for notify_obj in queryset:
            try:
                wx_api.send_mass_message(
                    {
                        "touser": [
                            notify_obj.fund_buyer.openid,  # 接口要求必须两个openid, 所以重复参数
                            notify_obj.fund_buyer.openid
                        ],
                        "msgtype": "text",
                        "text": {"content": notify_obj.get_notify_message()}
                    })

                notify_obj.confirm_send()

            except Exception, exc:
                self.message_user(request, exc.message, level=messages.ERROR)
                return

        self.message_user(request, '消息发送成功', level=messages.INFO)

        return

    action_send_mass_message.short_description = "确认发送消息给".decode('utf8')

    actions = ['action_send_mass_message']

