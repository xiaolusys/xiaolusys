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
    search_fields = ['id', 'admin__id', 'admin__username', 'admin__nick', 'mama_id']
    list_display = ['id', 'mama_id', 'mama_nick', 'mama_mobile', 'admin__id', 'admin__username', 'admin__nick',
                    'group_uni_key', 'fans_count_quick', 'gift_count_quick', 'gifted_count_quick', 'group_link', 'status']
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
        customer = obj.mama.get_mama_customer()
        return customer.nick if customer else ''

    mama_nick.short_description = u'小鹿妈妈用户名'

    def mama_mobile(self, obj):
        return obj.mama.mobile

    mama_mobile.short_description = u'小鹿妈妈手机'

    def fans_count_quick(self, obj):
        return obj.fans_count_dict.get(obj.id, 0)
    fans_count_quick.short_description = u'粉丝数量'

    def gift_count_quick(self, obj):
        return obj.gift_count_dict.get(obj.id, 0)
    gift_count_quick.short_description = u'将发券粉丝数'

    def gifted_count_quick(self, obj):
        return obj.gifted_count_dict.get(obj.id, 0)
    gifted_count_quick.short_description = u'已发券用户数'

    def group_link(self, obj):
        return HOST + "/july_event/html/mama_attender.html?unionid=" + obj.mama.openid

    group_link.short_description = u'小鹿妈妈查看凉席活动详情'


admin.site.register(GroupMamaAdministrator, GroupMamaAdministratorAdmin)


class ActivityUsersAdmin(BaseModelAdmin):
    search_fields = ['id', '=activity_id', 'user_id', 'group']
    list_display = ['activity', 'user_id', 'group_link']

    def group_link(self, obj):
        return '<a href="/admin/weixingroup/groupmamaadministrator?group_uni_key=' + obj.group.group_uni_key + '">'+obj.group.group_uni_key + '</a>'

    group_link.short_description = u'微信群'
    group_link.allow_tags = True
admin.site.register(ActivityUsers, ActivityUsersAdmin)


class GroupFansAdmin(BaseModelAdmin):
    list_display = ['id', 'group_link', 'user_id', 'nick', 'union_id', 'open_id', 'gifted', 'head_img_url']
    search_fields = ['id', 'group__id', 'group__group_uni_key', 'group__mama_id', 'nick']

    def lookup_allowed(self, lookup, value):
        if lookup in ['group__id', 'group__group_uni_key', 'group__mama_id']:
            return True
        return super(GroupFansAdmin, self).lookup_allowed(lookup, value)

    def group_link(self, obj):
        return '<a href="/admin/weixingroup/groupmamaadministrator?group_uni_key=' + obj.group.group_uni_key + '">'+obj.group.group_uni_key + '</a>'

    group_link.short_description = u'微信群'
    group_link.allow_tags = True
    group_link.admin_order_field = 'group_id'

admin.site.register(GroupFans, GroupFansAdmin)
