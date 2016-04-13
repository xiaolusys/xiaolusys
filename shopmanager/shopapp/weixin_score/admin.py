# -*- coding: utf-8 -*-
from django.contrib import admin
from shopapp.weixin_score.models import SampleFrozenScore


class SampleFrozenScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_openid', 'sample_id', 'frozen_score', 'frozen_time', 'modified', 'status')
    list_display_links = ('id', 'sample_id')

    list_filter = ('status',)
    search_fields = ['id', 'user_openid', 'sample_id']


admin.site.register(SampleFrozenScore, SampleFrozenScoreAdmin)
