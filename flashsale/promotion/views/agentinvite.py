# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import random
import hashlib
from django.views.generic import View
from django.http.response import HttpResponse
from django.contrib.auth.models import User
from flashsale.pay.models import Customer
from django.shortcuts import redirect, render
from django.db import transaction

from core.weixin.mixins import WeixinAuthMixin
from games.weixingroup.models import XiaoluAdministrator, GroupFans, GroupMamaAdministrator


class WXPubAssignAgentView(WeixinAuthMixin, View):
    def get(self, request, *args, **kwargs):

        active_no = kwargs.get('active_no','') or '201712'
        # openid, unionid = 'our5huJDzr6D3IA03p5xwTMm26Gk', 'o29cQs__te-yTyrNkpsuPFPJYSac'

        openid, unionid = self.get_openid_and_unionid(request)
        is_from_weixin = self.is_from_weixin(request)
        if is_from_weixin and not self.valid_openid(openid):
            redirect_url = self.get_wxauth_redirct_url(request)
            return redirect(redirect_url)

        if not is_from_weixin:
            invite_code = request.COOKIES.get('invite_code','')
            if not invite_code:
                invite_code = ''.join(random.sample('1234567890abcdefghijklmnopqrstuvwxyz',10))
            openid = invite_code

        gf_unionid  = '%s_%s' % (openid, active_no)
        group_fans  = GroupFans.objects.filter(union_id=gf_unionid).first()
        if not group_fans:

            admins = XiaoluAdministrator.get_admins_by_active_no(active_no)
            admin_qrcodes = admins.values_list('id', 'weixin_qr_img')
            if len(admin_qrcodes) == 0:
                return HttpResponse('活动管理员列表为空!')

            idx = random.randrange(0, len(admin_qrcodes))
            admin_id, admin_qrcode = admin_qrcodes[idx]
            admin_group = GroupMamaAdministrator.objects.filter(admin=admin_id).first()

            group_fans = GroupFans.objects.create(
                group=admin_group,
                head_img_url="",
                nick="",
                union_id=gf_unionid,
                open_id=openid
            )

        admin_qrcode = group_fans.group.admin.weixin_qr_img

        response = render(
            request,
            'promotion/agent_qrcode.html',
            {'admin_qrcode': admin_qrcode, 'is_weixin': is_from_weixin},
        )

        response.set_cookie('invite_code', openid)

        return response
