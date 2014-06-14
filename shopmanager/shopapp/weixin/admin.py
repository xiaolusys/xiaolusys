#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopapp.weixin.models import WeiXinAccount,WeiXinUser,WeiXinAutoResponse

class WeiXinAccountAdmin(admin.ModelAdmin):
    
    list_display = ('id','account_id','token','app_id','expires_in',
                    'expired','in_voice','is_active')
    
    list_filter = ('is_active','in_voice')
    search_fields = ['app_id','token']
    
    def urlencode(self,value):
        ds = {'s':value}
        return urllib.urlencode(ds)[len('s='):]

    def unicode2Utf8(self,menu):
        
        if type(menu) == list:
            for m in menu:
                self.unicode2Utf8(m)
            
        if type(menu) == dict:
            for k,v in menu.iteritems():
                if type(v) == list:
                    self.unicode2Utf8(v)

                if type(v) == unicode:
                    menu[k] = v.encode('utf8')
                
    
    def response_change(self, request, obj, *args, **kwargs):
        #订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name

        pk_value = obj._get_pk_val()
        
        if obj.jmenu:
            try:
                jmenu = obj.jmenu.copy()
               
                #self.unicode2Utf8(jmenu)
                from .weixin_apis import WeiXinAPI
                wx_api = WeiXinAPI()
                wx_api.createMenu(jmenu)
            except Exception,exc:
                self.message_user(request, u"微信菜单创建失败：%s"%(exc.message or u'请求错误'))
            
        return super(WeiXinAccountAdmin, self).response_change(request, obj, *args, **kwargs)

admin.site.register(WeiXinAccount, WeiXinAccountAdmin)  


class WeiXinUserAdmin(admin.ModelAdmin):
    
    list_display = ('openid','nickname','sex','province',
                    'city','subscribe_time','subscribe')
    
    list_filter = ('subscribe','sex')
    search_fields = ['openid','nickname']
    

admin.site.register(WeiXinUser, WeiXinUserAdmin) 


class WeiXinAutoResponseAdmin(admin.ModelAdmin):
    
    list_display = ('message','rtype','title','content')
    
    list_filter = ('rtype',)
    search_fields = ['message','title','content']
    
    ordering = ('message',)
    
    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={'rows':5, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    

admin.site.register(WeiXinAutoResponse, WeiXinAutoResponseAdmin) 
