# coding:utf-8
__author__ = 'yan.huang'
from django.contrib import admin
from django.http import HttpResponseRedirect
from core.admin import BaseModelAdmin
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, ActivityUsers

HOST = "http://m.xiaolumeimei.com"


class XiaoluAdministratorAdmin(BaseModelAdmin):
    search_fields = ['id', 'user_id', 'name', 'nick']
    list_display = ['id', 'user_id', 'username', 'nick', 'admin_link', 'admin_wx_link']
    list_filter = ['status']

    def admin_link(self, obj):
        return HOST + '/sale/weixingroup/xiaoluadministrator/mama_join?administrastor_id=' + str(obj.id)

    admin_link.short_description = u'小鹿妈妈报名页面'

    def admin_wx_link(self, obj):
        return HOST + '/sale/weixingroup/xiaoluadministrator/mamawx_join?administrastor_id=' + str(obj.id)

    admin_wx_link.short_description = u'小鹿妈妈微信报名链接'


admin.site.register(XiaoluAdministrator, XiaoluAdministratorAdmin)


class GroupMamaAdministratorAdmin(BaseModelAdmin):
    search_fields = ['admin__id', 'admin__username', 'admin__nick', 'mama_id']
    list_display = ['id', 'mama_id', 'mama_nick', 'mama_mobile', 'admin__id', 'admin__username', 'admin__nick',
                    'group_uni_key', 'group_link', 'status']
    list_filter = ['status']

    def admin__id(self, obj):
        return obj.admin.id

    admin__id.short_description = u'小鹿管理员ID'

    def admin__username(self, obj):
        return obj.admin.username

    admin__username.short_description = u'小鹿管理员用户名'

    def admin__nick(self, obj):
        return obj.admin.nick

    admin__nick.short_description = u'小鹿管理员昵称'

    def mama_nick(self, obj):
            return obj.mama.get_customer().nick

    mama_nick.short_description = u'小鹿妈妈用户名'

    def mama_mobile(self, obj):
        return obj.mama.mobile

    mama_mobile.short_description = u'小鹿妈妈手机'

    def group_link(self, obj):
        return HOST + "/july_event/html/mama_attender.html?unionid=" + obj.mama.openid

    group_link.short_description = u'小鹿妈妈查看凉席活动详情'


admin.site.register(GroupMamaAdministrator, GroupMamaAdministratorAdmin)


class ActivityUsersAdmin(BaseModelAdmin):
    search_fields = ['id', '=activity_id', 'user_id']
    list_display = ['activity', 'user_id', 'group']


admin.site.register(ActivityUsers, ActivityUsersAdmin)
