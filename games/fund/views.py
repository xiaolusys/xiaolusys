# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

from django.views.generic import View
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import authenticate, login

from core.weixin.mixins import WeixinAuthMixin
from shopapp.weixin.models import WeiXinAccount
from flashsale.pay.models import Customer

from shopapp.weixin.apis.wxpubsdk import WeiXinAPI
from .models import FundBuyerAccount, FundNotifyMsg

class FundAccountMgrView(WeixinAuthMixin, View):

    def get(self, request):
        app_key = settings.WX_HGT_APPID
        self.set_appid_and_secret(app_key, WeiXinAccount.get_wxpub_account_secret(app_key))

        openid, unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(openid) or not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        data = {
            'is_valid': False,
            'customer': None,
            'notify_msg': None,
            'fund_ac': None,
            'unionid': unionid,
            'openid': openid
        }

        dj_user, state  = DjangoUser.objects.get_or_create(username=unionid)
        customer = Customer.objects.filter(user=dj_user, unionid=unionid).first()
        if not customer:
            customer, state = Customer.objects.get_or_create(user=dj_user, unionid=unionid)

        if customer:
            data.update({'is_valid': True})
            data.update({'customer': customer})
            fund_ac = FundBuyerAccount.objects.filter(customer_id=customer.id).first()
            if fund_ac:
                notify_data = fund_ac.get_live_notify_data()

                notify_obj = FundNotifyMsg.objects.create(
                    fund_buyer=fund_ac,
                    send_data=notify_data,
                    send_type=FundNotifyMsg.CLICK_SEND,
                )

                # wx_api = WeiXinAPI()
                # wx_api.setAccountId(appKey=settings.WX_HGT_APPID)

                notify_msg = notify_obj.get_notify_message()
                # # 发送客服消息
                # wx_api.send_custom_message(
                #     {
                #         "touser": fund_ac.openid,
                #         "msgtype": "text",
                #         "text": {"content": notify_msg}
                #     })
                #
                # notify_obj.confirm_send()

                data.update({'fund_ac':fund_ac, 'notify_msg': notify_msg})

        response = render(
            request,
            "fund/applyfund.html",
            data,
        )

        # login(request, dj_user)
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

    def post(self, request):

        content = request.POST
        mobile  = content.get('mobile')
        openid  = content.get('openid')
        unionid = content.get('unionid')

        dj_user = get_object_or_404(DjangoUser, username=unionid)
        customer = get_object_or_404(Customer, user=dj_user ,unionid=unionid)

        fund_ac  = FundBuyerAccount.objects.create(
            customer_id=customer.id,
            mobile=mobile,
            openid=openid,
            status=FundBuyerAccount.APPLYING
        )

        data = {
            'is_valid': False,
            'customer': customer,
            'notify_msg': None,
            'fund_ac': fund_ac
        }

        response = render(
            request,
            "fund/applyfund.html",
            data,
        )

        return response

