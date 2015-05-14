#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.forms import TextInput, Textarea, FloatField
from django.http import HttpResponseRedirect

from shopback.base import log_action,User, ADDITION, CHANGE
from shopback.trades.filters import DateFieldListFilter
from .models import (SaleTrade,
                     SaleOrder,
                     TradeCharge,
                     Customer,
                     Register,
                     District,
                     UserAddress,
                     SaleRefund)

import logging
logger = logging.getLogger('django.request')

class SaleOrderInline(admin.TabularInline):
    
    model = SaleOrder
    fields = ('oid','outer_id','title','outer_sku_id','sku_name','payment','num','refund_fee','refund_status','status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields + ('oid',))
        if not request.user.is_superuser:
            readonly_fields.update(('outer_id','outer_sku_id'))
        return tuple(readonly_fields)
    
    

class SaleTradeAdmin(admin.ModelAdmin):
    list_display = ('id','tid','buyer_nick','channel','payment','pay_time','created','status')
    list_display_links = ('id','tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter   = ('status','channel',('created',DateFieldListFilter))
    search_fields = ['tid','id','receiver_mobile']
    
    inlines = [SaleOrderInline]
    
    #-------------- 页面布局 --------------
    fieldsets =((u'订单基本信息:', {
                    'classes': ('expand',),
                    'fields': (('tid','buyer_nick','channel','status')
                               ,('trade_type','total_fee','payment','post_fee')
                               ,('pay_time','consign_time','charge')
                               ,('buyer_message','seller_memo')
                               )
                }),
                (u'收货人及物流信息:', {
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
    
    list_display = ('id','name','full_name','parent_id','grade','sort_order')
    search_fields = ['id','parent_id','name']
    
    list_filter = ('grade',)

admin.site.register(District, DistrictAdmin)


class UserAddressAdmin(admin.ModelAdmin):
    
    list_display = ('id','cus_uid','receiver_name','receiver_state',
                    'receiver_city','receiver_mobile','default','status')
    search_fields = ['cus_uid','receiver_mobile']
    
    list_filter = ('default','status')

admin.site.register(UserAddress, UserAddressAdmin)

class SaleRefundChangeList(ChangeList):
    
    def get_query_set(self,request):
        
        search_q = request.GET.get('q','').strip()
        if search_q :
            
            refunds = SaleRefund.objects.none()
            trades = SaleTrade.objects.filter(tid=search_q)
            if trades.count() > 0 and search_q.isdigit():
                
                refunds = SaleRefund.objects.filter(models.Q(trade_id=trades[0].id)|
                                                    models.Q(order_id=search_q)|
                                                    models.Q(refund_id=search_q)|
                                                    models.Q(mobile=search_q)|
                                                    models.Q(trade_id=search_q))
                
            elif trades.count() > 0:
                refunds = SaleRefund.objects.filter(trade_id=trades[0].id)
                
            elif search_q.isdigit():
                refunds = SaleRefund.objects.filter(models.Q(order_id=search_q)|
                                                    models.Q(refund_id=search_q)|
                                                    models.Q(mobile=search_q)|
                                                    models.Q(trade_id=search_q))
            
            return refunds
        
        return super(SaleRefundChangeList,self).get_query_set(request)

from flashsale.xiaolumm.models import XiaoluMama,CarryLog

class SaleRefundAdmin(admin.ModelAdmin):
    
    list_display = ('refund_no','order_no','title','refund_fee','has_good_return','has_good_change','created','status')
    
    list_filter = ('status','good_status','has_good_return','has_good_change')
    
    search_fields = ['trade_id','order_id','refund_id','mobile']
    
    def order_no(self, obj):
        strade = SaleTrade.objects.get(id=obj.trade_id)
        return strade.tid
    
    order_no.allow_tags = True
    order_no.short_description = "交易编号" 
    
    
    #-------------- 页面布局 --------------
    fieldsets =(('基本信息:', {
                    'classes': ('expand',),
                    'fields': (('refund_no','trade_id','order_id')
                               ,('title','sku_name',)
                               ,('payment','total_fee',)
                               ,('company_name','sid')
                               ,('reason','desc')
                               )
                }),
                ('内部信息:', {
                    'classes': ('collapse',),
                    'fields': (('buyer_nick','mobile','phone',),
                               ('item_id','sku_id','refund_id','charge',))

                }),
                ('审核信息:', {
                    'classes': ('expand',),
                    'fields': (('has_good_return','has_good_change',)
                                ,('refund_num','refund_fee')
                                ,('feedback')
                                ,('good_status','status'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':35})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields or [])
        if not request.user.is_superuser:
            readonly_fields.update(('refund_no','trade_id','order_id','payment','total_fee',
                                   'reason','desc','refund_id','charge','status'))

        return readonly_fields
    
    def get_changelist(self, request, **kwargs):
        return SaleRefundChangeList
    
    def response_change(self, request, obj, *args, **kwargs):
        #订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name
        
        pk_value = obj._get_pk_val()
        if request.POST.has_key("_refund_confirm"):
            try:
                
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):
                    
                    strade = SaleTrade.objects.get(id=obj.trade_id)
                    customer = Customer.objects.get(id=strade.buyer_id)
                    
                    if strade.channel == SaleTrade.WALLET :
                        payment = int(obj.refund_fee * 100)
                        xlmm_queryset = XiaoluMama.objects.filter(openid=customer.unionid)
                        urows = xlmm_queryset.update(cash=models.F('cash')+payment)
                        
                        if urows > 0:
                            xlmm = xlmm_queryset[0]
                            CarryLog.objects.create(xlmm=xlmm.id,
                                        order_num=strade.id,
                                        buyer_nick=strade.buyer_nick,
                                        value=payment,
                                        log_type=CarryLog.REFUND_RETURN,
                                        carry_type=CarryLog.CARRY_IN)
                        obj.status = SaleRefund.REFUND_SUCCESS
                        obj.save()
                        
                    elif obj.refund_fee > 0 and obj.charge:
                        import pingpp
                        pingpp.api_key = settings.PINGPP_APPKEY
                        ch = pingpp.Charge.retrieve(obj.charge)
                        re = ch.refunds.create(description=obj.refund_desc, 
                                               amount=int(obj.refund_fee*100))
                        obj.refund_id = re.id
                        obj.status = SaleRefund.REFUND_APPROVE
                        obj.save()
                    
                    log_action(request.user.id,obj,CHANGE,'退款审核通过:%s'%obj.refund_id)
                    self.message_user(request, '退款单审核通过')
                else:
                    self.message_user(request, '退款单状态不可申审核')
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                self.message_user(request, '系统出错:%s'%exc.message)
            
            return HttpResponseRedirect("../%s/" % pk_value)
        
        elif request.POST.has_key("_refund_refuse"):
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):

                    obj.status = SaleRefund.REFUND_REFUSE_BUYER
                    obj.save()
                    log_action(request.user.id,obj,CHANGE,'驳回重申')
                    self.message_user(request, '驳回成功')
                else:
                    self.message_user(request, '退款单状态不可申审核')    
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                self.message_user(request, '系统出错:%s'%exc.message)
                
            return HttpResponseRedirect("../%s/" % pk_value)
        
        return super(SaleRefundAdmin, self).response_change(request, obj, *args, **kwargs)
    

admin.site.register(SaleRefund, SaleRefundAdmin)

