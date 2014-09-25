#-*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.conf import settings

from django.forms import TextInput, Textarea
from shopback.base.options import DateFieldListFilter
from .models import WeixinUserPicture


class WeixinUserPictureAdmin(admin.ModelAdmin):
    
    list_display = ('user_openid', 'mobile', 'pic_link','check_link','pic_type','pic_num',
                    'created','status')
    search_fields = ['user_openid','mobile']
    
    list_filter = ('pic_type','status',('created',DateFieldListFilter))
    
    def pic_link(self, obj):
        abs_pic_url = '%s%s'%(settings.MEDIA_URL,obj.pic_url)
        return (u'<a href="%s" target="_blank"><img src="%s" width="100px" height="80px"/></a>'%(abs_pic_url,abs_pic_url))
    
    pic_link.allow_tags = True
    pic_link.short_description = "上传图片"
    
    def check_link(self, obj):
        return (u'<a href="javascript:void(0);" class="btn %s" pid="%d" >%s</a>'%
                (('','btn-success')[0 if obj.status else 1],obj.id,(u'审核',u'已处理')[1 if obj.status else 0]))
    
    check_link.allow_tags = True
    check_link.short_description = "操作"
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/common.css","jquery/jquery-ui-1.10.1.css")}
        js = ("jquery/jquery-ui-1.8.13.min.js","jquery/addons/jquery.form.js","script/admin/adminpopup.js")
    
    
admin.site.register(WeixinUserPicture, WeixinUserPictureAdmin) 