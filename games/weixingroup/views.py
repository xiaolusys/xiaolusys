# coding=utf-8
__author__ = 'yan.huang'
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.forms import forms
from rest_framework.response import Response
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from core.weixin.mixins import WeixinAuthMixin
from core.upload.xqrcode import push_qrcode_to_remote
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, ActivityUsers
from .serializers import XiaoluAdministratorSerializers, GroupMamaAdministratorSerializers, GroupFansSerializers, \
    MamaGroupsSerializers
from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
from flashsale.promotion.models import ActivityEntry
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.xiaolumm.serializers import XiaoluMamaSerializer
from flashsale.pay.models import Customer
from shopapp.weixin.models import WeixinUserInfo
from .forms import GroupFansForm
import logging
log = logging.getLogger('django.request')


class XiaoluAdministratorViewSet(WeixinAuthMixin, viewsets.GenericViewSet):
    """
        小鹿微信群管理员
    """
    queryset = XiaoluAdministrator.objects.all()
    serializer_class = XiaoluAdministratorSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['POST', 'GET'])
    def mama_join(self, request):
        if not request.user.is_anonymous():
            xiaoumama = request.user.customer.getXiaolumm() if request.user.customer else None
        else:
            # 1. check whether event_id is valid
            self.set_appid_and_secret(settings.WX_PUB_APPID, settings.WX_PUB_APPSECRET)
            # 2. get openid from cookie
            openid, unionid = self.get_cookie_openid_and_unoinid(request)
            if not self.valid_openid(unionid):
                # 3. get openid from gf'debug' or from using 'code' (if code exists)
                userinfo = self.get_auth_userinfo(request)
                unionid = userinfo.get("unionid")
                openid = userinfo.get("openid")
                if not self.valid_openid(unionid):
                    # 4. if we still dont have openid, we have to do oauth
                    redirect_url = self.get_snsuserinfo_redirct_url(request)
                    return redirect(redirect_url)
            xiaoumama = XiaoluMama.objects.filter(openid=unionid).first()

        if not xiaoumama:
            raise exceptions.ValidationError(u'您不是小鹿妈妈或者你的微信号未和小鹿妈妈账号绑定')

        task_mama_daily_tab_visit_stats.delay(xiaoumama.id, MamaTabVisitStats.TAB_MAMA_BOUTIQUE_FAQ)
        
        mama_id = xiaoumama.id
        administrastor_id = request.POST.get('administrastor_id') or request.GET.get('administrastor_id')
        if GroupMamaAdministrator.objects.filter(mama_id=mama_id).exists():
            admin = GroupMamaAdministrator.objects.filter(mama_id=mama_id).first().admin
        elif administrastor_id:
            admin = XiaoluAdministrator.objects.filter(id=administrastor_id).first()
            if not admin:
                raise exceptions.NotFound(u'指定的管理员不存在')
        else:
            admin = XiaoluAdministrator.get_group_mincnt_admin()
        group = GroupMamaAdministrator.get_or_create(admin=admin, mama_id=mama_id)
        return Response(self.get_serializer(admin).data)

    @list_route(methods=['GET'])
    def mamawx_join(self, request):
        if not request.user.is_anonymous():
            xiaoumama = request.user.customer.getXiaolumm() if request.user.customer else None
        else:
            # 1. check whether event_id is valid
            self.set_appid_and_secret(settings.WX_PUB_APPID, settings.WX_PUB_APPSECRET)
            # 2. get openid from cookie
            openid, unionid = self.get_cookie_openid_and_unoinid(request)
            if not self.valid_openid(unionid):
                # 3. get openid from gf'debug' or from using 'code' (if code exists)
                userinfo = self.get_auth_userinfo(request)
                unionid = userinfo.get("unionid")
                openid = userinfo.get("openid")
                if not self.valid_openid(unionid):
                    # 4. if we still dont have openid, we have to do oauth
                    redirect_url = self.get_snsuserinfo_redirct_url(request)
                    return redirect(redirect_url)
            xiaoumama = XiaoluMama.objects.filter(openid=unionid).first()
        if not xiaoumama:
            raise exceptions.ValidationError(u'您不是小鹿妈妈或者你的微信号未和小鹿妈妈账号绑定')
        mama_id = xiaoumama.id
        administrastor_id = request.GET.get('administrastor_id')
        if GroupMamaAdministrator.objects.filter(mama_id=mama_id).exists():
            admin = GroupMamaAdministrator.objects.filter(mama_id=mama_id).first().admin
        elif administrastor_id:
            admin = XiaoluAdministrator.objects.filter(id=administrastor_id).first()
            if not admin:
                raise exceptions.NotFound(u'指定的管理员不存在')
        else:
            admin = XiaoluAdministrator.get_group_mincnt_admin()
        group = GroupMamaAdministrator.get_or_create(admin=admin, mama_id=mama_id)
        return redirect("/july_event/html/mama_attender.html?unionid=" + xiaoumama.openid)

    @list_route(methods=['GET'])
    def get_xiaolu_administrator(self, request):
        administrastor_id = request.GET.get('administrastor_id')
        if GroupMamaAdministrator.objects.filter(id=request.user.id).exists():
            admin = GroupMamaAdministrator.objects.filter(mama_id=request.user.id).first().admin
        elif administrastor_id:
            admin = GroupMamaAdministrator.objects.filter(id=administrastor_id).first()
            if not admin:
                raise exceptions.NotFound(u'指定的管理员不存在')
        else:
            admin = XiaoluAdministrator.get_group_mincnt_admin()
        return Response(self.get_serializer(admin).data)


class GroupMamaAdministratorViewSet(viewsets.mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
        小鹿微信群
    """
    queryset = GroupMamaAdministrator.objects.all()
    serializer_class = MamaGroupsSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    JOIN_URL = settings.M_SITE_URL + '/sale/weixingroup/liangxi/join?group_id='

    @list_route(methods=['GET'])
    def get_self_info(self, request):
        try:
            customer = request.user.customer
            mama = XiaoluMama.objects.get(openid=customer.unionid)
            join = GroupMamaAdministrator.objects.filter(mama_id=mama.id, status=1).exists()
            res = {
                'join': join,
                'mama_id': mama.id,
                'union_id': customer.unionid,
                'url': '/july_event/html/mama_attender.html?unionid=' + customer.unionid
            }
            return Response(res)
        except Exception, e:
            raise exceptions.ValidationError(u'用户未登录或不是小鹿妈妈')

    @detail_route(methods=['GET'])
    def detail(self, request, pk):
        group = get_object_or_404(GroupMamaAdministrator, group_uni_key=pk)
        res = self.get_serializer(group).data
        res['mama'] = XiaoluMamaSerializer(group.mama).data
        res = Response(res)
        res['Access-Control-Allow-Origin'] = '*'
        return res

    @detail_route(methods=['GET'])
    def groups(self, requenst, pk):
        mama = XiaoluMama.objects.filter(openid=pk).first()
        if not mama:
            raise exceptions.NotFound(u'未能找到指定的小鹿妈妈')
        groups = GroupMamaAdministrator.objects.filter(mama_id=mama.id)
        if not groups.first():
            raise exceptions.NotFound(u'此小鹿妈妈尚未报名到微信群')
        res = {}
        admin = groups.first().admin
        res['admin'] = XiaoluAdministratorSerializers(admin).data
        res['groups'] = self.get_serializer(groups, many=True).data
        res = Response(res)
        res['Access-Control-Allow-Origin'] = '*'
        return res

    @detail_route(methods=['GET'])
    def users(self, request, pk):
        group = GroupMamaAdministrator.objects.filter(group_uni_key=pk).first()
        if not group:
            raise exceptions.NotFound(u'指定的小鹿妈妈群不存在')
        queryset = self.filter_queryset(group.fans.order_by('-id'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def join(self):
        """凉席活动同时加入了微信群组"""
        pass

    @detail_route(methods=['GET'])
    def qr_code(self, request, pk):
        group = GroupMamaAdministrator.objects.filter(group_uni_key=pk).first()
        if not group:
            raise exceptions.NotFound(u'指定的小鹿妈妈群不存在')
        link = self.JOIN_URL + group.group_uni_key
        return redirect(push_qrcode_to_remote('lxmm_join' + group.group_uni_key, link))


class LiangXiActivityViewSet(WeixinAuthMixin, viewsets.GenericViewSet):
    """
        凉席活动后台支持
        (将凉席活动的代码都放在这里，便于抛弃）
    """
    ACTIVITY_NAME = u"7月送万件宝宝凉席活动"
    queryset = GroupFans.objects.all()
    serializer_class = GroupFansSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @property
    def activity(self):
        if not hasattr(self, '_activity_'):
            self._activity_ = ActivityEntry.objects.filter(title=LiangXiActivityViewSet.ACTIVITY_NAME).first()
        return self._activity_

    @detail_route(methods=['GET'])
    def detail(self, request, pk):
        fans = get_object_or_404(GroupFans, pk=pk)
        res = self.get_serializer(fans).data
        res['group'] = GroupMamaAdministratorSerializers(fans.group).data
        res['mama'] = XiaoluMamaSerializer(fans.group.mama).data
        return Response(res)

    @list_route(methods=['GET'])
    def get_group_users(self, request):
        group_id = request.GET.get('group_id')
        group = GroupMamaAdministrator.objects.filter(group_uni_key=group_id).first()
        if not group:
            raise exceptions.NotFound(u'指定的小鹿妈妈群不存在')
        queryset = self.filter_queryset(group.fans.order_by('-id'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['GET'])
    def join(self, request):
        form = GroupFansForm(request.GET)
        if not form.is_valid():
            raise exceptions.ValidationError(form.error_message)
        if not self.activity.is_on():
            raise exceptions.ValidationError(u"凉席活动暂不可使用")
        group_uni_key = form.cleaned_data['group_id']
        group = GroupMamaAdministrator.objects.filter(group_uni_key=group_uni_key).first()
        if not group:
            raise exceptions.NotFound(u'此妈妈尚未加入微信群组')
        self.set_appid_and_secret(settings.WX_PUB_APPID, settings.WX_PUB_APPSECRET)
        # get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)
        userinfo = {}
        if unionid:
            userinfo_records = WeixinUserInfo.objects.filter(unionid=unionid)
            record = userinfo_records.first()
        else:
            record = None
        if record:
            userinfo.update({"unionid": record.unionid, "nickname": record.nick, "headimgurl": record.thumbnail})
        else:
            # get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")
            if not self.valid_openid(unionid):
                # if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)
        # if user is xiaolumama, jump to his qr_code page
        xiaolumama = XiaoluMama.objects.filter(openid=unionid).first()
        if xiaolumama:
            mamagroup = GroupMamaAdministrator.objects.filter(mama_id=xiaolumama.id).first()
            if mamagroup:
                group = mamagroup
        # if user already join a group, change group
        fans = GroupFans.objects.filter(
            union_id=userinfo.get('unionid')
        ).first()
        if not fans:
            # log.error("lx-join:" + str(userinfo) + '|record:' + str(record))
            fans = GroupFans.create(group, request.user.id, userinfo.get('headimgurl'), userinfo.get('nickname'),
                                    userinfo.get('unionid'), userinfo.get('openid', ''))
            user_id = None
            customer = Customer.objects.filter(unionid=unionid).exclude(status=Customer.DELETE).first()
            if request.user.id:
                user_id = request.user.id
            elif customer:
                user_id = customer.user_id
            if user_id:
                ActivityUsers.join(self.activity, user_id, fans.group_id)
        group = GroupMamaAdministrator.objects.get(id=fans.group_id)
        response = redirect("/mall/activity/summer/mat/register?groupId=" + group.group_uni_key+'&fansId=' + str(fans.id))
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

    @list_route(methods=['GET'])
    def show_fans(self, request):
        form = GroupFansForm(request.GET)
        if not form.is_valid():
            raise exceptions.ValidationError(form.error_message)
        group_uni_key = form.cleaned_data['group_id']
        group = GroupMamaAdministrator.objects.filter(group_uni_key=group_uni_key).first()
        if not group:
            raise exceptions.NotFound(u'此妈妈尚未加入微信群组')
        if not request.user.is_anonymous():
            xiaoumama = request.user.customer.getXiaolumm() if request.user.customer else None
        else:
            raise exceptions.ValidationError(u'粉丝详情请从APP进入页面查看')
        if not xiaoumama:
            raise exceptions.ValidationError(u'只有小鹿妈妈可以查看粉丝详情')
        fans = GroupFans.objects.filter(
            union_id=xiaoumama.openid
        ).first()
        if not fans:
            # 妈妈都成为自己的粉丝
            customer = xiaoumama.get_mama_customer()
            fans = GroupFans.create(group, customer.user.id, customer.thumbnail, customer.nick,
                                    customer.unionid, customer.openid)
            ActivityUsers.join(self.activity, customer.user.id, fans.group_id)
        # 纠正成为了他人粉丝的小鹿妈妈
        elif fans.group_id != group:
            log.error(u'fans become other fans:' + str(fans.id) + '|' + str(fans.group_id) + '|need' + str(group.id))
        return redirect("/mall/activity/summer/mat/register?groupId=" + group.group_uni_key+'&fansId=' + str(fans.id))