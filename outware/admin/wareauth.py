# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from ..models import OutwareAccount

@admin.register(OutwareAccount)
class OutwareAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'app_id', 'sign_method')
    list_filter = ('created',)
    search_fields = ['=id','=app_id']
    ordering = ('-created',)