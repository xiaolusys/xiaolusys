# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from ..models import OutwareActionRecord

@admin.register(OutwareActionRecord)
class OutwareActionRecordAdmin(admin.ModelAdmin):
    list_display = ('object_id', 'record_obj', 'action_code', 'state_code', 'message', 'created')
    list_filter = ('action_code', 'state_code',)
    search_fields = ['=object_id']
    ordering = ('-modified',)