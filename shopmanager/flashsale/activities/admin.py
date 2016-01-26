# -*- coding:utf-8 -*-
from django.contrib import admin
from .models import Activities, ParticipateDetail, Participation


class ActivitiesDAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'start_time', 'end_time', 'modified')
    list_display_links = ('title',)
    list_filter = ('created',)
    search_fields = ['=id', '=title']


admin.site.register(Activities, ActivitiesDAdmin)


class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity', 'phone_no', 'activation_code', 'result', 'modified')
    list_display_links = ('activity', 'phone_no')
    list_filter = ('created',)
    search_fields = ['=id', '=activity']


admin.site.register(Participation, ParticipationAdmin)


class ParticipateDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'participation', 'verify_phone', 'is_activate', 'created')
    list_display_links = ('verify_phone', 'id')
    list_filter = ('created',)
    search_fields = ['=id', '=participation', 'verify_phone']


admin.site.register(ParticipateDetail, ParticipateDetailAdmin)

