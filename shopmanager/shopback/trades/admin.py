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
from django.contrib.admin.models import LogEntry, User, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.conf import settings
from shopback.orders.models import Trade
from shopback.items.models import Product,ProductSku
from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade,ReplayPostTrade,merge_order_maker,merge_order_remover
from shopback import paramconfig as pcfg
from shopback.fenxiao.models import PurchaseOrder
from shopback.base import log_action
from shopback.signals import rule_signal
from auth import apis
from auth.utils import parse_datetime
import logging 

logger =  logging.getLogger('tradepost.handler')

__author__ = 'meixqhi'

class SubTradePostException(Exception):

    def __init__(self,msg=''):
        self.msg  = msg

    def __str__(self):
        return self.msg

def has_modify_trade_info_status_permission(request, obj=None):
     if request.user.has_perm('mergetrade.can_trade_modify'):
         return True
     return False

class MergeOrderInline(admin.TabularInline):
    
    model = MergeOrder
    fields = ('oid','outer_id','outer_sku_id','title','price','payment','num','sku_properties_name','out_stock',
                    'is_merge','is_rule_match','gift_type','refund_id','refund_status','status','sys_status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'12'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


class MergeTradeAdmin(admin.ModelAdmin):
    list_display = ('id','popup_tid_link','user','buyer_nick_link','type','payment','created','pay_time','consign_time'
                    ,'status','logistics_company','is_picking_print','is_express_print','is_send_sms'
                    ,'reason_code','has_memo','has_refund','sys_status','operator','remind_time')
    list_display_links = ('id','popup_tid_link')
    #list_editable = ('update_time','task_type' ,'is_success','status')
    
    #change_list_template = "admin/trades/change_list_result.html"
    change_form_template  = "admin/trades/change_trade_form.html"
    
    date_hierarchy = 'created'
    ordering = ['-priority','pay_time',]
    list_per_page = 100
     
    def popup_tid_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);">%d</a>' %(obj.id,obj.tid)
    popup_tid_link.allow_tags = True
    popup_tid_link.short_description = "淘宝ID" 
    
    def buyer_nick_link(self, obj):
        symbol_link = obj.buyer_nick
        if obj.sys_status in (pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_CHECK_BARCODE_STATUS):
            symbol_link = '<a href="javascript:void(0);" class="check-order" trade_id="%d" >%s</a>'%(obj.id,symbol_link) 
        return symbol_link
    buyer_nick_link.allow_tags = True
    buyer_nick_link.short_description = "买家昵称" 

    inlines = [MergeOrderInline]
    
    list_filter   = ('sys_status','status','user','type','has_out_stock','has_refund','has_rule_match','has_sys_err',
                     'has_merge','is_picking_print','is_express_print')
    search_fields = ['id','buyer_nick','tid','operator','out_sid','receiver_name']
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/checkorder.css")}
        js = ("script/admin/adminpopup.js",)
        
    #--------设置页面布局----------------
    fieldsets =(('订单基本信息:', {
                    'classes': ('collapse',),
                    'fields': (('tid','user','type','status','seller_id'),('buyer_nick','seller_nick','pay_time','total_num')
                               ,('total_fee','payment','discount_fee','adjust_fee','post_fee')
                               ,('seller_cod_fee','buyer_cod_fee','cod_fee','cod_status','alipay_no'),('modified','consign_time','created')
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
                    'fields': (('has_sys_err','has_memo','has_refund','has_out_stock','has_rule_match','has_merge','is_send_sms','is_picking_print','is_express_print')
                               ,('priority','remind_time','reason_code','refund_num')
                               ,('post_cost','operator','weight','sys_status',))
                }))

    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    #重写订单视图
    def changelist_view(self, request, extra_context=None, **kwargs):

        #if not has_modify_trade_info_status_permission(request):
        #    self.readonly_fields=('tid','user','seller_nick','buyer_nick','payment','total_num','discount_fee'
        #             ,'adjust_fee','post_fee','total_fee','alipay_no','seller_cod_fee','buyer_cod_fee','cod_fee'
        #             ,'cod_status','buyer_message','seller_memo','created','pay_time','modified','consign_time'
        #             ,'type','status','shipping_type','operator','is_send_sms','out_sid'
        #             ,'has_memo','has_refund','has_out_stock','has_rule_match','has_merge','sys_status')
            
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
                rule_signal.send(sender='payment_rule',trade_tid=obj.tid) 
                msg = "审核通过"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "审核未通过（请确保订单状态为问题单，无退款，无问题编码，无匹配，无缺货, 是否手动合单，已选择快递）")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_invalid"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.INVALID_STATUS)
                msg = "订单已作废"
                self.message_user(request, msg)
                
                log_action(request.user.id,obj,CHANGE,msg)
                
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "作废未成功（请确保订单状态为问题单）")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_uninvalid"):
            if obj.sys_status==pcfg.INVALID_STATUS:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.WAIT_AUDIT_STATUS)
                msg = "订单已入问题单"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "订单非作废状态,不需反作废")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_regular"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS and obj.remind_time:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.REGULAR_REMAIN_STATUS)
                msg = "订单定时时间:%s"%obj.remind_time
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "订单不是问题单或没有设定提醒时间")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_unregular"):
            if obj.sys_status==pcfg.REGULAR_REMAIN_STATUS:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.WAIT_AUDIT_STATUS,remind_time=None)
                msg = "订单定时已取消"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "订单不在定时提醒区，不需要取消定时")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_split"):
            if obj.sys_status==pcfg.WAIT_AUDIT_STATUS:
                if obj.has_merge:
                    buyertrades = MergeBuyerTrade.objects.filter(main_tid=obj.tid)
                    subtids = [t.sub_tid for t in buyertrades]
                    buyertrades.delete()
                    for subtid in subtids:
                        MergeTrade.objects.get(tid=subtid).remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
                    MergeTrade.objects.filter(tid__in=subtids).update(sys_status=pcfg.WAIT_AUDIT_STATUS)
                    obj.merge_trade_orders.filter(is_merge=True).delete()
                    obj.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
                else:
                    obj.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                msg = "订单已取消合并状态"
                self.message_user(request, msg)
                log_action(request.user.id,obj,CHANGE,msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, "该订单不是问题单,或没有合并子订单")
                return HttpResponseRedirect("../%s/" % pk_value)
        elif request.POST.has_key("_save"):
            msg = ' %(name)s "%(obj)s" 保存成功.'.decode('utf8')% {'name': force_unicode(verbose_name), 'obj': force_unicode(obj)}
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)
        return super(MergeTradeAdmin, self).response_change(request, obj, *args, **kwargs)
    
    #--------定义action----------------

    #合并订单
    def merge_order_action(self,request,queryset):
        
        trade_ids = [t.id for t in queryset]
        myset = queryset.filter(sys_status=pcfg.WAIT_AUDIT_STATUS)
        if queryset.count()<2 or myset.count()!=queryset.count():
            return 
        queryset = queryset.order_by('pay_time')	
        merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[t.tid for t in queryset])
        if merge_buyer_trades.count()>0:
            main_merge_tid = merge_buyer_trades[0].main_tid
            main_trade = MergeTrade.objects.get(tid=main_merge_tid)
        else:
            main_trade = queryset[0] #主订单
        
        queryset = queryset.exclude(tid=main_trade.tid)		
        main_full_addr = main_trade.buyer_full_address #主订单收货人地址
        is_merge_success = False #合单成功
        merge_trade_ids  = []	 #合单成的订单ID
        for trade in queryset:
            if trade.buyer_full_address != main_full_addr:
                is_merge_success = False
                break
            is_merge_success = merge_order_maker(trade.tid,main_trade.tid)
            if not is_merge_success:
                break
            merge_trade_ids.append(trade.tid)
        
        if is_merge_success:
            MergeTrade.objects.filter(tid__in=merge_trade_ids).update(sys_status=pcfg.ON_THE_FLY_STATUS)
        
        elif merge_trade_ids:
            merge_order_remover(main_trade.tid)
        
        trades = MergeTrade.objects.filter(id__in=trade_ids)
        return render_to_response('trades/mergesuccess.html',{'trades':trades,'merge_status':is_merge_success},
                                  context_instance=RequestContext(request),mimetype="text/html") 	

    merge_order_action.short_description = "合并订单".decode('utf8')

    #更新下载订单
    def pull_order_action(self, request, queryset):
        queryset = queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,''))
        pull_success_ids = []
        pull_fail_ids    = []
        for trade in queryset:
            MergeTrade.objects.filter(tid=trade.tid).update(sys_status='')
            try:
                if trade.type == pcfg.TAOBAO_TYPE:
                    response = apis.taobao_trade_fullinfo_get(tid=trade.tid,tb_user_id=trade.seller_id)
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    Trade.save_trade_through_dict(trade.seller_id,trade_dict)
                elif trade.type == pcfg.FENXIAO_TYPE:
                    purchase = PurchaseOrder.objects.get(id=trade.tid)
                    response_list = apis.taobao_fenxiao_orders_get(purchase_order_id=purchase.fenxiao_id,tb_user_id=trade.seller_id)
                    orders_list = response_list['fenxiao_orders_get_response']
                    if orders_list['total_results']>0:
                        o = orders_list['purchase_orders']['purchase_order'][0]
                        PurchaseOrder.save_order_through_dict(trade.seller_id,o)    
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                MergeTrade.objects.filter(tid=trade.tid,reason_code='').update(sys_status=pcfg.WAIT_AUDIT_STATUS)
                pull_fail_ids.append(trade.tid)
            else:
                pull_success_ids.append(trade.tid)
        success_trades = MergeTrade.objects.filter(tid__in=pull_success_ids)
        fail_trades    = MergeTrade.objects.filter(tid__in=pull_fail_ids)
        return render_to_response('trades/repullsuccess.html',{'success_trades':success_trades,'fail_trades':fail_trades},
                                  context_instance=RequestContext(request),mimetype="text/html") 

    pull_order_action.short_description = "重新下单".decode('utf8')
    
    
    #淘宝后台同步发货
    def sync_trade_post_taobao(self, request, queryset):
        trade_ids = [t.id for t in queryset]
        
        prapare_trades = queryset.filter(is_picking_print=True,is_express_print=True,sys_status=pcfg.WAIT_PREPARE_SEND_STATUS
                                         ,operator=request.user.username,reason_code='',status=pcfg.WAIT_SELLER_SEND_GOODS).exclude(out_sid='')

        for trade in prapare_trades:
            
            if trade.sys_status != pcfg.WAIT_PREPARE_SEND_STATUS:
                continue
            if trade.type in (pcfg.DIRECT_TYPE,pcfg.EXCHANGE_TYPE):
                MergeTrade.objects.filter(tid=trade.tid).update(sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS
                                                                ,consign_time=datetime.datetime.now())
                continue 
            
            logistics_company_code = trade.logistics_company.code     
            try:
                merge_buyer_trades = []
                #判断是否有合单子订单
                if trade.has_merge:
                    merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.tid)
                    
                for sub_buyer_trade in merge_buyer_trades:
                    try:
                        sub_trade = MergeTrade.objects.get(tid=sub_buyer_trade.sub_tid)
                        sub_trade.out_sid      = trade.out_sid
                        sub_trade.company_code = logistics_company_code
                        sub_trade.save()
                        response = apis.taobao_logistics_offline_send(tid=sub_trade.tid,out_sid=trade.out_sid
                                                      ,company_code=trade.logistics_company.code,tb_user_id=sub_trade.seller_id)
                        #response = {'logistics_offline_send_response': {'shipping': {'is_success': True}}}
                        if not response['logistics_offline_send_response']['shipping']['is_success']:
                            raise Exception(u'子订单(%d)淘宝发货失败'%sub_trade.tid)
                    except Exception,exc:
                        time.sleep(1)
                        is_post_success = False
                        error_msg = exc.message
                        try:
                            is_post_success = trade.is_post_success()
                        except Exception,exc:
                            error_msg = error_msg+','+exc.message
                            
                        if is_post_success:
                            MergeTrade.objects.filter(tid=sub_trade.tid)\
                               .update(out_sid=trade.out_sid,operator=trade.operator,sys_status=pcfg.FINISHED_STATUS\
                               ,consign_time=datetime.datetime.now())
                        else:
                            sub_trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
                            MergeTrade.objects.filter(tid=sub_trade.tid).update(
                                                sys_status=pcfg.WAIT_AUDIT_STATUS,sys_memo=exc.message,is_picking_print=False,is_express_print=False)
                            raise SubTradePostException(error_msg)
                    else:
                        MergeTrade.objects.filter(tid=sub_trade.tid,sys_status=pcfg.ON_THE_FLY_STATUS).update(out_sid=trade.out_sid
                            ,operator=trade.operator,sys_status=pcfg.FINISHED_STATUS,consign_time=datetime.datetime.now())
                
                response = apis.taobao_logistics_offline_send(tid=trade.tid,out_sid=trade.out_sid
                                              ,company_code=logistics_company_code,tb_user_id=trade.seller_id)  
                #response = {'logistics_offline_send_response': {'shipping': {'is_success': True}}}
                if not response['logistics_offline_send_response']['shipping']['is_success']:
                    raise Exception(u'订单(%d)淘宝发货失败'%trade.tid)
                #else:
                #    raise Exception(u'订单(%d)本地修改日期(%s)与线上修改日期(%s)不一致'%(trade.tid,trade.modified,latest_modified))
            except SubTradePostException,exc:
                trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
                MergeTrade.objects.filter(tid=trade.tid).update(sys_status=pcfg.WAIT_AUDIT_STATUS,sys_memo=exc.message)
                logger.error(exc.message+'--sub post error',exc_info=True)
            except Exception,exc:
                time.sleep(1)
                is_post_success = False
                error_msg = exc.message
                try:
                    is_post_success = trade.is_post_success()
                except Exception,exc:
                    error_msg = error_msg+','+exc.message
                    
                if is_post_success:
                    MergeTrade.objects.filter(tid=trade.tid)\
                        .update(sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS,consign_time=datetime.datetime.now())
                else:
                    trade.append_reason_code(pcfg.POST_MODIFY_CODE)
                    MergeTrade.objects.filter(tid=trade.tid).update(
                                       sys_status=pcfg.WAIT_AUDIT_STATUS,sys_memo=exc.message,is_picking_print=False,is_express_print=False)

                    logger.error(error_msg,exc_info=True)
            else:
                MergeTrade.objects.filter(tid=trade.tid,sys_status=pcfg.WAIT_PREPARE_SEND_STATUS).update(
                    sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS,consign_time=datetime.datetime.now())

        queryset = MergeTrade.objects.filter(id__in=trade_ids)
        queryset.filter(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS).exclude(out_sid='').update(
            is_picking_print=False,is_express_print=False,sys_status=pcfg.WAIT_AUDIT_STATUS)
        post_trades = queryset.filter(sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        trade_items = {}
        for trade in post_trades:
            used_orders = trade.merge_trade_orders.filter(status__in=(pcfg.WAIT_BUYER_CONFIRM_GOODS,pcfg.WAIT_SELLER_SEND_GOODS),
                sys_status=pcfg.IN_EFFECT).exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
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
                            prod_sku = ProductSku.objects.get(outer_id=outer_id)
                        except:
                            prod_sku = None
                        prod_sku_name =prod_sku.properties_name if prod_sku else order.sku_properties_name
                        skus[outer_sku_id] = {'sku_name':prod_sku_name,'num':order.num}
                else:
                    prod = None
                    try:
                        prod = Product.objects.get(outer_id=outer_id)
                    except:
                        prod = None
                    trade_items[outer_id]={
                                           'num':order.num,
                                           'title': prod.name if prod else order.title,
                                           'skus':{outer_sku_id:{'sku_name':order.sku_properties_name,'num':order.num}}
                                           }
                     
        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.seller_nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['pay_time'] = trade.pay_time.strftime('%Y-%m-%d %H:%M:%S')
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)
            
        trade_list = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
        for trade in trade_list:
            skus = trade[1]['skus']
            trade[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['num'],reverse=True)
 
        response_dict = {'trades':trades,'trade_items':trade_list}
        
        try:
            ReplayPostTrade.objects.create(operator=request.user.username,post_data=json.dumps(response_dict))
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            
        return render_to_response('trades/tradepostsuccess.html',response_dict,
                                  context_instance=RequestContext(request),mimetype="text/html")
                          
    sync_trade_post_taobao.short_description = "同步发货".decode('utf8')
    
    actions = ['sync_trade_post_taobao','merge_order_action','pull_order_action']
    
    
    

admin.site.register(MergeTrade,MergeTradeAdmin)


class MergeOrderAdmin(admin.ModelAdmin):
    list_display = ('id','tid','oid','outer_id','outer_sku_id','seller_nick','buyer_nick','price','num_iid','sku_id','num','sku_properties_name',
                    'payment','refund_id','refund_status','cid','status')
    list_display_links = ('oid','tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','status','gift_type','refund_status')
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
    list_display = ('id','operator','post_data','created')
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
