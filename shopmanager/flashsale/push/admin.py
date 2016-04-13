# coding=utf-8

from django.contrib import admin
from models_message import PushMsgTpl


class PushMsgTplAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tpl_content', 'is_valid')
    list_filter = ['is_valid']


admin.site.register(PushMsgTpl, PushMsgTplAdmin)
