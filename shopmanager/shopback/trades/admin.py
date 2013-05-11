#-*- coding:utf8 -*-
import json
import time
import datetime
from django.contrib import admin
from django.db import models
from django.views.decorators.csrf import csrf_protect
from django.forms import TextInput, Textarea
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.contrib.admin import SimpleListFilter
from django.conf import settings
from celery import group
from shopback.orders.models import Trade
from shopback.items.models import Product,ProductSku
from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade,ReplayPostTrade,merge_order_maker,merge_order_remover,SYS_TRADE_STATUS
from shopback import paramconfig as pcfg
from shopback.fenxiao.models import PurchaseOrder
from shopback.trades.tasks import sendTaobaoTradeTask
from shopback.trades import permissions as perms
from shopback.base import log_action,User, ADDITION, CHANGE
from shopback.signals import rule_signal
from auth.utils import parse_datetime,pinghost
from auth import apis
import logging 

logger =  logging.getLogger('tradepost.handler')

__author__ = 'meixqhi'

class MergeOrderInline(admin.TabularInline):
    
    model = MergeOrder
    fields = ('oid','outer_id','outer_sku_id','title','price','payment','num','sku_properties_name','out_stock',
                    'is_merge','is_rule_match','is_reverse_order','gift_type','refund_id','refund_status','status','sys_status')
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('trades.can_trade_modify'):
            return self.readonly_fields + ('oid','outer_id','outer_sku_id','is_merge',
                                           'is_reverse_order','operator','gift_type','status','refund_status')
        return self.readonly_fields
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'12'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }

class TradeStatusFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    title = u'系统状态'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'sys_status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return SYS_TRADE_STATUS

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        status_name  = self.value()
        if not status_name:
            return queryset
        elif status_name == pcfg.WAIT_AUDIT_STATUS:
            return queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_CHECK_BARCODE_STATUS
                                ,pcfg.WAIT_SCAN_WEIGHT_STATUS)).exclude(reason_code='',is_express_print=True)
        else:
            return queryset.filter(sys_status=status_name)
                


class MergeTradeAdmin(admin.ModelAdmin):
    list_display = ('trade_id_link','popup_tid_link','user','buyer_nick_link','type','payment','pay_time','consign_time'
                    ,'status','sys_status','logistics_company','reason_code','is_picking_print','is_express_print'
                    ,'can_review','operator','created','weight_time')
    #list_display_links = ('trade_id_link','popup_tid_link')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    change_list_template  = "admin/trades/change_list.html"
    change_form_template  = "admin/trades/change_trade_form.html"
    
    date_hierarchy = 'created'
    ordering = ['-sys_status','-priority','pay_time',]
    list_per_page = 100
    
    def trade_id_link(self, obj):
        return ('<a href="%d/">%d</a><a href="javascript:void(0);"  trade_id="%d">'
                +'<img src="/static/img/tags.png" class="icon-tags" alt="系统备注"/></a>'
                +'<a href="javascript:void(0);"  trade_id="%d">'
                +'<img src="/static/img/regular.jpg" class="icon-tags" alt="定时提醒明天"/></a>')%(obj.id,obj.id,obj.id,obj.id)
    trade_id_link.allow_tags = True
    trade_id_link.short_description = "ID"
    
    def popup_tid_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);">%s</a>' %(obj.id,obj.tid and str(obj.tid) or '' )
    popup_tid_link.allow_tags = True
    popup_tid_link.short_description = "淘宝单号" 
    
    def buyer_nick_link(self, obj):
        symbol_link = obj.buyer_nick

        if  obj.sys_status in (pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
            symbol_link = '<a href="javascript:void(0);" class="check-order" trade_id="%d" >%s</a>'%(obj.id,symbol_link) 
        return symbol_link
    buyer_nick_link.allow_tags = True
    buyer_nick_link.short_description = "买家昵称" 

    inlines = [MergeOrderInline]
    
    list_filter   = (TradeStatusFilter,'status','user','type','has_out_stock','has_refund','has_rule_match','has_sys_err',
                     'has_merge','has_memo','is_picking_print','is_express_print','can_review','is_locked')

    search_fields = ['id','buyer_nick','tid','operator','out_sid','receiver_name','receiver_mobile','receiver_phone']
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/checkorder.css")}
        js = ("script/admin/adminpopup.js",)
        
    #--------设置页面布局----------------
    fieldsets =(('订单基本信息:', {
                    'classes': ('collapse',),
                    'fields': (('tid','user','type','status','seller_id'),('buyer_nick','seller_nick','pay_time','total_num')
                               ,('total_fee','payment','discount_fee','adjust_fee','post_fee')
                               ,('seller_cod_fee','buyer_cod_fee','cod_fee','cod_status','alipay_no')
                               ,('modified','consign_time','created','weight_time')
                               ,('buyer_message','seller_memo','sys_memo'))
                }),
                ('收货人及物流信息:', {
                    'classes': ('expand',),
                    'fields': (('receiver_name','receiver_state','receiver_city','receiver_district')
                            ,('receiver_address','receiver_zip','receiver_mobile','receiver_phone')
                            ,('shipping_type','logistics_company','out_sid'))
                }),
                ('系统内部信息:', {
                    'classes': ('collapse',),
                    'fields': (('has_sys_err','has_memo','has_refund','has_out_stock','has_rule_match','has_merge'
                                ,'is_send_sms','is_picking_print','is_express_print','can_review')
                               ,('priority','remind_time','reason_code','refund_num')
                               ,('is_locked','post_cost','operator','weight','sys_status',))
                }))

    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':6, 'cols':35})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('trades.can_trade_modify'):
            return self.readonly_fields + ('tid','reason_code','has_rule_match','has_merge','has_memo','payment','post_fee','tid','user','type'
                                           'is_locked','operator','can_review','is_picking_print','is_express_print','sys_status','status')
        return self.readonly_fields
    
    def get_actions(self, request):
        
        user = request.user
        actions = super(MergeTradeAdmin, self).get_actions(request)

        if not perms.has_delete_trade_permission(user) and 'delete_selected' in actions:
            del actions['delete_selected']
        if not perms.has_sync_post_permission(user) and 'sync_trade_post_taobao' in actions:
            del actions['sync_trade_post_taobao']
        if not perms.has_merge_order_permission(user) and 'merge_order_action' in actions:
            del actions['merge_order_action']
        if not perms.has_pull_order_permission(user) and 'pull_order_action' in actions:
            del actions['pull_order_action']
        if not perms.has_unlock_trade_permission(user) and 'unlock_trade_action' in actions:
            del actions['unlock_trade_action']
        return actions
    
    def change_view(self, request, extra_context=None, **kwargs):

        return super(MergeTradeAdmin, self).change_view(request, extra_context)  
        
    #重写订单视图
    def changelist_view(self, request, extra_context=None, **kwargs):

        return super(MergeTradeAdmin, self).changelist_view(request, extra_context)     
    
    def response_change(self, request, obj, *args, **kwargs):
        #订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name

        pk_value = obj._get_pk_val()
        operate_success = False
        if request.POST.has_key("_save_audit"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS and not obj.reason_code and not obj.has_rule_match and not obj.has_refund\
                 and not obj.has_out_stock and obj.logistics_company and not obj.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE):
                try:
                    MergeTrade.objects.filter(id=obj.id,reason_code='').update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
                except Exception,exc:
                    logger.error(exc.message,exc_info=True)
                    operate_success = False
                else:
                    operate_success = True
                    
            if operate_success:
                rule_signal.send(sender='payment_rule',trade_id=obj.id) 
                msg = u"审核通过"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"审核未通过（请确保订单状态为问题单，无退款，无问题编码，无匹配，无缺货, 是否手动合单，已选择快递）")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_invalid"):
            if obj.sys_status in (pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_CHECK_BARCODE_STATUS):
                obj.sys_status=pcfg.INVALID_STATUS
                obj.save()
                msg = u"订单已作废"
                self.message_user(request, msg)
                
                log_action(request.user.id,obj,CHANGE,msg)
                
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"作废未成功（请确保订单状态为问题单）")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_uninvalid"):
            if obj.sys_status==pcfg.INVALID_STATUS:
                obj.sys_status=pcfg.WAIT_AUDIT_STATUS
                obj.save()
                msg = u"订单已入问题单"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单非作废状态,不需反作废")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_regular"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS and obj.remind_time:
                obj.sys_status=pcfg.REGULAR_REMAIN_STATUS
                obj.save()
                msg = u"订单定时时间:%s"%obj.remind_time
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单不是问题单或没有设定提醒时间")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_unregular"):
            if obj.sys_status==pcfg.REGULAR_REMAIN_STATUS:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.WAIT_AUDIT_STATUS,remind_time=None)
                msg = u"订单定时已取消"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单不在定时提醒区，不需要取消定时")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_split"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS:
                if obj.has_merge:
                    merge_order_remover(obj.tid)
                else:
                    obj.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                msg = u"订单已取消合并状态"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"该订单不是问题单,或没有合并子订单")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_save"):
            msg = u'%(name)s "%(obj)s" 保存成功.'% {'name': force_unicode(verbose_name), 'obj': force_unicode(obj)}
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_finish"):
            if obj.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
                obj.sys_status = pcfg.FINISHED_STATUS
                obj.weight_time = datetime.datetime.now()
                obj.save()
                msg = u'%(name)s "%(obj)s" 订单手动修改已完成.'% {'name': force_unicode(verbose_name), 'obj': force_unicode(obj)} 
                log_action(request.user.id,obj,CHANGE,msg)
            else:
                msg = u"订单不在待扫描验货或待扫描称重，不能修改为已完成状态"
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)
        
        return super(MergeTradeAdmin, self).response_change(request, obj, *args, **kwargs)
    
    #--------定义action----------------
    #合并订单
    def merge_order_action(self,request,queryset):
        
        trade_ids = [t.id for t in queryset]
        is_merge_success = False
        queryset  = queryset.filter(type__in=(pcfg.FENXIAO_TYPE,pcfg.TAOBAO_TYPE))
        myset = queryset.exclude(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.ON_THE_FLY_STATUS,
                                pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS))
        postset = queryset.filter(sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS))
        if queryset.count()<2 or myset.count()>0 or postset.count()>1:
            trades = queryset
            is_merge_success = False
            fail_reason = u'订单不符合合并条件（合并订单必须两单以上，订单类型为一口价，分销,订单状态在问题单或待扫描）'
        else:
            merge_trade_ids  = []     #合单成的订单ID
            fail_reason      = ''
            #如果有订单在待扫描，则将子订单与主订单合并，发货，完成
            if postset.count()==1:
                main_trade  = postset[0]
                sub_trades  = queryset.filter(sys_status=pcfg.WAIT_AUDIT_STATUS)
                for trade in sub_trades:
                    is_merge_success = False 
                    is_merge_success = merge_order_maker(trade.tid,main_trade.tid)

                    if is_merge_success:
                        merge_trade_ids.append(str(trade.tid))
                        trade.out_sid    = main_trade.out_sid
                        trade.logistics_company = main_trade.logistics_company
                        trade.sys_status = pcfg.FINISHED_STATUS
                        trade.operator   = main_trade.operator
                        trade.consign_time = main_trade.consign_time
                        trade.save()
                        
                        log_action(request.user.id,trade,CHANGE,u'订单并入主订单（%d），并发货完成'%main_trade.tid)
                        try:
                            trade.send_trade_to_taobao(pcfg.SUB_TRADE_COMPANEY_CODE,trade.out_sid)
                        except:
                            log_action(request.user.id,trade,CHANGE,u'订单合并发货失败')
                                        
                if len(merge_trade_ids)<sub_trades.count():
                    fail_reason = u'部分订单未合并成功'
                    is_merge_success = False 
                else:
                    #合并后金额匹配
                    rule_signal.send(sender='payment_rule',trade_id=main_trade.id)
                    is_merge_success = True
                log_action(request.user.id,main_trade,CHANGE,u'合并订单(%s)'%','.join(merge_trade_ids))
            else:
                queryset = queryset.filter(sys_status=pcfg.WAIT_AUDIT_STATUS).order_by('pay_time')	
                merge_trades = queryset.filter(has_merge=True)
                if merge_trades.count()>0:
                    main_trade = merge_trades[0]
                else:
                    main_trade = queryset[0] #主订单
                
                queryset = queryset.exclude(tid=main_trade.tid)		
                main_full_addr = main_trade.buyer_full_address #主订单收货人地址
                
                for trade in queryset:
                    if trade.buyer_full_address != main_full_addr:
                        is_merge_success = False
                        fail_reason      = u'订单地址不同'
                        break
                    is_merge_success = merge_order_maker(trade.tid,main_trade.tid)
                    if not is_merge_success:
                        fail_reason      = u'订单合并错误'
                        break
                    merge_trade_ids.append(trade.tid)
                
                if is_merge_success:
                    MergeTrade.objects.filter(tid__in=merge_trade_ids).update(sys_status=pcfg.ON_THE_FLY_STATUS)
                    #合并后金额匹配
                    rule_signal.send(sender='payment_rule',trade_id=main_trade.id)
                    log_action(request.user.id,main_trade,CHANGE,u'合并订单,主订单:%d,子订单:%s'%(main_trade.id,','.join([str(id) for id in merge_trade_ids])))
                elif merge_trade_ids:
                    merge_order_remover(main_trade.tid)
            
            trades = MergeTrade.objects.filter(id__in=trade_ids)
        return render_to_response('trades/mergesuccess.html',{'trades':trades,'merge_status':is_merge_success,'fail_reason':fail_reason},
                                  context_instance=RequestContext(request),mimetype="text/html") 	

    merge_order_action.short_description = "合并订单".decode('utf8')

    #更新下载订单
    def pull_order_action(self, request, queryset):
        queryset = queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,''))
        pull_success_ids = []
        pull_fail_ids    = []
        for trade in queryset:
            #如果有合单，则取消合并
            if trade.sys_status != pcfg.WAIT_AUDIT_STATUS:
                continue
            if trade.has_merge:
                merge_order_remover(trade.tid)
            seller_id  = trade.user.visitor_id
            trade.sys_status = ''
            trade.reason_code=''
            trade.has_sys_err=False
            trade.has_merge=False
            trade.has_memo=False
            trade.has_rule_match=False
            trade.has_out_stock=False
            trade.has_refund=False
            trade.save()
            #减去商品的待发货数，订单重新入库时（判断是否缺货功能），会重新肩上
            wait_post_orders = trade.merge_trade_orders.filter(sys_status=pcfg.IN_EFFECT
                            ,gift_type__in=(pcfg.REAL_ORDER_GIT_TYPE,pcfg.COMBOSE_SPLIT_GIT_TYPE))
            for order in wait_post_orders:
                if order.outer_sku_id:
                    try:
                        product_sku = ProductSku.objects.get(product__outer_id=order.outer_id,outer_id=order.outer_sku_id)
                    except:
                        pass
                    else:
                        product_sku.update_waitpostnum_incremental(order.num)
                elif order.outer_id:
                    try:
                        product = Product.objects.get(outer_id=order.outer_id)
                    except:
                        pass
                    else:
                        product.update_waitpostnum_incremental(order.num) 
                        
            try:
                trade.merge_trade_orders.all().delete()
                if trade.type == pcfg.TAOBAO_TYPE:
                    response = apis.taobao_trade_fullinfo_get(tid=trade.tid,tb_user_id=seller_id)
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    Trade.save_trade_through_dict(seller_id,trade_dict)
                elif trade.type == pcfg.FENXIAO_TYPE:
                    purchase = PurchaseOrder.objects.get(id=trade.tid)
                    response_list = apis.taobao_fenxiao_orders_get(purchase_order_id=purchase.fenxiao_id,tb_user_id=seller_id)
                    orders_list = response_list['fenxiao_orders_get_response']
                    if orders_list['total_results']>0:
                        o = orders_list['purchase_orders']['purchase_order'][0]
                        PurchaseOrder.save_order_through_dict(seller_id,o)    
            except Exception,exc:
                logger.error('pull error '+exc.message,exc_info=True)
                trade.append_reason_code(pcfg.PULL_ORDER_ERROR_CODE)
                pull_fail_ids.append(trade.tid)
            else:
                pull_success_ids.append(trade.tid)
                log_action(request.user.id,trade,CHANGE,u'重新下载订单')
        success_trades = MergeTrade.objects.filter(tid__in=pull_success_ids)
        fail_trades    = MergeTrade.objects.filter(tid__in=pull_fail_ids)
        return render_to_response('trades/repullsuccess.html',{'success_trades':success_trades,'fail_trades':fail_trades},
                                  context_instance=RequestContext(request),mimetype="text/html") 

    pull_order_action.short_description = "重新下单".decode('utf8')
    
    def get_trade_pickle_list_data(self,post_trades):
        """生成配货单数据列表"""
        
        trade_items = {}
        for trade in post_trades:
            used_orders = trade.merge_trade_orders.filter(sys_status=pcfg.IN_EFFECT)\
                .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
            for order in used_orders:
                outer_id = order.outer_id or str(order.num_iid)
                outer_sku_id = order.outer_sku_id or str(order.sku_id)
                
                if trade_items.has_key(outer_id):
                    trade_items[outer_id]['num'] += order.num
                    skus = trade_items[outer_id]['skus']
                    if skus.has_key(outer_sku_id):
                        skus[outer_sku_id]['num'] += order.num
                    else:
                        prod_sku = None
                        try:
                            prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
                        except:
                            prod_sku = None
                        prod_sku_name = (prod_sku.properties_alias or prod_sku.properties_name ) if prod_sku else order.sku_properties_name
                        skus[outer_sku_id] = {'sku_name':prod_sku_name,'num':order.num}
                else:
                    prod = None
                    try:
                        prod = Product.objects.get(outer_id=outer_id)
                    except:
                        prod = None
                        
                    prod_sku = None
                    try:
                        prod_sku = ProductSku.objects.get(outer_id=outer_id,product__outer_id=outer_id)
                    except:
                        prod_sku = None
                    prod_sku_name =prod_sku.properties_name if prod_sku else order.sku_properties_name
                        
                    trade_items[outer_id]={
                                           'num':order.num,
                                           'title': prod.name if prod else order.title,
                                           'skus':{outer_sku_id:{'sku_name':prod_sku_name,'num':order.num}}
                                           }
                     
        trade_list = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
        for trade in trade_list:
            skus = trade[1]['skus']
            trade[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['num'],reverse=True)
        
        return trade_list
        
    #淘宝后台同步发货
    def sync_trade_post_taobao(self, request, queryset):
        
        pingstatus = pinghost(settings.TAOBAO_API_HOSTNAME)
        if pingstatus:
            return HttpResponse('<body style="text-align:center;"><h1>当前网络不稳定，请稍后再试...</h1></body>')
        
        user_id   = request.user.id
        trade_ids = [t.id for t in queryset]
        
        prapare_trades = queryset.filter(is_picking_print=True,is_express_print=True,sys_status=pcfg.WAIT_PREPARE_SEND_STATUS
                                         ,reason_code='',status=pcfg.WAIT_SELLER_SEND_GOODS).exclude(out_sid='')#,operator=request.user.username
        
        if prapare_trades.count() > 0:
            try:                                     
                send_tasks = group([ sendTaobaoTradeTask.s(user_id,trade.id) for trade in prapare_trades])()
                send_tasks.get()
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                return HttpResponse('<body style="text-align:center;"><h1>发货任务执行出错:（%s）！</h1></body>'%exc.message) 
        queryset = MergeTrade.objects.filter(id__in=trade_ids)
        wait_prepare_trades = queryset.filter(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,is_picking_print=True
                                              ,is_express_print=True).exclude(out_sid='')#,operator=request.user.username
        for prepare_trade in wait_prepare_trades:
            prepare_trade.is_picking_print=False
            prepare_trade.is_express_print=False
            prepare_trade.sys_status=pcfg.WAIT_AUDIT_STATUS
            prepare_trade.save()
            log_action(user_id,prepare_trade,CHANGE,u'订单未发货被拦截入问题单')
        
        post_trades = queryset.filter(sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        trade_list = self.get_trade_pickle_list_data(post_trades)
        
        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.seller_nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['company_name'] = trade.logistics_company.name 
            trade_dict['out_sid']    = trade.out_sid
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)
        
        response_dict = {'trades':trades,'trade_items':trade_list}
        
        try:
            ReplayPostTrade.objects.create(operator=request.user.username,
                                           order_num=len(trade_ids),post_data=json.dumps(response_dict))
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            
        return render_to_response('trades/tradepostsuccess.html',response_dict,
                                  context_instance=RequestContext(request),mimetype="text/html")
                          
    sync_trade_post_taobao.short_description = "同步发货".decode('utf8')
    
    
    def unlock_trade_action(self, request, queryset):
        """ 解除订单锁定 """
        trade_ids = [t.id for t in queryset]
        unlockable_trades = queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS),
                        is_locked=True)
        
        for trade in unlockable_trades:
            operator = trade.operator
            trade.is_locked = False
            trade.operator  = ''
            trade.save()
            log_action(request.user.id,trade,CHANGE,u'解除订单锁定(前锁定人:%s)'%operator)
                        
        success_trades = MergeTrade.objects.filter(id__in=trade_ids,is_locked=False)
        
        fail_trades    = MergeTrade.objects.filter(id__in=trade_ids,is_locked=True)
        
        
        
        return render_to_response('trades/unlock_trade_status_template.html',{'success_trades':success_trades,'fail_trades':fail_trades},
                                  context_instance=RequestContext(request),mimetype="text/html") 

    unlock_trade_action.short_description = "订单解锁".decode('utf8')
    
    actions = ['sync_trade_post_taobao','merge_order_action','pull_order_action','unlock_trade_action']
   

admin.site.register(MergeTrade,MergeTradeAdmin)


class MergeOrderAdmin(admin.ModelAdmin):
    list_display = ('id','tid','oid','outer_id','outer_sku_id','seller_nick','buyer_nick','price','num','sku_properties_name',
                    'out_stock','is_rule_match','payment','refund_id','refund_status','cid','status')
    list_display_links = ('oid','tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','status','gift_type','refund_status','out_stock','is_rule_match')
    search_fields = ['oid','tid','buyer_nick','outer_id','outer_sku_id']


admin.site.register(MergeOrder,MergeOrderAdmin)


class MergeBuyerTradeAdmin(admin.ModelAdmin):
    list_display = ('sub_tid','main_tid','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['sub_tid','main_tid']
    

admin.site.register(MergeBuyerTrade,MergeBuyerTradeAdmin)


class ReplayPostTradeAdmin(admin.ModelAdmin):
    list_display = ('id','operator','order_num','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']
    search_fields = ['operator','id']
    
    def replay_post(self, request, queryset):
        object = queryset.order_by('-created')[0]
        replay_data = json.loads(object.post_data)
        return render_to_response('trades/tradepostsuccess.html',replay_data,
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    replay_post.short_description = "重现发货清单".decode('utf8')
    
    actions = ['replay_post']

admin.site.register(ReplayPostTrade,ReplayPostTradeAdmin)
