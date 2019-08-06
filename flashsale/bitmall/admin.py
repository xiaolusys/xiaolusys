# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import BitVIP

@admin.register(BitVIP)
class BitVIPAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'mobile', 'parent', 'progress', 'created')
    list_filter = ('progress', 'created')
    search_fields = ['=id', '=user__username', '=parent_id']
    readonly_fields = ['user']
    list_per_page = 100