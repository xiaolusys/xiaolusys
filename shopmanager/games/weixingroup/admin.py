# coding:utf-8
__author__ = 'yan.huang'
from django.contrib import admin
from django.http import HttpResponseRedirect
from core.admin import BaseModelAdmin
from .models import XiaoluAdministrator, GroupMamaAdministrator, GroupFans, Activity, ActivityUsers


class XiaoluAdministratorAdmin(BaseModelAdmin):
    search_fields = ['id', 'user_id', 'name', 'nick']
    list_display = ['user_id', 'username', 'nick']
    list_filter = ['status']


admin.site.register(XiaoluAdministrator, XiaoluAdministratorAdmin)


class GroupMamaAdministratorAdmin(BaseModelAdmin):
    search_fields = ['admin__id', 'admin__username', 'admin__nick', 'mama_id']
    list_display = ['id', 'mama_id', 'admin__id', 'admin__username', 'admin__nick', 'status', ]
    list_filter = ['status']

    def admin__id(self, obj):
        return obj.admin.id

    def admin__username(self, obj):
        return obj.admin.username

    def admin__nick(self, obj):
        return obj.admin.nick

admin.site.register(GroupMamaAdministrator, GroupMamaAdministratorAdmin)


class ActivityAdmin(BaseModelAdmin):
    search_fields = ['=id', '=name', 'desc']
    list_display = ['id', 'name', 'homepage', 'begin_time', 'end_time', 'desc', 'content', 'note']
    list_filter = ['status']


admin.site.register(Activity, ActivityAdmin)
