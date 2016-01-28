# -*- coding:utf8 -*-
import datetime
from shopapp.weixin.views import get_user_openid, valid_openid
from django.views.generic import View
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
import random
from .models_freesample import XLSampleApply, XLFreeSample, XLSampleSku
from .models import XLInviteCode
from django.http import HttpResponse
import json


def genCode():
    NUM_CHAR_LIST = list('1234567890')
    return ''.join(random.sample(NUM_CHAR_LIST, 7))


class XLSampleapplyView(View):
    weixin_authentic_url = "https://open.weixin.qq.com/connect/oauth2/authorize" \
                           "?appid=wxc2848fa1e1aa94b5" \
                           "&redirect_uri=http://m.xiaolumeimei.com/weixin/freesamples/" \
                           "&response_type=code" \
                           "&scope=snsapi_base" \
                           "&state=135#wechat_redirect"
    xlsampleapply = 'promotion/xlsampleapply.html'

    vipcode_default_message = u'请输入邀请码'
    vipcode_error_message = u'邀请码不正确'
    vipcode_none_message = u'邀请码不能为空'
    mobile_default_message = u'请输入手机号码'
    mobile_error_message = u'手机号码有误'

    free_pro = 1

    def get(self, request):
        content = request.REQUEST
        vipcode = content.get('vipcode', None)  # 获取分享用户　用来记录分享状况

        # 测试用户的openid 则开始
        # started = True if user_openid in ('oMt59uE55lLOV2KS6vYZ_d0dOl5c', 'oMt59uJJBoNRC7Fdv1b5XiOAngdU') else False

        # 商品sku信息  # 获取商品信息到页面
        xlsample = XLFreeSample.objects.get(id=self.free_pro)
        zl_aku = XLSampleSku.objects.get(sample_product=xlsample)
        response = render_to_response(self.xlsampleapply,
                                      {"vipcode": vipcode, "xlsample": xlsample, "zl_aku": zl_aku,
                                       "vipcode_message": self.vipcode_default_message,
                                       "mobile_message": self.mobile_default_message},
                                      context_instance=RequestContext(request))
        return response

    def post(self, request):
        content = request.REQUEST
        mobile = content.get("mobile", None)  # 参与活动的手机号
        vipcode = content.get("vipcode", None)  # 活动邀请码

        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        if "MicroMessenger" in agent:  # 如果是在微信里面
            code = content.get('code', None)  # 微信返回的用户的code信息
            user_openid = get_user_openid(request, code)  # 获取用户的openid
            if not valid_openid(user_openid):  # 若果是无效的openid则跳转到授权页面
                return redirect(self.weixin_authentic_url)
        xlsample = XLFreeSample.objects.get(id=self.free_pro)
        zl_aku = XLSampleSku.objects.get(sample_product=xlsample)
        if vipcode not in ('None', None):  # 如果有邀请码　则提取邀请码　参与记录
            try:
                # participates = XLInviteCode.objects.get(vipcode=vipcode)  # 验证邀请码是否存在
                url = '/sale/promotion/appdownload/'
                return redirect(url)  # 跳转到下载页面
            except Exception, exc:
                return render_to_response(self.xlsampleapply,
                                          {"vipcode": vipcode, "xlsample": xlsample, "zl_aku": zl_aku,
                                           'vipcode_message': self.vipcode_error_message,
                                           "mobile_message": self.mobile_error_message},
                                          context_instance=RequestContext(request))
        return render_to_response(self.xlsampleapply,
                                  {"vipcode": vipcode, "xlsample": xlsample, "zl_aku": zl_aku,
                                   'vipcode_message': self.vipcode_default_message,
                                   "mobile_message": self.mobile_default_message},
                                  context_instance=RequestContext(request))


class APPDownloadView(View):
    """ 下载页面 """
    download_page = 'promotion/download.html'

    def get(self, request):
        return render_to_response(self.download_page, {}, context_instance=RequestContext(request))


class ActivationShareView(View):
    """ 申请使用提交 """
    active_share_page = 'promotion/activation_share.html'
    vipcode_default_message = u'请输入邀请码'
    vipcode_error_message = u'邀请码不正确'
    free_pro = 1

    def get(self, request):
        xlsample = XLFreeSample.objects.get(id=self.free_pro)  # 免费申请商品
        zl_aku = XLSampleSku.objects.get(sample_product=xlsample)
        return render_to_response(self.active_share_page,
                                  {"xlsample": xlsample, "zl_aku": zl_aku,
                                   'vipcode_message': self.vipcode_default_message},
                                  context_instance=RequestContext(request))

    def post(self, request):
        content = request.REQUEST
        mobile = content.get("mobile", None)  # 参与活动的手机号　app 中获取
        vipcode = content.get("vipcode", None)  # 活动邀请码

        xlsample = XLFreeSample.objects.get(id=self.free_pro)  # 免费申请商品
        zl_aku = XLSampleSku.objects.get(sample_product=xlsample)

        try:
            # participates = XLInviteCode.objects.get(vipcode=vipcode)  # 验证邀请码是否存在
            # 给邀请人记录邀请结果
            pass
        except Exception, exc:
            return render_to_response(self.active_share_page,
                                      {"xlsample": xlsample, "zl_aku": zl_aku,
                                       'vipcode_message': self.vipcode_error_message},
                                      context_instance=RequestContext(request))
        share_link = '1234'  # 生成自己的邀请码
        promotion_passed = True
        return render_to_response(self.active_share_page,
                                  {"xlsample": xlsample, "zl_aku": zl_aku,
                                   "share_link": share_link, "promotion_passed": promotion_passed,
                                   'vipcode_message': self.vipcode_default_message},
                                  context_instance=RequestContext(request))
