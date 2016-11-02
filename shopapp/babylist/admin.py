# -*- coding:utf8 -*-
from django.contrib import admin
from shopapp.babylist.models import BabyPhone


class BabyPhoneAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'ma_mobile', 'mather', 'fa_mobile', 'father', 'state', 'address', 'sex', 'born', 'code', 'hospital',)
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    search_fields = ['father', 'mather', 'id', 'ma_mobile', 'fa_mobile']


admin.site.register(BabyPhone, BabyPhoneAdmin)
