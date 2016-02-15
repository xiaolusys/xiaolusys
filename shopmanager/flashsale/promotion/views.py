# -*- coding:utf8 -*-
import datetime
import re
from shopapp.weixin.views import get_user_openid, valid_openid
from django.views.generic import View
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
import random
from .models_freesample import XLSampleApply, XLFreeSample, XLSampleSku
from .models import XLInviteCode
from django.http import HttpResponse
import json
from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.models import Customer


def genCode():
    NUM_CHAR_LIST = list('1234567890')
    return ''.join(random.sample(NUM_CHAR_LIST, 7))


class XLSampleapplyView(View):
    xlsampleapply = 'promotion/xlsampleapply.html'

    vipcode_default_message = u'请输入邀请码'
    vipcode_error_message = u'邀请码不正确'
    mobile_default_message = u'请输入手机号'
    mobile_error_message = u'手机号码有误'

    PLANTFORM = ('wxapp', 'pyq', 'qq', 'txwb', 'web')
    free_pro = 1

    def get(self, request):
        content = request.REQUEST
        vipcode = content.get('vipcode', None)  # 获取分享用户　用来记录分享状况
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        from_customer = content.get('from_customer', 0)  # 分享人的用户id
        if "MicroMessenger" in agent:  # 如果是在微信里面
            weixi = WeixinAuthMixin()
            openid, unionid = weixi.get_openid_and_unionid(request)  # 获取用户的openid, unionid
            if not weixi.valid_openid(openid):  # 若果是无效的openid则跳转到授权页面
                return redirect(weixi.get_wxauth_redirct_url(request))

        # 商品sku信息  # 获取商品信息到页面
        xlsample = XLFreeSample.objects.get(id=self.free_pro)
        skus = XLSampleSku.objects.filter(sample_product=xlsample)
        response = render_to_response(self.xlsampleapply,
                                      {"vipcode": vipcode, 'from_customer': from_customer,
                                       "xlsample": xlsample,
                                       "skus": skus, "option_length": skus.count(),
                                       "mobile_message": self.mobile_default_message},
                                      context_instance=RequestContext(request))
        return response

    def post(self, request):
        content = request.REQUEST
        vmobile = content.get("mobile", None)  # 参与活动的手机号
        vipcode = content.get("vipcode", None)  # 活动邀请码
        from_customer = content.get('from_customer', 0)  # 分享人的用户id

        sku_code = content.get("sku_code", None)  # 产品sku码
        ufrom = content.get("ufrom", None)
        openid = None
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        if "MicroMessenger" in agent:  # 如果是在微信里面
            weixi = WeixinAuthMixin()
            openid, unionid = weixi.get_openid_and_unionid(request)  # 获取用户的openid, unionid
            if not weixi.valid_openid(openid):  # 若果是无效的openid则跳转到授权页面
                return redirect(weixi.get_wxauth_redirct_url(request))

        xlsample = XLFreeSample.objects.get(id=self.free_pro)
        skus = XLSampleSku.objects.filter(sample_product=xlsample)

        regex = re.compile(r'^1[34578]\d{9}$', re.IGNORECASE)
        mobiles = re.findall(regex, vmobile)
        mobile = mobiles[0] if len(mobiles) >= 1 else None
        if mobile:
            custs = Customer.objects.filter(id=from_customer)  # 用户是否存在
            cust = custs[0] if custs.exists() else ''
            if cust:  # 用户存在则计数
                participates = XLInviteCode.objects.filter(mobile=cust.mobile)
                if participates.exists():
                    participate = participates[0]
                    participate.usage_count += 1
                    participate.save()  # 使用次数累加

            url = '/sale/promotion/appdownload/?vipcode={0}&from_customer={1}'.format(vipcode, from_customer)
            xls = XLSampleApply.objects.filter(outer_id=xlsample.outer_id, mobile=mobile)  # 记录来自平台设申请的sku选项
            if not xls.exists():  # 如果没有申请记录则创建记录
                sku_code_r = '' if sku_code is None else sku_code
                sample_apply = XLSampleApply()
                sample_apply.outer_id = xlsample.outer_id
                sample_apply.mobile = mobile
                sample_apply.sku_code = sku_code_r
                sample_apply.vipcode = vipcode
                sample_apply.user_openid = openid
                sample_apply.from_customer = from_customer  # 保存分享人的客户id
                if ufrom in self.PLANTFORM:
                    sample_apply.ufrom = ufrom
                sample_apply.save()
            return redirect(url)  # 跳转到下载页面

        return render_to_response(self.xlsampleapply,
                                  {"vipcode": vipcode, "xlsample": xlsample, "skus": skus,
                                   "option_length": skus.count(),
                                   "mobile": vmobile,
                                   "mobile_message": self.mobile_error_message},
                                  context_instance=RequestContext(request))


class APPDownloadView(View):
    """ 下载页面 """
    download_page = 'promotion/download.html'

    def get(self, request):
        content = request.REQUEST
        vipcode = content.get("vipcode", None)  # 活动邀请码
        from_customer = content.get("from_customer", None)  # 分享人的用户id
        return render_to_response(self.download_page, {"vipcode": vipcode, "from_customer": from_customer},
                                  context_instance=RequestContext(request))
