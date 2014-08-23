#-*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopapp.weixin.models import (WeiXinAccount,
                                   WeiXinUser,
                                   WeiXinAutoResponse,
                                   WXProduct,
                                   WXOrder,
                                   WXLogistic,
                                   ReferalRelationship,
                                   ReferalSummary,
                                   ReferalBonusRecord,
                                   Refund,
                                   FreeSample,
                                   SampleOrder,
                                   VipCode,
                                   SampleSku,
                                   Coupon,
                                   CouponClick,
                                   Survey
                                   )

class WeiXinAccountAdmin(admin.ModelAdmin):
    
    list_display = ('id','account_id','token','app_id','expires_in',
                    'expired','in_voice','is_active')
    
    list_display_links = ('id','account_id')
    
    list_filter = ('is_active','in_voice')
    search_fields = ['app_id','token','partner_id']
    
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
                    'city','subscribe','subscribe_time','isvalid')
    
    list_filter = ('subscribe','isvalid','sex')
    search_fields = ['openid','nickname','mobile']
    

admin.site.register(WeiXinUser, WeiXinUserAdmin) 


class WeiXinAutoResponseAdmin(admin.ModelAdmin):
    
    list_display = ('message','rtype','title','content','fuzzy_match')
    
    list_filter = ('rtype','fuzzy_match')
    search_fields = ['message','title','content']
    
    ordering = ('message',)
    
    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={'rows':5, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
admin.site.register(WeiXinAutoResponse, WeiXinAutoResponseAdmin) 


class WXProductAdmin(admin.ModelAdmin):
    
    list_display = ('product_id','product_name','sync_stock','status')
    
     #--------设置页面布局----------------
    fieldsets =((u'商品信息:', {
                    'classes': ('expand',),
                    'fields': (('product_id','product_name','product_img')
                               ,('product_base',)
                               ,('sku_list',)
                               ,('attrext',)
                               ,('delivery_info',)
                               ,('sync_stock','status',)
                               )
                }),
                )
    
    list_filter = ('status',)
    search_fields = ['product_id','product_name']
    
admin.site.register(WXProduct, WXProductAdmin) 


class WXOrderAdmin(admin.ModelAdmin):
    
    list_display = ('order_id','buyer_nick','order_total_price','order_create_time',
                    'delivery_id','delivery_company','order_status')
    
    list_filter = ('order_status',)
    search_fields = ['order_id','trans_id','buyer_nick','delivery_id']
    
     #--------设置页面布局----------------
    fieldsets =((u'订单信息:', {
                    'classes': ('expand',),
                    'fields': (('order_id','seller_id','trans_id')
                               ,('order_total_price','order_express_price','order_create_time')
                               ,('buyer_openid','buyer_nick','order_status')
                               )
                }),
                (u'商品信息:', {
                    'classes': ('collapse',),
                    'fields': (('product_id','product_name','product_price')
                               ,('product_sku','product_count','product_img')
                               )
                }),
                (u'收货信息:', {
                    'classes': ('expand',),
                    'fields': (('receiver_name','receiver_province','receiver_city','receiver_zone')
                               ,('receiver_address','receiver_mobile','receiver_phone')
                               ,('delivery_id','delivery_company')
                               )
                }),
                )
    

admin.site.register(WXOrder, WXOrderAdmin) 


class WXLogisticAdmin(admin.ModelAdmin):
    
    list_display = ('company_name','origin_code','company_code')
    
    search_fields = ['company_name','origin_code','company_code']
    

admin.site.register(WXLogistic, WXLogisticAdmin) 


class ReferalRelationshipAdmin(admin.ModelAdmin):
    
    list_display = ('referal_from_openid', 'referal_to_mobile', 'time_created')
    
    search_fields = ['referal_from_openid','referal_to_mobile']

admin.site.register(ReferalRelationship, ReferalRelationshipAdmin) 


class ReferalSummaryAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'direct_referal_count', 'indirect_referal_count')

    search_fields = ['user_openid']

admin.site.register(ReferalSummary, ReferalSummaryAdmin) 


class ReferalBonusRecordAdmin(admin.ModelAdmin):
    list_display = ('user_openid', 'referal_user_openid', 'trade_id', 'bonus_value', 'confirmed_status', 'created')

    search_fields = ['user_openid', 'referal_user_openid', 'trade_id']

admin.site.register(ReferalBonusRecord, ReferalBonusRecordAdmin) 
    

class RefundAdmin(admin.ModelAdmin):
    
    list_display = ('trade_id', 'refund_type','pay_amount','vip_code',
                    'review_note','pay_note','created','refund_status')
    
    list_filter = ('refund_type','refund_status','pay_type')
    search_fields = ['trade_id','vip_code','user_openid','mobile','review_note']
    
admin.site.register(Refund, RefundAdmin) 


class FreeSampleAdmin(admin.ModelAdmin):

    list_display = ('outer_id','name','expiry','stock')

    search_fields = ['outer_id','name']

admin.site.register(FreeSample, FreeSampleAdmin) 


class SampleOrderAdmin(admin.ModelAdmin):

    list_display = ('sample_product','sku_code','user_openid','vipcode','created','status')
    
    list_filter = ('status',)
    search_fields = ['user_openid','vipcode']

admin.site.register(SampleOrder, SampleOrderAdmin) 


class VipCodeAdmin(admin.ModelAdmin):

    list_display = ('owner_openid','code','expiry','code_type',
                    'code_rule', 'max_usage', 'usage_count')

    search_fields = ['owner_openid__openid','code']

admin.site.register(VipCode, VipCodeAdmin) 


class SampleSkuAdmin(admin.ModelAdmin):

    list_display = ('sample_product','sku_code','sku_name')
    
    search_fields = ['sku_code','sku_name']

admin.site.register(SampleSku, SampleSkuAdmin) 


class CouponAdmin(admin.ModelAdmin):
    list_display = ('description','coupon_url','face_value','expiry','created')

admin.site.register(Coupon, CouponAdmin) 


class CouponClickAdmin(admin.ModelAdmin):
    list_display = ('coupon','wx_user','vipcode','created')
    search_fields = ['wx_user', 'vipcode']

admin.site.register(CouponClick, CouponClickAdmin) 

class SurveyAdmin(admin.ModelAdmin):
    list_display = ('selection', 'wx_user', 'created')
    search_fields = ['wx_user']
    list_filter = ('selection',)

admin.site.register(Survey, SurveyAdmin) 
