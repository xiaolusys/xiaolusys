# -*- encoding:utf-8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.template import RequestContext
from django.shortcuts import render

from shopback.base.authentication import login_required_ajax
from shopapp.weixin.views import WeiXinUser, VipCode, get_user_openid
from .models import WeixinUserPicture, WeixinUserAward, WeixinLinkShare
from .tasks import task_notify_referal_award
from shopapp.signals import weixin_referal_signal
from django.shortcuts import redirect


@csrf_exempt
@login_required_ajax
def picture_review(request):
    content = request.GET

    rows = WeixinUserPicture.objects.filter(id=content.get('pid')) \
        .update(status=WeixinUserPicture.COMPLETE)

    return HttpResponse(json.dumps({'code': (1, 0)[rows]}), content_type="application/json")


class AwardView(View):
    def post(self, request):
        content = request.POST
        user_openid = request.COOKIES.get('openid')
        select_val = content.get("select_val")
        try:
            wx_user = WeiXinUser.objects.get(openid=user_openid)
            referal_from_openid = wx_user.referal_from_openid

            wx_award, state = WeixinUserAward.objects.get_or_create(user_openid=user_openid)

            if not wx_award.is_receive:
                wx_award.is_receive = True
                wx_award.select_val = select_val
                wx_award.referal_from_openid = referal_from_openid
                wx_award.save()

                weixin_referal_signal.send(sender=WeixinUserAward,
                                           user_openid=user_openid,
                                           referal_from_openid=referal_from_openid)

                rep_json = {'success': True}
            else:
                wx_award.select_val = select_val
                wx_award.save()
                rep_json = {'success': True, 'msg': u'更新选择'}
        except:
            rep_json = {'success': False, 'err_msg': u'系统错误，请联系管理员'}

        return HttpResponse(json.dumps(rep_json), content_type="application/json")


class AwardNotifyView(View):
    def get(self, request):
        content = request.GET
        code = content.get('code')
        user_openid = get_user_openid(request, code)

        is_share = False
        my_awards = WeixinUserAward.objects.filter(user_openid=user_openid)
        if my_awards.count() > 0:
            is_share = my_awards[0].is_share

        response = render(
            request,
            'weixin/sales/gift.html',
              {'user_openid': user_openid, "is_share": is_share},
        )
        response.set_cookie("openid", user_openid)
        return response

    def post(self, request):

        content = request.POST
        award_val = content.get('award_val')
        user_openid = request.COOKIES.get('openid')
        notify_num = 0

        try:
            wx_award, state = WeixinUserAward.objects.get_or_create(user_openid=user_openid)

            if not wx_award.is_share:
                task_notify_referal_award.delay(user_openid)

                wx_award.is_share = True
                wx_award.award_val = award_val
                wx_award.remind_time = datetime.datetime.now()
                wx_award.remind_count = 0
                wx_award.save()

            wx_user = WeiXinUser.objects.get(openid=user_openid)
            return redirect("/weixin/sampleads/%s/" % wx_user.pk)
        except:
            rep_json = {'success': False, 'notify_num': 0}

            return HttpResponse(json.dumps(rep_json), content_type="application/json")


class AwardRemindView(View):
    def post(self, request):
        try:
            content = request.POST
            code = content.get('code')
            user_openid = get_user_openid(request, code)

            wx_user = WeiXinUser.objects.get(openid=user_openid)
            wx_award, state = WeixinUserAward.objects.get_or_create(user_openid=wx_user.referal_from_openid)

            wx_award.remind_count = F('remind_count') + 1
            wx_award.remind_time = datetime.datetime.now()
            wx_award.save()

            rep_json = {'success': True}
        except:
            rep_json = {'success': False}

        return HttpResponse(json.dumps(rep_json), content_type="application/json")


class AwardShareView(View):
    def get(self, request, *args, **kwargs):
        wx_user_pk = kwargs.get('pk', 0)
        users = WeiXinUser.objects.filter(pk=wx_user_pk)

        openid = request.COOKIES.get('openid')
        if openid == "" or openid == "None" or openid == None:
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://m.xiaolumeimei.com/weixin/freesamples/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)

        identical = False
        vipcode = 0
        nickname = ''
        if users.count() > 0:
            nickname = users[0].nickname
            referal_images = []
            referal_users = WeiXinUser.objects.filter(referal_from_openid=users[0].openid)
            for user in referal_users:
                referal_images.append(user.headimgurl)

            if users[0].vipcodes:
                vipcode = users[0].vipcodes.code
            else:
                vipcode = VipCode.objects.genVipCodeByWXUser(users[0])

            if users[0].openid == openid:
                identical = True

            response = render(
                request,
                'weixin/sales/share.html',
                  {"identical": identical, "vipcode": vipcode, "pk": wx_user_pk,
                   "nickname": nickname, "referal_images": referal_images},
            )
            return response

        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://m.xiaolumeimei.com/weixin/freesamples/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
        return redirect(redirect_url)


class AwardApplyView(View):
    def post(self, request):
        content = request.POST

        code = content.get('code')
        user_openid = get_user_openid(request, code)

        if user_openid == "" or user_openid == None or user_openid == "None":
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://xiaolu.so/weixin/freesamples/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)

        fcode = content.get("fcode")
        code_objects = VipCode.objects.filter(code=fcode)
        if code_objects.count() > 0:
            referal_from_openid = code_objects[0].owner_openid.openid

            if referal_from_openid != user_openid:
                wx_user, state = WeiXinUser.objects.get_or_create(openid=user_openid)
                wx_user.referal_from_openid = referal_from_openid
                wx_user.save()

                redirect_url = "/weixin/sales/award/share/%s/" % wx_user.pk
                return redirect(redirect_url)

        rep_json = {'code': 'error', "try this F code": "866988"}
        return HttpResponse(json.dumps(rep_json), content_type="application/json")


class LinkShareView(View):
    def post(self, request):
        content = request.POST

        user_openid = content.get('user_openid')
        share_type = content.get('share_type')
        share_link = content.get('share_link')

        wls = WeixinLinkShare.objects.create(user_openid=user_openid,
                                             link_url=share_link,
                                             link_type=share_type)

        return HttpResponse(json.dumps({"success": "ok"}), content_type="application/json")

    get = post
