# coding=utf-8
__author__ = 'yan.huang'
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.forms import forms
from rest_framework.response import Response
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions

from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, Activity
from .serializers import XiaoluAdministratorSerializers, GroupMamaAdministratorSerializers, GroupFansSerializers
from core.weixin.mixins import WeixinAuthMixin
from shopapp.weixin.models_base import WeixinUserInfo


class XiaoluAdministratorViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = XiaoluAdministrator.objects.all()
    serializer_class = XiaoluAdministratorSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET'])
    def get_xiaolu_administrator(self, request):
        if GroupMamaAdministrator.objects.filter(id=request.user.id).exists():
            admin = GroupMamaAdministrator.objects.filter(id=request.user.id).first().admin
        else:
            admin = XiaoluAdministrator.get_group_mincnt_admin()
        return Response(admin)


class GroupMamaAdministratorViewSet(viewsets.mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = GroupMamaAdministrator.objects.all()
    serializer_class = GroupMamaAdministratorSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @detail_route(methods=['GET'])
    def get_group_detail(self, request, pk):
        group = get_object_or_404(GroupMamaAdministrator, pk=pk)
        return Response(group)


class LiangXiActivityViewSet(WeixinAuthMixin, viewsets.GenericViewSet):
    """
        凉席活动后台支持
    """
    ACTIVITY_NAME = "LIANGXI"
    queryset = GroupFans.objects.all()
    activity = Activity.objects.filter(name=ACTIVITY_NAME).first()
    serializer_class = GroupFansSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['POST'])
    def get_xiaolu_administrator(self, request):
        return Response()

    @detail_route(methods=['GET'])
    def get_group_detail(self, request, pk):
        fans = get_object_or_404(GroupFans, pk=pk)
        return Response(fans)

    @list_route(methods=['POST'])
    def join(self, request):
        form = forms.GroupFansForm(request)
        if form.is_vailed():
            raise exceptions.ValidationError(form.error_message)
        if self.activity.is_vailed():
            raise exceptions.ValidationError(u"凉席活动暂不可使用")
        group_id = form.cleaned_data['group_id']
        # mama_id = form.cleaned_data['mama_id']
        group = GroupMamaAdministrator.objects.filter(group_id=group_id).first()
        if not group:
            raise exceptions.NotFound(u'此妈妈')
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)

        # get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        userinfo = {}
        userinfo_records = WeixinUserInfo.objects.filter(unionid=unionid)
        record = userinfo_records.first()
        if record:
            userinfo.update({"unionid":record.unionid, "nickname":record.nick, "headimgurl":record.thumbnail})
        else:
            # get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")

            if not self.valid_openid(unionid):
                # if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)
        # if user already join a group, change group
        fans = GroupFans.objects.filter(
            unionid=userinfo.get('unionid'),
            open_id=userinfo.get('open_id')
        ).first()
        if fans:
            fans.group_id = group.id
            fans.head_img_url = userinfo.get('headimgurl')
            fans.nick = userinfo.get('nickname')
            fans.save()
        else:
            fans = GroupFans.create(group, request.user.id, userinfo.get('headimgurl'), userinfo.get('nickname'),
                                userinfo.get('unionid'), userinfo.get('open_id'))
        self.activity.join(request.user.id, fans.group_id)
        return Response()