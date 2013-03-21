#-*- coding:utf8 -*-
from django.contrib import admin
from django.http import HttpResponseRedirect
from shopback.refunds.models import Refund,RefundProduct

__author__ = 'meixqhi'


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id','tid','oid','num_iid','buyer_nick','total_fee','refund_fee','payment'
                    ,'company_name','sid','has_good_return','is_reissue','created','good_status','order_status','status')
    list_display_links = ('refund_id','tid','buyer_nick')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']
    
    list_filter   = ('seller_nick','has_good_return','good_status','is_reissue','order_status','status',)
    search_fields = ['refund_id','tid','oid','sid','buyer_nick']
    
    #标记为已处理
    def tag_as_finished(self,request,queryset):
        
        http_referer = request.META.get('HTTP_REFERER')
        for refund in queryset:
            refund.is_reissue = True
            refund.save()
            
        return HttpResponseRedirect(http_referer)
    
    tag_as_finished.short_description = u"标记为已处理"
    
    actions = ['tag_as_finished',]
    

admin.site.register(Refund,RefundAdmin)
  
  
class RefundProductAdmin(admin.ModelAdmin):
    list_display = ('id','outer_id','outer_sku_id','buyer_nick','buyer_mobile','buyer_phone','trade_id'
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
    
    actions = ['tag_as_finished',]

admin.site.register(RefundProduct,RefundProductAdmin)

