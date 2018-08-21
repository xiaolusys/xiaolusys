# -*- coding:utf8 -*-
from django.contrib import admin
from shopapp.calendar.models import StaffEvent


class StaffEventAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'executor', 'creator', 'start', 'end', 'interval_day', 'title', 'type', 'created', 'modified', 'is_finished')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'

    list_filter = ('status', 'is_finished',)
    search_fields = ['executor__username', 'id', 'title']


admin.site.register(StaffEvent, StaffEventAdmin)
