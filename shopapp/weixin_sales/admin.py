# -*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.conf import settings

from django.forms import TextInput, Textarea
from core.filters import DateFieldListFilter
from .models import (
    WeixinUserPicture,
    WeixinUserAward,
    WeixinLinkClicks,
    WeixinLinkClickRecord,
    WeixinLinkShare)


class WeixinUserPictureAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'mobile', 'pic_link', 'check_link', 'pic_type', 'pic_num',
                    'created', 'status')
    search_fields = ['user_openid', 'mobile']

    list_filter = ('pic_type', 'status', ('created', DateFieldListFilter))

    def pic_link(self, obj):
        abs_pic_url = '%s%s' % (settings.MEDIA_URL, obj.pic_url)
        return (
        u'<a href="%s" target="_blank"><img src="%s" width="100px" height="80px"/></a>' % (abs_pic_url, abs_pic_url))

    pic_link.allow_tags = True
    pic_link.short_description = "上传图片"

    def check_link(self, obj):
        return (u'<a href="javascript:void(0);" class="btn %s" pid="%d" >%s</a>' %
                (('btn-success', '', '')[obj.status], obj.id, (u'审核', u'已处理', u'')[obj.status]))

    check_link.allow_tags = True
    check_link.short_description = "操作"

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.form.js",
              "script/admin/adminpopup.js",
              "weixin/sales/js/picturereview.js")


admin.site.register(WeixinUserPicture, WeixinUserPictureAdmin)


class WeixinUserAwardAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'is_receive', 'is_share', 'is_notify', 'award_val', 'created', 'modified')
    search_fields = ['user_openid', 'referal_from_openid']

    list_filter = ('is_receive', 'is_share', 'is_notify', ('created', DateFieldListFilter))


admin.site.register(WeixinUserAward, WeixinUserAwardAdmin)


class WeixinLinkClicksAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'link_url', 'clicker_num', 'click_count', 'validated_in', 'modified', 'created')
    search_fields = ['user_openid', 'link_url']

    list_filter = (('modified', DateFieldListFilter), 'link_type')


admin.site.register(WeixinLinkClicks, WeixinLinkClicksAdmin)


class WeixinLinkClickRecordAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'link_url', 'created')
    search_fields = ['user_openid', 'link_url']

    list_filter = (('created', DateFieldListFilter),)


admin.site.register(WeixinLinkClickRecord, WeixinLinkClickRecordAdmin)


class WeixinLinkShareAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'link_url', 'link_type', 'created', 'modified')
    search_fields = ['user_openid', 'link_url']

    list_filter = (('created', DateFieldListFilter), 'link_type')


admin.site.register(WeixinLinkShare, WeixinLinkShareAdmin)
