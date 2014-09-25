#-*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback.base.options import DateFieldListFilter
from .models import WeixinUserPicture


class WeixinUserPictureAdmin(admin.ModelAdmin):
    
    list_display = ('user_openid', 'mobile', 'pic_url','pic_type','pic_num',
                    'created','status')
    search_fields = ['user_openid','mobile']
    
    list_filter = ('pic_type','status',('created',DateFieldListFilter))

admin.site.register(WeixinUserPicture, WeixinUserPictureAdmin) 