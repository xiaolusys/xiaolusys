# encoding:utf-8
from django.contrib import admin
from .models import Joiner


class JoinerAdmin(admin.ModelAdmin):
    list_display = ('name', 'thumbnail_pic', 'born_at', 'addresss', 'descript', 'is_active')
    # list_display_links = ('trade_id_link','popup_tid_link')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_per_page = 50

    list_filter = ('is_active',)

    search_fields = ['id', 'name']

    def thumbnail_pic(self, obj):
        return '<img src="%s?imageMogr2/thumbnail/100/format/jpg/quality/90" width="100px" height="80px"/>' % (
        obj.thumbnail.url)

    thumbnail_pic.allow_tags = True
    thumbnail_pic.short_description = u"照片"

    # 作废商品
    def invalid_joiner_action(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, u"批量取消成功")

    invalid_joiner_action.short_description = u"取消活动参与"

    # 作废商品
    def active_joiner_action(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, u"批量激活成功")

    active_joiner_action.short_description = u"激活活动参与"

    actions = ['invalid_joiner_action',
               'active_joiner_action',
               ]


admin.site.register(Joiner, JoinerAdmin)
