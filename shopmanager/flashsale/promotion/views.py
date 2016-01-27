# -*- coding:utf8 -*-
import datetime
from shopapp.weixin.views import get_user_openid, valid_openid
from django.views.generic import View
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
import random


def genCode():
    NUM_CHAR_LIST = list('1234567890')
    return ''.join(random.sample(NUM_CHAR_LIST, 7))


class FreeSampleView(View):
    weixin_authentic_url = "https://open.weixin.qq.com/connect/oauth2/authorize" \
                           "?appid=wxc2848fa1e1aa94b5" \
                           "&redirect_uri=http://m.xiaolumeimei.com/weixin/freesamples/" \
                           "&response_type=code" \
                           "&scope=snsapi_base" \
                           "&state=135#wechat_redirect"
    start_page = 'active/freetrial.html'
    activation_share_page = 'active/activation_share.html'

    def record_share_customer_log(self, share_customer, participant_phone):
        # 记录被分享人的手机号码到分享人的分享结果中
        activity = Activities.objects.get(id=1)
        participations = Participation.objects.filter(weixinid=share_customer, activity=activity)  # 参与记录
        if participations.exists():
            participation = participations[0]
            ParticipateDetail.objects.create(participation=participation.id, verify_phone=participant_phone)  # 参与记录的明细
        return

    def get(self, request):
        content = request.REQUEST
        code = content.get('code')  # 微信返回的用户的code信息
        share_customer = content.get('share_customer', None)  # 获取分享用户　用来记录分享状况
        user_openid = get_user_openid(request, code)  # 获取用户的openid
        if not valid_openid(user_openid):  # 若果是无效的openid则跳转到授权页面
            return redirect(self.weixin_authentic_url)
        wx_user, state = WeiXinUser.objects.get_or_create(openid=user_openid)  # 创建获取微信用户

        activity = Activities.objects.get(id=1)
        # 查看同一活动是否有参加　如果  有参与  返回跳转到下载页面并返回APP激活码
        participations = Participation.objects.filter(weixinid=wx_user.id, activity=activity.id)
        if participations.exists():
            participation = participations[0]
            share_link = request.path + '?share_customer={0}'.format(participation.weixinid)
            alredy_dic = {"share_customer": participation.weixinid, "activation_code": participation.activation_code,
                          "participant_phone": participation.phone_no, "share_link": share_link}
            return render_to_response(self.activation_share_page, alredy_dic, context_instance=RequestContext(request))

        # 测试用户的openid 则开始
        started = True if user_openid in ('oMt59uE55lLOV2KS6vYZ_d0dOl5c', 'oMt59uJJBoNRC7Fdv1b5XiOAngdU') else False

        response = render_to_response(self.start_page,
                                      {"wx_user": wx_user, "share_customer": share_customer},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid", user_openid)
        return response

    def record_user_participate(self, wx_user, participant_phone, activation_code):
        # 生成自己对APP活动的激活码  参与APP活动的时候激活　参与活动的手机号码的激活码并保存到数据库中用来激活时候匹配
        activity = Activities.objects.get(id=1)
        participation, state = Participation.objects.get_or_create(weixinid=wx_user.id, activity=activity.id)
        participation.phone_no = participant_phone
        participation.activation_code = activation_code  # 邀请码用来激活
        participation.save()
        return participation

    def post(self, request):
        content = request.REQUEST
        share_customer = content.get('share_customer', None)  # 获取分享用户　有则记录分享用户的分享记录
        participant_phone = content.get("participant_phone", None)  # 参与活动的手机号
        activation_code = content.get("activation_code", None)  # 活动邀请码
        code = content.get('code')  # 微信返回的用户的code信息

        user_openid = get_user_openid(request, code)  # 获取用户的openid
        if not valid_openid(user_openid):  # 若果是无效的openid则跳转到授权页面
            return redirect(self.weixin_authentic_url)

        if activation_code not in ('None', None):  # 如果有邀请码　则提取邀请码　参与记录
            participates = Participation.objects.filter(activation_code=activation_code)
            if participates.exists():
                share_customer = participates[0].weixinid  # 有邀请的时候分享人就是邀请码对应的人
            else:  # 返回提示页面　邀请码不存在
                pass

        wx_user, state = WeiXinUser.objects.get_or_create(openid=user_openid)  # 创建获取微信用户
        print "wx_user: ", wx_user
        if share_customer not in ('None', None):  # 如果有分享人
            self.record_share_customer_log(share_customer, participant_phone)  # 记录被分享人的手机号码　到　分享人的分享结果中
        else:
            share_customer = wx_user.id  # 如果是空则返回当前微信用户为分享者

        # 生成用户自己的邀请码邀请码
        activation_code = genCode()

        # 记录参与活动的用户信息
        participation = self.record_user_participate(wx_user, participant_phone, str(activation_code))

        # 同时生成邀请的二维码带上自己的身份id
        share_link = request.path + '?share_customer={0}'.format(share_customer)
        dic = {"share_customer": share_customer, "activation_code": participation.activation_code,
               "share_link": share_link, "participant_phone": participant_phone}
        return render_to_response(self.activation_share_page, dic, context_instance=RequestContext(request))


class ActiveAction(View):
    """ 页面点击激活跳转到下载页面 """
    download_page = 'active/download.html'

    def get(self, request):
        return render_to_response(self.download_page, {}, context_instance=RequestContext(request))
