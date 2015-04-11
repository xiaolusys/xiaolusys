#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect

from shopback.trades.filters import DateFieldListFilter
from .models import SaleTrade,SaleOrder,TradeCharge,Customer,Register,District


class SaleOrderInline(admin.TabularInline):
    
    model = SaleOrder
    fields = ('oid','outer_id','title','outer_sku_id','sku_name','payment','num','status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }
    
    def get_readonly_fields(self, request, obj=None):
   
        if not request.user.is_superuser:
            return self.readonly_fields + ('oid',)
        return self.readonly_fields
    

class SaleTradeAdmin(admin.ModelAdmin):
    list_display = ('id','tid','buyer_nick','channel','payment','pay_time','created','status')
    list_display_links = ('id','tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter   = ('channel',('created',DateFieldListFilter))
    search_fields = ['tid','id']
    
    inlines = [SaleOrderInline]
    
    fieldsets =(('订单基本信息:', {
                    'classes': ('expand',),
                    'fields': (('tid','buyer_nick','channel','status')
                               ,('trade_type','total_fee','payment','post_fee')
                               ,('pay_time','consign_time')
                               ,('buyer_message','seller_memo')
                               )
                }),
                ('收货人及物流信息:', {
                    'classes': ('expand',),
                    'fields': (('receiver_name','receiver_state','receiver_city','receiver_district')
                            ,('receiver_address','receiver_zip','receiver_mobile','receiver_phone')
                            ,('logistics_company','out_sid'))
                }),
                )
    
     #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':35})},
    }
    
    def get_readonly_fields(self, request, obj=None):
   
        if not request.user.is_superuser:
            return self.readonly_fields + ('tid',)
        return self.readonly_fields
    
admin.site.register(SaleTrade,SaleTradeAdmin)


class TradeChargeAdmin(admin.ModelAdmin):
    
    list_display = ('order_no','charge','channel','amount','time_paid','paid','refunded')
    list_display_links = ('order_no','charge',)
    
    list_filter   = (('time_paid',DateFieldListFilter),)
    search_fields = ['order_no','charge']

admin.site.register(TradeCharge,TradeChargeAdmin)


class RegisterAdmin(admin.ModelAdmin):
    list_display = ('id','cus_uid','vmobile','vemail','created')
    list_display_links = ('id','cus_uid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter   = (('created',DateFieldListFilter),)
    search_fields = ['id','cus_uid','vmobile','vemail']

admin.site.register(Register,RegisterAdmin)


class CustomerAdmin(admin.ModelAdmin):
    
    list_display = ('id','nick','mobile','phone','created','modified')
    list_display_links = ('id','nick',)
    
    search_fields = ['id','mobile','openid','unionid']
    
    
admin.site.register(Customer,CustomerAdmin)



class DistrictAdmin(admin.ModelAdmin):
    
    list_display = ('id','name','parent_id','grade','sort_order')
    search_fields = ['parent_id','name']
    
    list_filter = ('grade',)

admin.site.register(District, DistrictAdmin)
