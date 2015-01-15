#-*- coding:utf8 -*-
import re
import json
import time
import datetime
import cStringIO as StringIO
from django.core.urlresolvers import reverse
from django.http import HttpResponse,HttpResponseNotFound,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import FormView
from django.template import RequestContext
from django.db.models import Q,Sum

from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse

from shopback.trades.models import (
        MergeTrade,
        MergeOrder,
        ReplayPostTrade,
        GIFT_TYPE,
        SYS_TRADE_STATUS,
        TAOBAO_TRADE_STATUS,
        SHIPPING_TYPE_CHOICE,
        TAOBAO_ORDER_STATUS)
from shopback.trades.forms import ExchangeTradeForm
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import Product,ProductSku,ProductDaySale
from shopback.base import log_action, ADDITION, CHANGE
from shopback.refunds.models import REFUND_STATUS,Refund
from shopback.signals import rule_signal,change_addr_signal
from shopapp.memorule import ruleMatchSplit
from shopback.users.models import User
from shopback import paramconfig as pcfg
from auth import apis
from common.utils import (
						parse_date,
                        CSVUnicodeWriter,
						parse_datetime,
						format_date,
						format_datetime)
import logging

logger = logging.getLogger('django.request')

    
############################### 缺货订单商品列表 #################################       
class OutStockOrderProductView(ModelView):
    """ docstring for class OutStockOrderProductView """
    
    def get(self, request, *args, **kwargs):
        
        outer_stock_orders  = MergeOrder.objects.filter(merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS,out_stock=True) 
        trade_items = {}
        
        for order in outer_stock_orders:
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
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    skus[outer_sku_id] = {
                                          'sku_name':prod_sku_name,
                                          'num':order.num,
                                          'quality':prod_sku.quantity if prod_sku else 0,
                                          'wait_post_num':prod_sku.wait_post_num if prod_sku else 0}
            else:
                prod = None
                try:
                    prod = Product.objects.get(outer_id=outer_id)
                except:
                    prod = None
                    
                prod_sku = None
                try:
                    prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
                except:
                    prod_sku = None
                prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    
                trade_items[outer_id]={
                                       'num':order.num,
                                       'title': prod.name if prod else order.title,
                                       'collect_num':prod.collect_num if prod else 0,
                                       'wait_post_num':prod.wait_post_num if prod else 0,
                                       'skus':{outer_sku_id:{
                                                             'sku_name':prod_sku_name,
                                                             'num':order.num,
                                                             'quality':prod_sku.quantity if prod_sku else 0,
                                                             'wait_post_num':prod_sku.wait_post_num if prod_sku else 0,
                                                             }
                                               }
                                       }
        
        trade_list = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
        for trade in trade_list:
            skus = trade[1]['skus']
            trade[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['num'],reverse=True)

        return {'trade_items':trade_list,}
    

class StatisticMergeOrderView(ModelView):
    """ docstring for class StatisticsMergeOrderView """
    
    def parseStartDt(self,start_dt):
        
        if not start_dt:
            dt  = datetime.datetime.now()
            return datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        
        if len(start_dt)>10:
            return parse_datetime(start_dt)
        
        return parse_date(start_dt)
    
    def parseEndDt(self,end_dt):
        
        if not end_dt:
            dt  = datetime.datetime.now()
            return datetime.datetime(dt.year,dt.month,dt.day,23,59,59)
        
        if len(end_dt)>10:
            return parse_datetime(end_dt)
        
        return parse_date(end_dt)
    
    def getSourceTrades(self,
                        shop_id=None,is_sale=None,
                        sc_by='created',start_dt=None,
                        end_dt=None,wait_send='0',p_outer_id=''):
        
        trade_qs  = MergeTrade.objects.all()
        if shop_id:
            trade_qs = trade_qs.filter(user=shop_id)
        
        if is_sale:
            trade_qs = trade_qs.filter(type=MergeTrade.WX_TYPE)
        
        if sc_by == 'pay':
            trade_qs = trade_qs.filter(pay_time__gte=start_dt,pay_time__lte=end_dt)
        elif sc_by == 'weight':
            trade_qs = trade_qs.filter(weight_time__gte=start_dt,weight_time__lte=end_dt)
        else:
            trade_qs = trade_qs.filter(created__gte=start_dt,created__lte=end_dt)
        
        if  wait_send == '1':
            trade_qs = trade_qs.filter(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
        elif wait_send == '2':
            trade_qs = trade_qs.filter(
                                       status__in=pcfg.ORDER_SUCCESS_STATUS,
                                       sys_status__in=pcfg.WAIT_WEIGHT_STATUS)
        else:
            trade_qs = trade_qs.filter(status__in=pcfg.ORDER_SUCCESS_STATUS)\
                .exclude(sys_status=pcfg.INVALID_STATUS)
        
        if p_outer_id:
            order_qs = self.getSourceOrders(trade_qs,p_outer_id=p_outer_id)
            trade_qs = MergeTrade.objects.filter(id__in=set([o.merge_trade.id for o in order_qs]))
            
        return trade_qs
        
    def getSourceOrders(self,trade_qs,p_outer_id=None,is_sale=False):
        
        order_qs  = MergeOrder.objects.filter(merge_trade__in=trade_qs,
                            sys_status=pcfg.IN_EFFECT)\
                            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
                            
        if is_sale :
            order_qs = order_qs.extra(where=["CHAR_LENGTH(outer_id)>=9"]).filter(outer_id__startswith="9")
        
        if p_outer_id:
            order_qs = order_qs.filter(outer_id=p_outer_id)
    
        return order_qs
    
    def getEffectOrdersId(self,order_qs):
        
        return [o.oid for o in order_qs if o.num]
        
    def getProductByOuterId(self,outer_id):
        
        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None
        
    def getProductSkuByOuterId(self,outer_id,outer_sku_id):
        
        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except:
            return None
    
    def getProductAndSku(self,outer_id,outer_sku_id):
        
        self.prod_map = {}
        outer_key = '-'.join((outer_id,outer_sku_id))
        if self.prod_map.has_key(outer_key):
            return self.prod_map.get(outer_key)
        
        prod = self.getProductByOuterId(outer_id)
        prod_sku = self.getProductSkuByOuterId(outer_id,outer_sku_id)
        self.prod_map[outer_key] = (prod,prod_sku)
        return  (prod,prod_sku)
    
    def getTradeSortedItems(self,order_qs,is_sale=False):
        
        trade_items  = {}
        for order in order_qs:
            
            outer_id = order.outer_id or str(order.num_iid)
            outer_sku_id = order.outer_sku_id or str(order.sku_id)
            payment   = float(order.payment or 0)
            order_num = order.num  or 0
            prod,prod_sku     = self.getProductAndSku(outer_id,outer_sku_id)

            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order_num
                skus = trade_items[outer_id]['skus']
                
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num']   += order_num
                    skus[outer_sku_id]['cost']  += skus[outer_sku_id]['std_purchase_price']*order_num
                    skus[outer_sku_id]['sales'] += payment
                    #累加商品成本跟销售额
                    trade_items[outer_id]['cost']  += skus[outer_sku_id]['std_purchase_price']*order_num 
                    trade_items[outer_id]['sales'] += payment
                else:
                    prod_sku_name  = prod_sku.name if prod_sku else order.sku_properties_name
                    purchase_price = float(prod_sku.cost) if prod_sku else 0
                    #累加商品成本跟销售额
                    trade_items[outer_id]['cost']  += purchase_price*order_num 
                    trade_items[outer_id]['sales'] += payment
                    
                    skus[outer_sku_id] = {
                                          'sku_name':prod_sku_name,
                                          'num':order_num,
                                          'cost':purchase_price*order_num,
                                          'sales':payment,
                                          'std_purchase_price':purchase_price}
            else:
                prod_sku_name  = prod_sku.name if prod_sku else order.sku_properties_name
                purchase_price = float(prod_sku.cost) if prod_sku else payment/order_num    
                trade_items[outer_id]={
                                       'num':order_num,
                                       'title': prod.name if prod else order.title,
                                       'cost':purchase_price*order_num ,
                                       'sales':payment,
                                       'skus':{outer_sku_id:{
                                            'sku_name':prod_sku_name,
                                            'num':order_num,
                                            'cost':purchase_price*order_num ,
                                            'sales':payment,
                                            'std_purchase_price':purchase_price}}
                                       }
        
        if  is_sale:
            order_items = sorted(trade_items.items(),key=lambda d:d[0])
        else:
            order_items = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
        
        total_cost   = 0
        total_sales  = 0
        for trade in order_items:
            total_cost  += trade[1]['cost']
            total_sales += trade[1]['sales']
            trade[1]['skus'] = sorted(trade[1]['skus'] .items(),key=lambda d:d[0])
        
        order_items.append(total_sales)
        order_items.append( total_cost)
        
        return order_items
    
    def getTotalRefundFee(self,order_qs):
        
        effect_oids = self.getEffectOrdersId(order_qs)
        
        return Refund.objects.filter(oid__in=effect_oids,status__in=(
                    pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_CONFIRM_GOODS,pcfg.REFUND_SUCCESS))\
                    .aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee',0)
        
    def responseCSVFile(self,request,order_items):
        
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
        pcsv =[]
        pcsv.append(("商品编码","商品名称","总数量","成本","销售额","规格编码","商品规格	","数量","成本","销售额"))
        
        for order in order_items:
            first_loop = True
            for item in order:  
                pcsv.append((first_loop and order[0] or '',
                                            first_loop and order[1]['title'] or '',
                                            first_loop and str(order[1]['num']) or '',
                                            first_loop and str(order[1]['cost']) or '',
                                            first_loop and str(order[1]['sales']) or '',
                                            item[0],
                                            item[1]['title'],
                                            str(item[1]['num']),
                                            str(item[1]['cost']),
                                            str(item[1]['sales']),
                                			))
                first_loop = False
            
        tmpfile = StringIO.StringIO()
        writer  = CSVUnicodeWriter(tmpfile,encoding = is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
            
        response = HttpResponse(tmpfile.getvalue(), mimetype='application/octet-stream')
        tmpfile.close()
        
        dt = datetime.datetime.now()
        
        response['Content-Disposition'] = 'attachment;filename=wx-sale-%s.csv'%dt.strftime("%Y%m%d%H")
        
        return response
        
    def get(self, request, *args, **kwargs):
        
        content   = request.REQUEST
        start_dt  = content.get('df','').strip()
        end_dt    = content.get('dt','').strip()
        shop_id   = content.get('shop_id')
        p_outer_id   = content.get('outer_id','')
        sc_by = content.get('sc_by','pay')
        wait_send = content.get('wait_send','0')
        is_sale       = content.get('is_sale','')
        action      = content.get('action','')
        
        start_dt  = self.parseStartDt(start_dt)
        end_dt    = self.parseEndDt(end_dt)
        
        trade_qs  = self.getSourceTrades(
                                         shop_id=shop_id, 
                                         sc_by=sc_by,
                                          wait_send=wait_send, 
                                          p_outer_id=p_outer_id, 
                                          start_dt=start_dt,
                                           end_dt=end_dt,
                                           is_sale=is_sale)
        order_qs  = self.getSourceOrders(trade_qs,p_outer_id = p_outer_id,is_sale=is_sale)
        
        buyer_nums   = trade_qs.values_list('buyer_nick').distinct().count()
        trade_nums    = trade_qs.count()
        total_post_fee = trade_qs.aggregate(total_post_fee=Sum('post_fee')).get('total_post_fee') or 0
        refund_fees      = self.getTotalRefundFee(order_qs)
        
        trade_list   = self.getTradeSortedItems(order_qs,is_sale=is_sale)
        total_cost = trade_list.pop()
        total_sales = trade_list.pop()
        
        if action =="download":
            return self.responseCSVFile(request, trade_list)
        
        shopers = User.objects.filter(status=User.NORMAL)
        
        return {'df':format_datetime(start_dt),
                'dt':format_datetime(end_dt),
                'sc_by':sc_by,
                'is_sale':is_sale,
                'outer_id':p_outer_id,
                'wait_send':wait_send,
                'shops':shopers ,
                'trade_items':trade_list, 
                'shop_id':shop_id and int(shop_id) or '',
                'total_cost':total_cost and round(total_cost,2) or 0 ,
                'total_sales':total_sales and round(total_sales,2) or 0,
                'refund_fees':refund_fees and round(refund_fees,2) or 0,
                'buyer_nums':buyer_nums,
                'trade_nums':trade_nums,
                'post_fees':total_post_fee }
        
    post = get    

class CheckOrderView(ModelView):
    """ docstring for class CheckOrderView """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        
        #rule_signal.send(sender='payment_rule',trade_id=trade.id)
        logistics = LogisticsCompany.objects.filter(status=True)
        
        trade_dict = {
            'id':trade.id,
            'tid':trade.tid,
            'buyer_nick':trade.buyer_nick,
            'seller_nick':trade.user.nick,
            'pay_time':trade.pay_time,
            'payment':trade.payment,
            'post_fee':trade.post_fee,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'sys_memo':trade.sys_memo,
            'logistics_company':trade.logistics_company,
            'shipping_type':trade.shipping_type,
            'priority':trade.priority,
            'type':trade.type,
            'total_num':trade.total_num,
            'receiver_name':trade.receiver_name,
            'receiver_state':trade.receiver_state,
            'receiver_city':trade.receiver_city,
            'receiver_district':trade.receiver_district,
            'receiver_address':trade.receiver_address,
            'receiver_mobile':trade.receiver_mobile,
            'receiver_phone':trade.receiver_phone,
            'receiver_zip':trade.receiver_zip,
            'has_memo':trade.has_memo,
            'has_refund':trade.has_refund,
            'has_out_stock':trade.has_out_stock,
            'out_of_logistic':trade.has_reason_code(pcfg.LOGISTIC_ERROR_CODE),
            'has_rule_match':(trade.has_rule_match and 
                              trade.has_reason_code(pcfg.RULE_MATCH_CODE)),
            'is_product_defect':(trade.has_rule_match and 
                                 trade.has_reason_code(pcfg.TRADE_DEFECT_CODE)),
            'has_merge':trade.has_merge,
            'has_sys_err':trade.has_sys_err,
            'need_manual_merge':trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE),
            'reason_code':trade.reason_code,
            'status':trade.status,
            'sys_status':trade.sys_status,
            'used_orders':trade.inuse_orders,
        }
        
        return {'trade':trade_dict,'logistics':logistics,'shippings':dict(SHIPPING_TYPE_CHOICE)}
        
    def post(self, request, id, *args, **kwargs):
        
        user_id = request.user.id
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return u'该订单不存在'
        content       = request.REQUEST
        priority      = content.get('priority')
        logistic_code = content.get('logistic_code')
        shipping_type = content.get('shipping_type')
        action_code   = content.get('action')
        logistics_company = None
           
        if logistic_code:
            logistics_company = LogisticsCompany.objects.get(code=logistic_code)
        elif shipping_type != pcfg.EXTRACT_SHIPPING_TYPE:
            #如果没有选择物流也非自提订单，则提示
            return u'请选择物流公司'
        
        is_logistic_change = trade.logistics_company != logistics_company
        trade.logistics_company = logistics_company
        trade.priority = priority
        trade.shipping_type = shipping_type
        trade.save()
            
        if action_code == 'check':
            check_msg = []
            if trade.has_refund:
                check_msg.append(u"有待退款")
            if trade.has_out_stock:
                check_msg.append(u"有缺货")
            if (trade.has_rule_match or 
                MergeTrade.objects.isTradeDefect(trade)):
                check_msg.append(u"订单商品编码与库存商品编码不一致")
            if trade.is_force_wlb:
                check_msg.append(u"订单由物流宝发货")
            if trade.sys_status != pcfg.WAIT_AUDIT_STATUS:
                check_msg.append(u"订单不在问题单")
            if trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE):
                check_msg.append(u"需手动合单")
            if trade.has_sys_err:
                check_msg.append(u"订单需管理员审核")
            orders = trade.inuse_orders.exclude(refund_status__in=
                                                pcfg.REFUND_APPROVAL_STATUS) 
            if orders.count()==0:
                check_msg.append(u"订单没有商品信息")   
            if check_msg:
                return ','.join(check_msg)
            
            if trade.type == pcfg.EXCHANGE_TYPE:
                change_orders = trade.merge_orders.filter(
                    gift_type=pcfg.CHANGE_GOODS_GIT_TYPE,
                    sys_status=pcfg.IN_EFFECT)

                if change_orders.count()>0:
                    #订单为自提
                    if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE:
                        trade.sys_status = pcfg.FINISHED_STATUS
                        trade.status     = pcfg.TRADE_FINISHED
                        trade.consign_time = datetime.datetime.now()
                        #更新退换货库存
                        trade.update_inventory()
                    #订单需物流
                    else:    
                        trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                        trade.status = pcfg.WAIT_SELLER_SEND_GOODS
                    trade.reason_code = ''
                    trade.save()
                else:
                    #更新退货库存
                    trade.update_inventory()
                    
                    trade.sys_status = pcfg.FINISHED_STATUS
                    trade.status     = pcfg.TRADE_FINISHED
                    trade.save()
                
            elif trade.type in (pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):   
                #订单为自提
                if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE: 
                    trade.sys_status = pcfg.FINISHED_STATUS
                    trade.status     = pcfg.TRADE_FINISHED
                    trade.consign_time = datetime.datetime.now()
                    #更新库存
                    trade.update_inventory()
                #订单需物流
                else:
                    trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                    trade.status     = pcfg.WAIT_SELLER_SEND_GOODS
                trade.reason_code = ''
                trade.save()
            else:
                if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE: 
                    try:
                        response = apis.taobao_logistics_offline_send(
                                                  tid=trade.tid,out_sid=1111111111
                                                  ,company_code=pcfg.EXTRACT_COMPANEY_CODE,
                                                  tb_user_id=trade.user.visitor_id)
                    except Exception,exc:
                        trade.append_reason_code(pcfg.POST_MODIFY_CODE)
                        trade.sys_status=pcfg.WAIT_AUDIT_STATUS
                        trade.sys_memo=exc.message
                        trade.save()
                        log_action(request.user.id,trade,CHANGE,u'订单发货失败')
                    else:
                        trade.sys_status=pcfg.FINISHED_STATUS
                        trade.consign_time=datetime.datetime.now()
                        trade.save()
                        log_action(request.user.id,trade,CHANGE,u'订单发货成功')
                    #更新库存
                    trade.update_inventory()
                else:
                    MergeTrade.objects.filter(id=id,sys_status = pcfg.WAIT_AUDIT_STATUS)\
                        .update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,reason_code='',out_sid='')  
            log_action(user_id,trade,CHANGE,u'审核成功')
            
        elif action_code == 'review':
            if trade.sys_status not in pcfg.WAIT_SCAN_CHECK_WEIGHT:
                return u'订单不在待扫描状态'
            
            if is_logistic_change:
                trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
            
            MergeTrade.objects.filter(id=id).update(can_review=True)
            log_action(user_id,trade,CHANGE,u'订单复审')
            
        return {'success':True}    
      
       
class OrderPlusView(ModelView):
    """ docstring for class OrderPlusView """
    
    def get(self, request, *args, **kwargs):
        
        q  = request.GET.get('q')
        if not q:
            return '没有输入查询关键字'.decode('utf8')
        products = Product.objects.filter(Q(outer_id=q)|Q(name__contains=q),status__in=(pcfg.NORMAL,pcfg.REMAIN))
        
        prod_list = [(prod.outer_id,prod.name,prod.std_sale_price,
                      [(sku.outer_id,sku.name,sku.quantity) for sku in prod.pskus]) for prod in products]
        return prod_list
        
    def post(self, request, *args, **kwargs):
        
        user_id  = request.user.id
        trade_id = request.POST.get('trade_id')
        outer_id = request.POST.get('outer_id')
        outer_sku_id = request.POST.get('outer_sku_id')
        num      = int(request.POST.get('num',1))    
        type     = request.POST.get('type',pcfg.CS_PERMI_GIT_TYPE) 
        try:
            merge_trade = MergeTrade.objects.get(id=trade_id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        try:
            Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExist:
            return '该商品不存在'.decode('utf8')
        
        if outer_sku_id:
            try:
                ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
            except ProductSku.DoesNotExist:
                return '该商品规格不存在'.decode('utf8')
        
        if not merge_trade.can_change_order:
            return HttpResponse(json.dumps({'code':1,"response_error":"订单不能修改！"}),mimetype="application/json")
        
        is_reverse_order = False
        if merge_trade.can_reverse_order:
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
            is_reverse_order = True    
        
        merge_order = MergeOrder.gen_new_order(trade_id,outer_id,outer_sku_id,num,gift_type=type
                                               ,status=pcfg.WAIT_BUYER_CONFIRM_GOODS,is_reverse=is_reverse_order)
        
        #组合拆分
        ruleMatchSplit(merge_trade)
        
        log_action(user_id,merge_trade,ADDITION,u'添加子订单(%d)'%merge_order.id)
        
        return merge_order
    
           
def change_trade_addr(request):
    
    user_id  = request.user.id
    CONTENT    = request.REQUEST
    trade_id   = CONTENT.get('trade_id')
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"订单不存在！"}),mimetype="application/json")
        
    for (key, val) in CONTENT.items():
        setattr(trade, key, val.strip())
    trade.save()
    
    try:
        if trade.type in (pcfg.TAOBAO_TYPE,
                          pcfg.FENXIAO_TYPE,
                          pcfg.GUARANTEE_TYPE) \
            and trade.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                     pcfg.WAIT_CHECK_BARCODE_STATUS,
                                     pcfg.WAIT_SCAN_WEIGHT_STATUS):
            apis.taobao_trade_shippingaddress_update(
                tid=trade.tid,
                receiver_name=trade.receiver_name,
                receiver_phone=trade.receiver_phone,
                receiver_mobile=trade.receiver_mobile,
                receiver_state=trade.receiver_state,
                receiver_city=trade.receiver_city,
                receiver_district=trade.receiver_district,
                receiver_address=trade.receiver_address,
                receiver_zip=trade.receiver_zip,
                tb_user_id=trade.user.visitor_id
            )
    except Exception,exc:
        logger.debug(u'订单地址更新失败：%s'%exc.message)
        
    #通知其他APP，订单地址已修改
    change_addr_signal.send(sender=MergeTrade,tid=trade.id)
    
    trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
    
    if MergeTrade.objects.isTradeMergeable(trade):
        trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE) 
    
    log_action(user_id,trade,CHANGE,u'修改地址,修改前（%s）'%trade.buyer_full_address)
    
    ret_params = {'code':0,'success':True}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")
    
    
def change_trade_order(request,id):
    
    user_id    = request.user.id
    CONTENT    = request.REQUEST
    outer_sku_id = CONTENT.get('outer_sku_id')
    order_num    = int(CONTENT.get('order_num',0))
    try:
        order = MergeOrder.objects.get(id=id)
    except MergeOrder.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"订单不存在！"}),mimetype="application/json")
    
    try:
        prod  = Product.objects.get(outer_id=order.outer_id)
    except Product.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"商品不存在！"}),mimetype="application/json")
        
    try:
        prod_sku = ProductSku.objects.get(product__outer_id=order.outer_id,outer_id=outer_sku_id) 
    except ProductSku.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"商品规格不存在！"}),mimetype="application/json")
    
    merge_trade = order.merge_trade

    if not merge_trade.can_change_order:
        return HttpResponse(json.dumps({'code':1,"response_error":"商品规格不能修改！"}),mimetype="application/json")
    
    is_reverse_order = False
    if merge_trade.can_reverse_order:
        merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
        is_reverse_order = True
        
    order.outer_sku_id=prod_sku.outer_id
    order.sku_properties_name=prod_sku.properties_name
    order.is_rule_match = False
    order.out_stock     = prod_sku.is_out_stock if prod_sku else prod.is_out_stock
    order.is_reverse_order = is_reverse_order
    order.num           = order_num
    order.save()
    merge_trade.remove_reason_code(pcfg.RULE_MATCH_CODE)
    order = MergeOrder.objects.get(id=order.id)
    
    log_action(user_id,merge_trade,CHANGE,u'修改子订单(%d)'%order.id)
    
    ret_params = {'code':0,'response_content':{'id':order.id,
                                               'outer_id':order.outer_id,
                                               'title':prod.name,
                                               'sku_properties_name':order.sku_properties_name,
                                               'num':order.num,
                                               'out_stock':order.out_stock,
                                               'price':order.price,
                                               'gift_type':order.gift_type,
                                               }}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

     
def delete_trade_order(request,id):
    
    user_id      = request.user.id
    try:
        merge_order  = MergeOrder.objects.get(id=id)
    
        merge_trade = merge_order.merge_trade
        is_reverse_order = False
        if merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                      pcfg.WAIT_SCAN_WEIGHT_STATUS):
            
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
            is_reverse_order = True
            
        merge_order.sys_status = pcfg.INVALID_STATUS
        merge_order.is_reverse_order = is_reverse_order
        merge_order.save()
        
        log_action(user_id,merge_trade,CHANGE,u'子订单作废(%d)'%merge_order.id)
            
    except MergeOrder.DoesNotExist:
        ret_params = {'code':1,'response_error':u'订单不存在'}
        
    except Exception,exc:
         ret_params = {'code':1,'response_error':u'系统操作失败'}
         logger.error(u'子订单(%s)删除失败:%s'%(id,exc.message),exc_info=True)
         
    else:
        ret_params = {'code':0,'response_content':{'success':True}}
        
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

    
        
############################### 订单复审 #################################       
class ReviewOrderView(ModelView):
    """ docstring for class ReviewOrderView """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        
        logistics = LogisticsCompany.objects.filter(status=True)
        order_nums = trade.inuse_orders.aggregate(total_num=Sum('num')).get('total_num')
        
        trade_dict = {
            'id':trade.id,
            'tid':trade.tid,
            'buyer_nick':trade.buyer_nick,
            'seller_nick':trade.user.nick,
            'pay_time':trade.pay_time,
            'payment':trade.payment,
            'post_fee':trade.post_fee,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'sys_memo':trade.sys_memo,
            'logistics_company':trade.logistics_company,
            'out_sid':trade.out_sid,
            'consign_time':trade.consign_time,
            'priority':trade.priority,
            'receiver_name':trade.receiver_name,
            'receiver_state':trade.receiver_state,
            'receiver_city':trade.receiver_city,
            'receiver_district':trade.receiver_district,
            'receiver_address':trade.receiver_address,
            'receiver_mobile':trade.receiver_mobile,
            'receiver_phone':trade.receiver_phone,
            'reason_code':trade.reason_code,
            'can_review':trade.can_review,
            'can_review_status':trade.sys_status in pcfg.WAIT_SCAN_CHECK_WEIGHT,
            'status':trade.status,
            'sys_status':trade.sys_status,
            'status_name':dict(TAOBAO_TRADE_STATUS).get(trade.status,u'未知'),
            'sys_status_name':dict(SYS_TRADE_STATUS).get(trade.sys_status,u'未知'),
            'used_orders':trade.inuse_orders.exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE),
            'order_nums':order_nums,
            'new_memo':trade.has_reason_code(pcfg.NEW_MEMO_CODE),
            'new_refund':trade.has_reason_code(pcfg.WAITING_REFUND_CODE) or trade.has_reason_code(pcfg.NEW_REFUND_CODE),
            'order_modify':trade.has_reason_code(pcfg.ORDER_ADD_REMOVE_CODE),
            'addr_modify':trade.has_reason_code(pcfg.ADDR_CHANGE_CODE),
            'new_merge':trade.has_reason_code(pcfg.NEW_MERGE_TRADE_CODE),
            'wait_merge':trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE),
            'has_out_stock':trade.has_out_stock,
        }
        
        return {'trade':trade_dict,'logistics':logistics}
        
              
def review_order(request,id):
    #仓库订单复审     
    user_id  = request.user.id
    try:
        merge_trade = MergeTrade.objects.get(id=id)
    except MergeTrade.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,'response_error':u'该订单不存在'}),mimetype="application/json")

    if not merge_trade.can_review and merge_trade.sys_status \
        not in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
        return HttpResponse(json.dumps({'code':1,'response_error':u'该订单不能复审'}),mimetype="application/json")
    MergeTrade.objects.filter(id=id).update(reason_code='')
    
    log_action(user_id,merge_trade,CHANGE,u'复审通过')
    return HttpResponse(json.dumps({'code':0,'response_content':{'success':True}}),mimetype="application/json")


def change_order_stock_status(request,id):
        
    content   = request.REQUEST
    out_stock = content.get('out_stock','0')
    user_id  = request.user.id
    
    try:
        merge_order = MergeOrder.objects.get(id=id)
    except MergeOrder.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,'response_error':u'该订单不存在'}),mimetype="application/json")
    
    merge_trade = merge_order.merge_trade
    if  merge_trade.sys_status not in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS,pcfg.FINISHED_STATUS):
        return HttpResponse(json.dumps({'code':1,'response_error':u'该订单不能修改缺货状态'}),mimetype="application/json")
    
    merge_order.out_stock = out_stock=='1' and True or False
    merge_order.save()
    
    if merge_order.out_stock:
        merge_trade.append_reason_code(pcfg.OUT_GOOD_CODE)
    
    log_action(user_id,merge_trade,CHANGE,u'设置订单(%d)缺货状态:%s'%(merge_order.id,str(merge_order.out_stock)))
    return HttpResponse(json.dumps({'code':0,'response_content':{'out_stock':merge_order.out_stock}}),mimetype="application/json")

    
def change_logistic_and_outsid(request):
    
    user_id  = request.user.id
    CONTENT    = request.REQUEST
    trade_id   = CONTENT.get('trade_id')
    out_sid    = CONTENT.get('out_sid')
    logistic_code = CONTENT.get('logistic_code','').upper()
    is_qrcode  = logistic_code.endswith('QR')
    
    if not trade_id or (not is_qrcode 
                        and (not out_sid or not logistic_code)):
        ret_params = {'code':1,'response_error':u'请填写快递名称及单号'}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
    
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
    except:    
        ret_params = {'code':1,'response_error':u'未找到该订单'}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
    
    origin_logistic_code = merge_trade.logistics_company and merge_trade.logistics_company.code
    origin_out_sid       = merge_trade.out_sid  
    try:
        logistic   = LogisticsCompany.objects.get(code=logistic_code)
        logistic_regex = re.compile(logistic.reg_mail_no)
        if not is_qrcode and not logistic_regex.match(out_sid):
            raise Exception(u'快递单号不合规则')
        
        real_logistic_code = logistic_code.split('_')[0]
        dt = datetime.datetime.now()
        if merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
            
            try:
                if not is_qrcode and (dt-merge_trade.consign_time).days<1:
                    response = apis.taobao_logistics_consign_resend(tid=merge_trade.tid,out_sid=out_sid
                                                     ,company_code=real_logistic_code,tb_user_id=merge_trade.user.visitor_id)
                    if not response['logistics_consign_resend_response']['shipping']['is_success']:
                        raise Exception(u'重发失败')
            except Exception,exc:
                dt  = datetime.datetime.now()
                merge_trade.sys_memo = u'%s,修改快递单号[%s]:(%s)%s'%(merge_trade.sys_memo,
                                                             dt.strftime('%Y-%m-%d %H:%M'),logistic_code,out_sid)
                logger.error(exc.message,exc_info=True)

            merge_trade.logistics_company = logistic
            merge_trade.out_sid   = out_sid
            merge_trade.save()
            log_action(user_id,merge_trade,CHANGE,u'修改快递及单号(修改前:%s,%s)'%(origin_logistic_code,origin_out_sid))
        elif merge_trade.sys_status == pcfg.FINISHED_STATUS:
            try:
                if not is_qrcode and (dt-merge_trade.consign_time).days<1:
                    apis.taobao_logistics_consign_resend(tid=merge_trade.tid,out_sid=out_sid
                                                 ,company_code=real_logistic_code,tb_user_id=merge_trade.user.visitor_id)
            except:
                pass
            dt  = datetime.datetime.now()
            merge_trade.sys_memo = u'%s,退回重发单号[%s]:(%s)%s'%(merge_trade.sys_memo,
                                                             dt.strftime('%Y-%m-%d %H:%M'),logistic_code,out_sid)
            merge_trade.logistics_company = logistic
            merge_trade.out_sid   = out_sid
            merge_trade.save()
            log_action(user_id,merge_trade,CHANGE,u'修改单号(修改前:%s,%s)'%(origin_logistic_code,origin_out_sid))
        else:
            raise Exception(u'该订单不能修改')
            
    except Exception,exc:
        ret_params = {'code':1,'response_error':exc.message}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
        
    ret_params = {'code':0,'response_content':{'logistic_company_name':logistic.name
                                               ,'logistic_company_code':logistic.code,'out_sid':out_sid}}
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")


############################### 退换货订单 #################################    
class ExchangeOrderView(ModelView):
    """ docstring for class ExchangeOrderView """
    
    def get(self, request, *args, **kwargs):
        
        origin_no   = MergeTrade._meta.get_field_by_name('tid')[0].get_default()
        sellers = User.objects.all()
        
        return {'origin_no':origin_no,'sellers':sellers}
    
    def post(self, request, *args, **kwargs):
        
        content     = request.REQUEST
        trade_id    = content.get('tid')
        seller_id   = content.get('sellerId')

        try:
            merge_trade,state = MergeTrade.objects.get_or_create(user_id=seller_id,tid=trade_id)
        except Exception,exc:
            return u'退换货单创建异常:%s'%exc.message
        
        if merge_trade.sys_status not in('',pcfg.WAIT_AUDIT_STATUS):
            return u'订单状态已改变'
        
        dt = datetime.datetime.now()
        for key,val in content.iteritems():
            hasattr(merge_trade,key) and setattr(merge_trade,key,val)  
        
        merge_trade.type = pcfg.EXCHANGE_TYPE
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.sys_status =  merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.created    = dt
        merge_trade.pay_time   = dt
        merge_trade.modified   = dt
        merge_trade.save()
        
        log_action(request.user.id,merge_trade,CHANGE,u'订单创建')

        return HttpResponseRedirect(reverse('exchange_order_instance', 
                                            kwargs={'id':merge_trade.id}))

class ExchangeOrderInstanceView(ModelView):
    """ docstring for class ExchangeOrderView """
    
    def get(self, request,id, *args, **kwargs):
        
        merge_trade =MergeTrade.objects.get(id=id)
        
        return {'trade':merge_trade,
                'sellers':User.objects.all()}
    
    def post(self, request,id, *args, **kwargs):
        
        content     = request.REQUEST
        try:
            merge_trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return u'退换货单创建异常'
        
        if merge_trade.sys_status not in('',pcfg.WAIT_AUDIT_STATUS):
            return u'订单状态已改变'
        
        for key,val in content.iteritems():
            hasattr(merge_trade,key) and setattr(merge_trade,key,val)  
        
        merge_trade.type = pcfg.EXCHANGE_TYPE
        merge_trade.user_id =  content.get('sellerId')
        merge_trade.sys_status =  merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.save()
        
        log_action(request.user.id,merge_trade,CHANGE,u'订单修改')
        
        return {'trade':merge_trade,
                'type':merge_trade.type,  
                'sellers':User.objects.all()}
        
############################### 内售订单 #################################       
class DirectOrderView(ModelView):
    """ docstring for class DirectOrderView """
    
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        type    = content.get('type','')
        origin_no   = MergeTrade._meta.get_field_by_name('tid')[0].get_default()
        sellers = User.objects.all()
        
        return {'origin_no':origin_no,
                'trade_type':type,                    
                'sellers':sellers}
    
    def post(self, request, *args, **kwargs):
        
        content     = request.REQUEST
        trade_id    = content.get('tid')
        seller_id    = content.get('sellerId')
        trade_type   = content.get('trade_type')
        
        if trade_type not in (pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return u'订单类型异常'
        try:
            merge_trade,state =  MergeTrade.objects.get_or_create(user_id=seller_id,tid=trade_id)
        except Exception,exc:
            return u'退换货单创建异常:%s'%exc.message
        
        if merge_trade.sys_status not in('',pcfg.WAIT_AUDIT_STATUS):
            return u'订单状态已改变'
        
        dt = datetime.datetime.now()
        for key,val in content.iteritems():
            hasattr(merge_trade,key) and setattr(merge_trade,key,val)  
        
        merge_trade.type = trade_type
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.created    = dt
        merge_trade.pay_time   = dt
        merge_trade.modified   = dt
        merge_trade.save()
        
        log_action(request.user.id,merge_trade,CHANGE,u'订单创建')
        
        return  HttpResponseRedirect(reverse('direct_order_instance', 
                                             kwargs={'id':merge_trade.id}))
                   
class DirectOrderInstanceView(ModelView):
    """ docstring for class DirectOrderView """
    
    def get(self, request, id,*args, **kwargs):
        
        merge_trade = MergeTrade.objects.get(id=id)
        sellers = User.objects.all()
        
        return {'trade':merge_trade,   
                'trade_type':merge_trade.type,
                'sellers':sellers}
    
    def post(self, request, id, *args , **kwargs):
        
        content     = request.REQUEST
        type = content.get('trade_type')
        
        if type not in (pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return u'订单类型异常'
        try:
            merge_trade =  MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return u'内售单创建异常'
        
        if merge_trade.sys_status not in('',pcfg.WAIT_AUDIT_STATUS):
            return u'订单状态已改变'
        
        for key,val in content.iteritems():
            hasattr(merge_trade,key) and setattr(merge_trade,key,val)  
        
        merge_trade.user_id =  content.get('sellerId')
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.save()
        
        log_action(request.user.id,merge_trade,CHANGE,u'订单修改')
        
        return {'trade':merge_trade,
                'trade_type':merge_trade.type,
                'sellers':User.objects.all()}
        
        
def update_sys_memo(request):
        
    user_id  = request.user.id
    content  = request.REQUEST
    trade_id = content.get('trade_id','')
    sys_memo = content.get('sys_memo','')
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
    except:
        return HttpResponse(json.dumps({'code':1,'response_error':u'订单未找到'}),mimetype="application/json")
    else:
        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        merge_trade.sys_memo   = sys_memo
        merge_trade.save()
        MergeTrade.objects.filter(id=merge_trade.id,sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,out_sid='')\
            .update(sys_status = pcfg.WAIT_AUDIT_STATUS)
        log_action(user_id,merge_trade,CHANGE,u'系统备注:%s'%sys_memo)
        return HttpResponse(json.dumps({'code':0,'response_content':{'success':True}}),mimetype="application/json")


        
def regular_trade(request,id):
        
    user_id  = request.user.id
    try:
        merge_trade = MergeTrade.objects.get(id=id,sys_status=pcfg.WAIT_AUDIT_STATUS)
    except:
        return HttpResponse(json.dumps({'code':1,'response_error':u'订单不在问题单'}),mimetype="application/json")
    else:
        dt = datetime.datetime.now()+datetime.timedelta(1,0,0)
        merge_trade.sys_status   = pcfg.REGULAR_REMAIN_STATUS
        merge_trade.remind_time  = dt
        merge_trade.save()
        log_action(user_id,merge_trade,CHANGE,u'定时提醒:%s'%dt.strftime('%Y-%m-%d %H:%M'))
        return HttpResponse(json.dumps({'code':0,'response_content':{'success':True}}),mimetype="application/json")


def replay_trade_send_result(request,id):
        
    try:
        replay_trade = ReplayPostTrade.objects.get(id=id)
    except:
        return HttpResponse('<body style="text-align:center;"><h1>发货结果未找到</h1></body>')
    else:
        from shopback.trades.tasks import get_replay_results
        try:
            reponse_result = get_replay_results(replay_trade)
        except Exception,exc:
            logger.error( 'trade post callback error:%s'%exc.message,exc_info=True)
        reponse_result['post_no'] = reponse_result.get('post_no',None) or replay_trade.id     
        
        return render_to_response('trades/trade_post_success.html',reponse_result,
                                  context_instance=RequestContext(request),mimetype="text/html")


class TradeSearchView(ModelView):   
    """ docstring for class ExchangeOrderView """
         
    def get(self, request, *args, **kwargs):
         
        q  = request.REQUEST.get('q')
        if not q:
            return u'请输入查询字符串'
        
        if q.isdigit():
            trades = MergeTrade.objects.filter(Q(id=q)|Q(tid=q)|
                    Q(buyer_nick=q)|Q(receiver_name=q)|Q(receiver_mobile=q))
        else:
            trades = MergeTrade.objects.filter(Q(buyer_nick=q)|
                                    Q(receiver_name=q)|Q(receiver_phone=q))
        trade_list = []
        for trade in trades:
            trade_dict       = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_id']  = trade.user.id if trade.user else ''
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['post_fee']   = trade.post_fee
            trade_dict['payment']    = trade.payment
            trade_dict['total_num']  = trade.order_num
            trade_dict['pay_time']   = trade.pay_time
            trade_dict['consign_time']   = trade.consign_time
            
            trade_dict['receiver_name']  = trade.receiver_name
            trade_dict['receiver_state'] = trade.receiver_state
            trade_dict['receiver_city']  = trade.receiver_city
            trade_dict['receiver_district'] = trade.receiver_district
            trade_dict['receiver_address']  = trade.receiver_address
            trade_dict['receiver_mobile'] = trade.receiver_mobile
            trade_dict['receiver_phone']  = trade.receiver_phone
            trade_dict['receiver_zip']    = trade.receiver_zip
            
            trade_dict['status']      = dict(TAOBAO_TRADE_STATUS).get(trade.status,u'其他')
            trade_dict['sys_status']  = dict(SYS_TRADE_STATUS).get(trade.sys_status,u'其他')
            trade_list.append(trade_dict)
        
        return trade_list
         
         
    def post(self, request, *args, **kwargs):
        
        content     = request.REQUEST
        cp_tid      = content.get('cp_tid')
        pt_tid      = content.get('pt_tid')
        type        = content.get('type','')
        
        if not cp_tid or not pt_tid or not type.isdigit():
            return u'请输入订单编号及退换货类型'
            
        try:
            cp_trade = MergeTrade.objects.get(id=cp_tid)
        except MergeTrade.DoesNotExist:
            return u'订单未找到'
        
        try:
            pt_trade = MergeTrade.objects.get(id=pt_tid)
        except MergeTrade.DoesNotExist:
            return u'订单未找到'
        
        can_post_orders = cp_trade.merge_orders.all()
        for order in can_post_orders:
            try:
                MergeOrder.gen_new_order(pt_trade.id,order.outer_id,
                                         order.outer_sku_id,order.num,gift_type=type)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                   
        orders = pt_trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)
        order_list = []
        for order in orders:
            try:
                prod = Product.objects.get(outer_id=order.outer_id)
            except Exception,exc:
                prod = None
            try:
                prod_sku = ProductSku.objects.get(outer_id=order.outer_sku_id,
                                                  product__outer_id=order.outer_id)
            except:
                prod_sku = None
            order_dict = {
            'id':order.id,
            'outer_id':order.outer_id,
            'title':prod.name if prod else order.title,
            'sku_properties_name':(prod_sku.properties_name if prod_sku 
                                   else order.sku_properties_name),
            'num':order.num,
            'out_stock':order.out_stock,
            'price':order.price,
            'gift_type':order.gift_type,}
            order_list.append(order_dict)
 
        return order_list


############################### 交易订单商品列表 #################################       
class OrderListView(ModelView):
    """ docstring for class OrderListView """
    
    def get(self, request, id, *args, **kwargs):
        
        order_list = []
        try:
            trade  = MergeTrade.objects.get(id=id)
        except:
            return HttpResponseNotFound('<h1>订单未找到</h1>')
        for order in trade.merge_orders.all():
            try:
                prod = Product.objects.get(outer_id=order.outer_id)
            except:
                prod = None
            order_dict = {}
            order_dict['id']  = order.id
            order_dict['tid'] = order.merge_trade.tid
            order_dict['outer_id']     = order.outer_id
            order_dict['outer_sku_id'] = order.outer_sku_id
            order_dict['total_fee']    = order.total_fee
            order_dict['payment']      = order.payment
            order_dict['title']        = prod and prod.name or order.title
            order_dict['num']          = order.num
            order_dict['sku_properties_name'] = order.sku_properties_name
            order_dict['refund_status'] = dict(REFUND_STATUS).get(order.refund_status,u'其他')
            order_dict['seller_nick']  = order.seller_nick
            order_dict['buyer_nick']   = order.buyer_nick
            order_dict['receiver_name'] = trade.receiver_name
            order_dict['pay_time']     = order.pay_time
            order_dict['status']     = dict(TAOBAO_ORDER_STATUS).get(order.status,u'其他')
            order_list.append(order_dict)
            
        return {'order_list':order_list}
    
############################### 关联销售商品 #################################  

class RelatedOrderStateView(ModelView):
    """ docstring for class RelatedOrderStateView """
    
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        df   = content.get('df')
        dt   = content.get('dt')
        outer_id = content.get('outer_id','')
        outer_sku_ids = content.get('sku_ids')
        limit  = content.get('limit',10) 
        
        if df and dt:
            start_dt = parse_date(df)
            end_dt   = parse_date(dt)
            start_dt = datetime.datetime(start_dt.year,start_dt.month,start_dt.day,0,0,0)
            end_dt   = datetime.datetime(end_dt.year,end_dt.month,end_dt.day,23,59,59)
        else:
            dt  = datetime.datetime.now()
            start_dt = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
            end_dt   = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)
        
        order_item_list  = []
        if outer_id:
            merge_orders = MergeOrder.objects.filter(outer_id=outer_id,
                                                created__gte=start_dt,
                                                created__lte=end_dt).exclude(
                           status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,
                                       pcfg.WAIT_BUYER_PAY,
                                       pcfg.TRADE_CLOSED))
            if outer_sku_ids:
                sku_ids = outer_sku_ids.split(',')
                merge_orders = merge_orders.filter(outer_sku_id__in=sku_ids)
                
            buyer_set = set()
            relative_orders_dict = {} 
            for order in merge_orders:
                receiver_mobile = order.merge_trade.receiver_mobile
                try:
                    buyer_set.remove(receiver_mobile)
                except:
                    buyer_set.add(receiver_mobile)
                    relat_orders = MergeOrder.objects.filter(
                                        merge_trade__receiver_mobile=receiver_mobile,
                                        is_merge=False,
                                        created__gte=start_dt,
                                        created__lte=end_dt).exclude(
                                             status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,
                                                         pcfg.WAIT_BUYER_PAY,
                                                         pcfg.TRADE_CLOSED))
                    for o in relat_orders:
                        relat_outer_id = o.outer_id
                        if relative_orders_dict.has_key(relat_outer_id):
                            relative_orders_dict[relat_outer_id]['cnum'] += o.num
                        else:
                            relative_orders_dict[relat_outer_id] = {'pic_path':o.pic_path,
                                                                    'title':o.title,
                                                                    'cnum':o.num}
                else:
                    buyer_set.add(receiver_mobile)
                
            relat_order_list = sorted(relative_orders_dict.items(),
                                      key=lambda d:d[1]['cnum'],
                                      reverse=True)  

            for order in relat_order_list[0:int(limit)]:
                pic_path = order[1]['pic_path']
                try:
                    product = Product.objects.get(outer_id=order[0])
                except Product.DoesNotExist:
                    pass
                else:
                    pic_path = pic_path or product.pic_path
                order_item = []
                order_item.append(order[0])
                order_item.append(pic_path)
                order_item.append(order[1]['title'])
                order_item.append(order[1]['cnum'])
                order_item_list.append(order_item)
            print order_item_list

        return {'df':format_date(start_dt),
                'dt':format_date(end_dt),
                'outer_id':outer_id,
                'limit':limit,
                'order_items':order_item_list}
        
    post = get
    
############################### 订单物流信息列表 #################################     
class TradeLogisticView(ModelView):
    """ docstring for class TradeLogisticView """
    
    def get(self, request, *args, **kwargs):
        
        content  = request.REQUEST
        q        = content.get('q')
        df       = content.get('df')
        dt       = content.get('dt')
        trade_list = []
        weight_list = []
        TOTAL_count = 0
        
        if q:
            mergetrades = MergeTrade.objects.filter(out_sid=q.strip('\' '),
                                                    is_express_print=True)
            for trade in mergetrades:
                trade_dict = {"tid":trade.tid, 
                              "seller_nick":trade.user.nick,
                              "buyer_nick":trade.buyer_nick,
                              "out_sid":trade.out_sid,
                              "logistics_company":trade.logistics_company.name,
                              "receiver_name":trade.receiver_name,
                              "receiver_state":trade.receiver_state,
                              "receiver_city":trade.receiver_city,
                              "receiver_district":trade.receiver_district,
                              "receiver_address":trade.receiver_address,
                              "receiver_zip":trade.receiver_zip,
                              "receiver_phone":trade.receiver_phone,
                              "receiver_mobile":trade.receiver_mobile,
                              "weight":trade.weight
                              }
                
                trade_list.append(trade_dict)
            
        if df:
            df = parse_date(df).date()
            queryset = MergeTrade.objects.filter(sys_status=pcfg.FINISHED_STATUS,
                                                 weight_time__gt=df,
                                                 logistics_company__code__in=("YUNDA","YUNDA_QR"))
            if dt:
                dt = parse_date(dt).date()
                queryset = queryset.filter(weight_time__lt=dt)
            
            TOTAL_count = queryset.count()
            
            SH_weight  = queryset.filter(receiver_state=u'上海').aggregate(wt=Sum('weight')).get('wt')
            SH_count   = queryset.filter(receiver_state=u'上海').count()
            JZA_weight = queryset.filter(receiver_state__in=(u'江苏省',u'浙江省',u'安徽省')).aggregate(wt=Sum('weight')).get('wt')
            JZA_count  = queryset.filter(receiver_state__in=(u'江苏省',u'浙江省',u'安徽省')).count()
            OTHER_weight = queryset.exclude(receiver_state__in=(u'上海','江苏省',u'浙江省',u'安徽省')).aggregate(wt=Sum('weight')).get('wt')
            OTHER_count  = queryset.exclude(receiver_state__in=(u'上海','江苏省',u'浙江省',u'安徽省')).count()
            
            weight_list.append((SH_weight,SH_count))
            weight_list.append((JZA_weight,JZA_count))
            weight_list.append((OTHER_weight,OTHER_count))

        return {'logistics':trade_list,'df':df or '','dt':dt or '','yunda_count':TOTAL_count,'weights':weight_list}   
    
    post = get 
    
    
def calFenxiaoInterval(fdt,tdt):
    fenxiao_array= []
    fenxiao_dict = {}
    fenxiao_sum  = 0
    fenxiao = MergeTrade.objects.filter(pay_time__gte=fdt,
                                        pay_time__lte=tdt,
                                        type=pcfg.FENXIAO_TYPE,
                                        sys_status=pcfg.FINISHED_STATUS)
    #buyer_nick 
    for f in fenxiao:
        
        buyer_nick=f.buyer_nick
        if fenxiao_dict.has_key(buyer_nick):
            fenxiao_dict[buyer_nick] = fenxiao_dict[buyer_nick]+float(f.payment or 0)
        else:
            fenxiao_dict[buyer_nick] = float(f.payment or 0)
    fenxiao_array = fenxiao_dict.items()
    
    fenxiao_array.sort(lambda x,y:cmp(x[1],y[1]))
    for key in fenxiao_array:
        fenxiao_sum=fenxiao_sum+key[1]
    fenxiao_array.append(["sum",fenxiao_sum])

    return fenxiao_array
    
    
def countFenxiaoAcount(request):
    
    content  = request.POST
    fromDate = content.get('fromDate')
    toDate   = content.get('endDate')
    
    toDate   = (toDate 
                and datetime.datetime.strptime(toDate, '%Y%m%d').date() 
                or datetime.datetime.now().date())
        
    fromDate = (fromDate 
                and datetime.datetime.strptime(fromDate, '%Y%m%d').date() 
                or toDate - datetime.timedelta(days=1)) 
    fromDateShow = fromDate.strftime('%Y%m%d')
    toDateShow   = toDate.strftime('%Y%m%d')
    fenxiaoDict = calFenxiaoInterval(fromDate,toDate)
    print 'fromDateShow',fromDateShow
    
    return render_to_response('trades/trade_fenxiao_count.html', 
                              {'data': fenxiaoDict,
                               'fromDateShow':fromDateShow,
                               'toDateShow':toDateShow,},
                              context_instance=RequestContext(request))


def showFenxiaoDateilFilter(fenxiao,fdt,tdt):
    fenxiao = MergeTrade.objects.filter(buyer_nick=fenxiao,
                                        pay_time__gte=fdt,
                                        pay_time__lte=tdt,
                                        type=pcfg.FENXIAO_TYPE,
                                        sys_status=pcfg.FINISHED_STATUS)
#    print "fenxiao",fenxiao[2].tid 
    return fenxiao
    
def showFenxiaoDetail(request):
    
    content = request.GET
    fenxiao = content.get('fenxiao')
   
    fromDate  = content.get('fdt').replace('-','')
    oneday    = datetime.timedelta(days=1)
    toDate    = content.get('tdt')
    
    if toDate:
        toDate=datetime.date.today().strftime('%Y%m%d')
    else:
        toDate  =toDate.replace('-','')

    toDate   = (toDate  
                and datetime.datetime.strptime(toDate, '%Y%m%d').date() 
                or datetime.datetime.now().date())
    toDate = toDate+oneday
    fromDate = (fromDate 
                and datetime.datetime.strptime(fromDate, '%Y%m%d').date() 
                or toDate - datetime.timedelta(days=1))
# date  over
    iid = []
    tid = []
    created    = []
    buyer_nick = []
    receiver_name   = []
    receiver_mobile = []
    receiver_state  = []
    receiver_city   = []
    receiver_district = []
    receiver_address  = []
    payment = []

    fenxiao_render_data = []    

    FenxiaoDateil=showFenxiaoDateilFilter(fenxiao,fromDate,toDate)
#    FenxiaoDateil=showFenxiaoDateilFilter('爱生活791115','20140526','20140527')
    for c in FenxiaoDateil:
        tid.append(c.tid)
        iid.append(c.id)
        created.append(c.created)
        buyer_nick.append(c.buyer_nick)
        receiver_name.append(c.receiver_name)
        receiver_mobile.append(c.receiver_mobile)
        receiver_state.append(c.receiver_state)
        receiver_city.append(c.receiver_city)
        receiver_district.append(c.receiver_district)
        receiver_address.append(c.receiver_address)
        payment.append(c.payment)
        
    for i,v in enumerate(tid):
       
        fenxiao_render_data.append((buyer_nick[i],
                                    tid[i],
                                    receiver_name[i],
                                    receiver_mobile[i],
                                    receiver_state[i],
                                    receiver_city[i],
                                    receiver_district[i],
                                    receiver_address[i],
                                    payment[i],iid[i]))
     
    return render_to_response('trades/trade_fenxiao_detail.html',
                              {'FenxiaoDateil':FenxiaoDateil,
                               'fenxiao_render_data':fenxiao_render_data,},  
                              context_instance=RequestContext(request))
                                                                  
########################## 提升订单优先级 ###########################
class ImprovePriorityView(ModelView):
    """ docstring for class OrderListView """
    
    def post(self, request, id, *args, **kwargs):
        
        row = MergeTrade.objects.filter(id=id).update(priority=pcfg.PRIORITY_HIG)
        
        return {'success':row > 0}
    
########################## 订单重量入库 ###########################
class PackageScanCheckView(ModelView):
    """ 订单扫描验货 """
    
    def isValidYundaId(self,package_no):
        if len(package_no) < 13:
            return False
        
        yunda_company = LogisticsCompany.objects.get(code='YUNDA')
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])
        
    def parsePackageNo(self,package_no):
        
        if not self.isValidYundaId(package_no):
            return package_no
        
        return package_no[0:13]  
    
    def getOrderItemsFromTrade(self,trade):
        
        order_items = []
        for order in trade.print_orders:
            
            barcode = Product.objects.getBarcodeByOuterid(order.outer_id,
                                                          order.outer_sku_id)
            product = Product.objects.getProductByOuterid(order.outer_id)
            product_sku = None
            if order.outer_sku_id:
                product_sku = Product.objects.getProductSkuByOuterid(order.outer_id,
                                                                        order.outer_sku_id)
            is_need_check = product_sku and product_sku.post_check or product.post_check
            
            order_dict = {'barcode':barcode,
                          'order_id':order.id,
                          'outer_id':order.outer_id,
                          'outer_sku_id':order.outer_sku_id,
                          'title':order.title,
                          'sku_properties_name':order.sku_properties_name,
                          'sku_name':product_sku and product_sku.name or '',
                          'pic_path':product.pic_path,
                          'num':order.num,
                          'post_check':is_need_check,
                          'status':order.get_status_display()
                          }
            
            order_items.append(order_dict)
            
        return order_items
        
    def get(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no','').strip()
        if not package_no:
            return u'运单号不能为空'
        
        package_id = self.parsePackageNo(package_no)
        try:
            mt  =  MergeTrade.objects.get(out_sid=package_id,
                                          reason_code='',
                                          sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        except MergeTrade.DoesNotExist:
            return u'运单号未找到订单'
        except MergeTrade.MultipleObjectsReturned:
            return u'结果返回多个订单'
        
        order_items = self.getOrderItemsFromTrade(mt)
        
        return {'package_no':package_id,
                'trade_id':mt.id,
                'order_items':order_items}
    
        
    def post(self, request,*args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no','').strip()
        
        if not package_no:
            return u'运单号不能为空'
        
        package_id = self.parsePackageNo(package_no)
        try:
            mt = MergeTrade.objects.get(out_sid=package_id,
                                        reason_code='',
                                        sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        except MergeTrade.DoesNotExist:
            return u'运单号未找到订单或被拦截'
        
        except MergeTrade.MultipleObjectsReturned:
            return u'运单号返回多个订单'
            
        mt.sys_status = pcfg.WAIT_SCAN_WEIGHT_STATUS
        mt.scanner    = request.user.username
        mt.save()
        
        log_action(mt.user.user.id,mt,CHANGE,u'扫描验货')
        
        return {'isSuccess':True}
        
    
########################## 订单重量入库 ###########################
class PackageScanWeightView(ModelView):
    """ 订单扫描称重 """
    
    def isValidYundaId(self,package_no):
        if len(package_no) < 13:
            return False
        
        yunda_company = LogisticsCompany.objects.get(code='YUNDA')
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])
        
    def parsePackageNo(self,package_no):
        
        if not self.isValidYundaId(package_no):
            return package_no
        
        return package_no[0:13]  
    
        
    def get(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no','').strip()
        if not package_no:
            return u'运单号不能为空'
        
        package_id = self.parsePackageNo(package_no)
        
        try:
            mt  =  MergeTrade.objects.get(out_sid=package_id,
                                          reason_code='',
                                          sys_status__in=(pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                          pcfg.WAIT_CHECK_BARCODE_STATUS))
        except MergeTrade.DoesNotExist:
            return u'运单号未找到订单或被拦截'
        except MergeTrade.MultipleObjectsReturned:
            return u'运单号返回多个订单'

        return {'package_no':package_id,
                'trade_id':mt.id,
                'seller_nick':mt.user.nick,
                'trade_type':mt.get_type_display(),
                'buyer_nick':mt.buyer_nick,
                'sys_status':mt.get_sys_status_display(),
                'company_name':mt.logistics_company.name,
                'receiver_mobile':mt.receiver_mobile,
                'receiver_name':mt.receiver_name,
                'receiver_state':mt.receiver_state,
                'receiver_city':mt.receiver_city,
                'receiver_district':mt.receiver_district,
                'receiver_address':mt.receiver_address
                }
    
        
    def post(self, request,*args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no','').strip()
        package_weight = content.get('package_weight','').strip()
        
        if not package_no:
            return u'运单号不能为空'
        
        try:
            if float(package_weight) > 100000:
                return u'重量超过100千克'
        except:
            return u'重量异常:%s'%package_weight
        
        package_id = self.parsePackageNo(package_no)
        try:
            mt = MergeTrade.objects.get(out_sid=package_id,
                                        reason_code='',
                                        sys_status__in=(pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                        pcfg.WAIT_CHECK_BARCODE_STATUS))
        except MergeTrade.DoesNotExist:
            return u'运单号未找到订单'
        except MergeTrade.MultipleObjectsReturned:
            return u'结果返回多个订单'
            
        MergeTrade.objects.updateProductStockByTrade(mt)
            
        mt.weight  = package_weight
        mt.sys_status = pcfg.FINISHED_STATUS
        mt.weight_time = datetime.datetime.now()
        mt.weighter = request.user.username
        mt.save()
        
        log_action(mt.user.user.id,mt,CHANGE,u'扫描称重')
        
        return {'isSuccess':True}
    

class SaleMergeOrderView(ModelView):
    """ docstring for class StatisticsMergeOrderView """
    
    def parseStartDt(self,start_dt):
        
        if not start_dt:
            dt  = datetime.datetime.now()
            return datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        
        if len(start_dt)>10:
            return parse_datetime(start_dt)
        
        return parse_date(start_dt)
    
    def parseEndDt(self,end_dt):
        
        if not end_dt:
            dt  = datetime.datetime.now()
            return datetime.datetime(dt.year,dt.month,dt.day,23,59,59)
        
        if len(end_dt)>10:
            return parse_datetime(end_dt)
        
        return parse_date(end_dt)
    
    def getSourceTrades(self,statistic_by,wait_send,p_outer_id,start_dt,end_dt):
        
        trade_qs  = MergeTrade.objects.filter(type=pcfg.WX_TYPE)

        if statistic_by == 'pay':
            trade_qs = trade_qs.filter(pay_time__gte=start_dt,pay_time__lte=end_dt)
        elif statistic_by == 'weight':
            trade_qs = trade_qs.filter(weight_time__gte=start_dt,weight_time__lte=end_dt)

        if wait_send:
            trade_qs = trade_qs.filter(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
        else:
            trade_qs = trade_qs.filter(status__in=pcfg.ORDER_SUCCESS_STATUS)
        
        final_trade_qs = []
        if p_outer_id:
            for trade in trade_qs:
                e_orders = trade.inuse_orders.filter(outer_id=p_outer_id)
                if e_orders.count() > 0:
                    final_trade_qs.append(object)
            
        return trade_qs
    
    def getEffectOrdersId(self,order_qs):
        
        return [o.oid for o in order_qs if o.num]
        
    def getProductByOuterId(self,outer_id):
        
        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None
        
    def getProductSkuByOuterId(self,outer_id,outer_sku_id):
        
        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except:
            return None
        
    def getTradeSortedItems(self,order_qs):
        
        trade_items  = {}
        for order in order_qs:
            
            outer_id = order.outer_id or str(order.num_iid)
            outer_sku_id = order.outer_sku_id or str(order.sku_id)
            payment   = float(order.payment or 0)
            order_num = order.num  or 0
            prod     = self.getProductByOuterId(outer_id)
            prod_sku = self.getProductSkuByOuterId(outer_id,outer_sku_id)
            
            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order_num
                skus = trade_items[outer_id]['skus']
                
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num']   += order_num
                    skus[outer_sku_id]['cost']  += skus[outer_sku_id]['std_purchase_price']*order_num
                    skus[outer_sku_id]['sales'] += payment
                    #累加商品成本跟销售额
                    trade_items[outer_id]['cost']  += skus[outer_sku_id]['std_purchase_price']*order_num 
                    trade_items[outer_id]['sales'] += payment
                else:
                    prod_sku_name  = prod_sku.name if prod_sku else order.sku_properties_name
                    purchase_price = float(prod_sku.cost) if prod_sku else 0
                    #累加商品成本跟销售额
                    trade_items[outer_id]['cost']  += purchase_price*order_num 
                    trade_items[outer_id]['sales'] += payment
                    
                    skus[outer_sku_id] = {
                                          'sku_name':prod_sku_name,
                                          'num':order_num,
                                          'cost':purchase_price*order_num,
                                          'sales':payment,
                                          'std_purchase_price':purchase_price}
            else:
                prod_sku_name  = prod_sku.name if prod_sku else order.sku_properties_name
                purchase_price = float(prod_sku.cost) if prod_sku else payment/order_num    
                trade_items[outer_id]={
                                       'num':order_num,
                                       'title': prod.name if prod else order.title,
                                       'cost':purchase_price*order_num ,
                                       'sales':payment,
                                       'skus':{outer_sku_id:{
                                            'sku_name':prod_sku_name,
                                            'num':order_num,
                                            'cost':purchase_price*order_num ,
                                            'sales':payment,
                                            'std_purchase_price':purchase_price}}
                                       }
            
        return sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
    
    def getTotalRefundFee(self,order_qs):
        
        effect_oids = self.getEffectOrdersId(order_qs)
        
        return Refund.objects.filter(oid__in=effect_oids,status__in=(
                    pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_CONFIRM_GOODS,pcfg.REFUND_SUCCESS))\
                    .aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee',0)
    
    def responseCSVFile(self,request,trade_list):
        
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 
        pcsv =[]
        pcsv.append((u'订单序号',u'订单明细ID',u'订单ID',u'客户名称',u'商品编码','商品名称',u'规格编码',u'规格名称',
                                u'拍下数量',u'留言',u'备注',u'付款时间',u'收货人',u'固话',u'手机',u'省',u'市',u'区',u'详细地址',u'快递方式'))
        
        trade_ids = []
        rindex      = 1
        for itrade in queryset:
            trade_ids.append(itrade.id)
        
        for trade in queryset:
            index = 0
            for order in trade.print_orders:  
                pcsv.append(('%s'%p for p in [ (rindex ,'')[index],
                                                                            order.oid,
                                                                            trade.tid,
                                                                            trade.receiver_name,
                                                                            order.outer_id,
                                                                            order.title,
                                                                            order.outer_sku_id,
                                                                            order.sku_properties_name,
                                                                            order.num,
                                                                            trade.buyer_message,
                                                                            '%s%s'%(trade.seller_memo,trade.sys_memo),
                                                                            trade.pay_time,
                                                                            trade.receiver_name,
                                                                            trade.receiver_phone,
                                                                            trade.receiver_mobile,
                                                                            trade.receiver_state,
                                                                            trade.receiver_city,
                                                                            trade.receiver_district,
                                                                            trade.receiver_address,
                                                                            trade.get_shipping_type_display()]))
                index = 1
            rindex += 1
            
        tmpfile = StringIO.StringIO()
        writer  = CSVUnicodeWriter(tmpfile,encoding = is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
            
        response = HttpResponse(tmpfile.getvalue(), mimetype='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment;filename=orderdetail-%s.csv'%str(int(time.time()))
        
        return response
    
    def get(self, request, *args, **kwargs):
        
        content   = request.REQUEST
        start_dt  = content.get('df','').strip()
        end_dt    = content.get('dt','').strip()
        shop_id   = content.get('shop_id')
        p_outer_id   = content.get('outer_id','')
        statistic_by = content.get('sc_by','pay')
        wait_send = content.get('wait_send','')
        
        start_dt  = self.parseStartDt(start_dt)
        end_dt    = self.parseEndDt(end_dt)
        
        trade_qs  = self.getSourceTrades(shop_id, statistic_by, wait_send, p_outer_id, start_dt, end_dt)
        order_qs  = self.getSourceOrders(trade_qs,p_outer_id = p_outer_id)
        
        buyer_nums   = trade_qs.values_list('buyer_nick').distinct().count()
        trade_nums   = trade_qs.count()
        total_post_fee = trade_qs.aggregate(total_post_fee=Sum('post_fee')).get('total_post_fee',0)
        refund_fees  = self.getTotalRefundFee(order_qs)
        
        trade_list   = self.getTradeSortedItems(order_qs)
        total_cost   = 0
        total_sales  = 0
        
        for trade in trade_list:
            total_cost  += trade[1]['cost']
            total_sales += trade[1]['sales']
            trade[1]['skus'] = sorted(trade[1]['skus'].items(),key=lambda d:d[1]['num'],reverse=True)
        
        return {'df':format_datetime(start_dt),
                'dt':format_datetime(end_dt),
                'sc_by':statistic_by,
                'outer_id':p_outer_id,
                'wait_send':wait_send,
                'shops':User.effect_users.all(),
                'trade_items':trade_list, 
                'shop_id':shop_id and int(shop_id) or '',
                'total_cost':total_cost and round(total_cost,2) or 0 ,
                'total_sales':total_sales and round(total_sales,2) or 0,
                'refund_fees':refund_fees and round(refund_fees,2) or 0,
                'buyer_nums':buyer_nums,
                'trade_nums':trade_nums,
                'post_fees':total_post_fee }
        
    post = get    
