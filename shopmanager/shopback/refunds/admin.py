#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User as DjangoUser
from shopback.refunds.models import Refund,RefundProduct
from shopback.items.models import Product

__author__ = 'meixqhi'


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id','tid','oid','num_iid','buyer_nick','total_fee','refund_fee','payment'
                    ,'company_name','sid','has_good_return','is_reissue','created','good_status','order_status','status')
    list_display_links = ('refund_id','tid','buyer_nick')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']
    
    #--------设置页面布局----------------
    fieldsets =(('重要信息', {
                    'classes': ('expand',),
                    'fields': (('tid','user','buyer_nick'),
                               ('has_good_return','good_status','status'),
                               'desc')
                }),
                ('参考信息:', {
                    'classes': ('collapse',),
                    'fields': (('oid','title','seller_id','seller_nick'),
                               ('num_iid','total_fee','refund_fee','payment')
                                ,('company_name','sid','is_reissue')
                                ,('cs_status','order_status','reason'))
                }))

     #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':35})},
    }
    
    list_filter   = ('user','has_good_return','good_status','is_reissue','order_status','status',)
    search_fields = ['refund_id','tid','oid','sid','buyer_nick']
    
    #标记为已处理
    def tag_as_finished(self,request,queryset):
        
        http_referer = request.META.get('HTTP_REFERER')
        for refund in queryset:
            refund.is_reissue = True
            refund.save()
            
        return HttpResponseRedirect(http_referer)
    
    tag_as_finished.short_description = u"标记为已处理"
    
    #更新退货款订单
    def pull_all_refund_orders(self,request,queryset):
        
        http_referer = request.META.get('HTTP_REFERER')
        
        from shopback.refunds.tasks import updateAllUserRefundOrderTask
        updateAllUserRefundOrderTask(days=7)
        
        return HttpResponseRedirect(http_referer)
    
    pull_all_refund_orders.short_description = u"更新退货款订单"
    
    actions = ['tag_as_finished','pull_all_refund_orders']
    

admin.site.register(Refund,RefundAdmin)
  
  
class RefundProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id', 'title', 'outer_sku_id','show_Product_Price','buyer_nick','buyer_mobile','buyer_phone','trade_id'
                    ,'out_sid','company','can_reuse','is_finish','created','modified','memo')
    list_display_links = ('id','outer_id')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter   = ('can_reuse','is_finish')
    search_fields = ['buyer_nick','buyer_mobile','buyer_phone','trade_id','out_sid']
    
    #标记为已处理
    def tag_as_finished(self,request,queryset):
        
        http_referer = request.META.get('HTTP_REFERER')
        for prod in queryset:
            prod.is_finish = True
            prod.save()
            
        return HttpResponseRedirect(http_referer)
    
    tag_as_finished.short_description = u"标记为已处理"

    def show_Product_Price(self, obj):
        outer_id = obj.outer_id
        pro = Product.objects.filter(outer_id=outer_id)
        if pro.exists():
            return pro[0].agent_price
        else:
            return None
    show_Product_Price.allow_tags = True
    show_Product_Price.short_description = u"出售价格"

    
    actions = ['tag_as_finished',]

admin.site.register(RefundProduct,RefundProductAdmin)

