#-*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseNotFound
from django.conf import settings
from django.core.urlresolvers import reverse
from auth import staff_requried
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from djangorestframework.views import ModelView
from shopback.trades.models import MergeTrade,MergeOrder
from shopback.items.models import ProductSku,Item
from shopback.refunds.models import RefundProduct,Refund,REFUND_STATUS,CS_STATUS_CHOICES
from auth.utils import parse_datetime,parse_date,format_time,map_int2str
from shopback.refunds.tasks import updateAllUserRefundOrderTask
from shopback import paramconfig as pcfg


__author__ = 'meixqhi'


@staff_requried(login_url=settings.LOGIN_URL)
def update_interval_refunds(request,dt_f,dt_t):

    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    logistics_task = updateAllUserRefundOrderTask.delay(update_from=dt_f,update_to=dt_t)

    ret_params = {'task_id':logistics_task.task_id}

    return HttpResponse(json.dumps(ret_params),mimetype='application/json')


############################### 缺货订单商品列表 #################################       
class RefundManagerView(ModelView):
    """ docstring for class RefundManagerView """
    
    def get(self, request, *args, **kwargs):
        
        handling_refunds = Refund.objects.filter(has_good_return=True,is_reissue=False,
                                status__in=(pcfg.REFUND_WAIT_RETURN_GOODS,pcfg.REFUND_CONFIRM_GOODS))
        handling_tids = []
        refund_dict  = {}
        for refund in handling_refunds:
            refund_tid = refund.tid
            handling_tids.append(refund_tid)
            if refund_dict.has_key(refund_tid):
                refund_dict[refund_tid]['order_num'] += 1
                refund_dict[refund_tid]['is_reissue'] &= refund.is_reissue
            else:
                try:
                    receiver_name = MergeTrade.objects.filter(tid=refund_tid).receiver_name
                except:
                    receiver_name = ''
                has_refund_prod = RefundProduct.objects.filter(trade_id=refund_tid).count()>0
                refund_dict[refund_tid] = {'tid':refund_tid,
                                           'buyer_nick':refund.buyer_nick,
                                           'seller_nick':refund.seller_nick,
                                           'receiver_name':receiver_name,
                                           'order_num':1,
                                           'created':refund.created.strftime('%Y.%m.%d'),
                                           'reason':refund.reason,
                                           'desc':refund.desc,
                                           'company_name':refund.company_name,
                                           'sid':refund.sid,
                                           'is_reissue':refund.is_reissue,
                                           'has_refund_prod':has_refund_prod,
                                           'cs_status':dict(CS_STATUS_CHOICES).get(refund.cs_status,u'状态不对'),
                                           'status':dict(REFUND_STATUS).get(refund.status,u'状态不对'),
                                           }
        
        refund_items = sorted(refund_dict.items(),key=lambda d:d[1]['created'],reverse=True)
        
        refund_list  = [v for k,v in refund_items]
        
        unrelate_prods = []
        unfinish_prods = RefundProduct.objects.filter(is_finish=False)
        for prod in unfinish_prods:
            if not prod.trade_id or prod.trade_id not in handling_tids:
                unrelate_prods.append(prod)

        return {'refund_trades':refund_list,'unrelate_prods':unrelate_prods}
        
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        tid     = content.get('tid')
        if not tid :
            return u'请输入交易ID'
        
        try:
            merge_trade = MergeTrade.objects.get(tid=tid)
        except:
            return u'订单未找到'
        refund_orders = Refund.objects.filter(tid=tid)
        refund_products  = RefundProduct.objects.filter(trade_id=tid)
        
        op_str  = render_to_string('refunds/refund_order_product.html', 
                { 'refund_orders': refund_orders,
                 'refund_products': refund_products ,
                 'STATIC_URL':settings.STATIC_URL,
                 'trade':merge_trade})
        
        return {'template_string':op_str,'trade_id':tid,}
        #return { 'refund_orders': refund_orders,'refund_products': refund_products ,'STATIC_URL':settings.STATIC_URL}
    
    
############################### 退货商品订单 #################################       
class RefundProductView(ModelView):
    """ docstring for class RefundProductView """
    
    def get(self, request, *args, **kwargs):
        
        return {}
    
    def post(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        outer_id   = content.get('outer_id')
        outer_sku_id = content.get('outer_sku_id')

        prod_sku = None
        prod     = None
        if outer_sku_id:
            try:
                prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
            except:
                pass
        else:
            try:
                prod     = Product.objects.get(outer_id=outer_id)
            except:
                pass
        rf_prod    = RefundProduct.objects.filter(outer_id='')
        if rf_prod.count() >0:
            rf = rf_prod[0]
        else:
            rf = RefundProduct()
            
        for k,v in content.iteritems():
            hasattr(rf,k) and setattr(rf,k,v)
        rf.can_reuse = content.get('can_reuse') == 'true' and True or False
        rf.title = prod_sku.product.name if prod_sku else prod.name
        rf.property = prod_sku.properties_alias or prod_sku.properties_name if prod_sku else ''
        
        rf.save()
        
        return rf
    
############################### 退货单 #################################       
class RefundView(ModelView):
    """ docstring for class RefundView """
    
    def get(self, request, *args, **kwargs):

        content   = request.REQUEST
        q  = content.get('q')
        if not q:
            return u'请输入查询内容'
        
        queryset = Refund.objects.filter(has_good_return=True)
        if q.isdigit():
            rf_prods  = queryset.filter(Q(mobile=q)|Q(phone=q)|Q(sid=q)|Q(refund_id=q)|Q(tid=q))
        else:
            rf_prods  = queryset.filter(Q(buyer_nick=q)|Q(mobile=q)|Q(phone=q)|Q(sid=q))
            
        prod_list = []
        for rp in rf_prods:
            
            tid  = rp.tid
            oid  = rp.oid
            
            try:
                order = MergeOrder.objects.get(tid=tid,oid=oid)
            except:
                return u'订单未找到'
            
            outer_id = order.outer_id 
            outer_sku_id = order.outer_sku_id

            prod_sku = None
            prod     = None
            if outer_sku_id:
                try:
                    prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
                except:
                    pass
            else:
                try:
                    prod     = Product.objects.get(outer_id=outer_id)
                except:
                    pass
                
            prod_dict = {}
            prod_dict['refund_id']  = rp.refund_id
            prod_dict['buyer_nick'] = rp.buyer_nick
            prod_dict['mobile']     = rp.mobile
            prod_dict['phone']      = rp.phone
            
            prod_dict['company_name'] = rp.company_name
            prod_dict['sid']        = rp.sid
            prod_dict['created']    = rp.created
            prod_dict['status']     = rp.status
            
            prod_dict['title']     = prod_sku.product.name if prod_sku else prod.name
            prod_dict['property']  = (prod_sku.properties_alias or prod_sku.properties_name) if prod_sku else ''
            
            prod_list.append(prod_dict)
            
        return prod_list
    
    
    def post(self, request, *args, **kwargs):
        
        content    = request.REQUEST

        rf = RefundProduct()
        for k,v in content.iteritems():
            if k=='can_reuse':
                v = v=="true" and True or False
            hasattr(rf,k) and setattr(rf,k,v)
        
        rf.save()
        return rf  
 

@csrf_exempt
@staff_member_required
def create_refund_exchange_trade(request,tid):
    
    try:
        origin_trade = MergeTrade.objects.get(tid=tid)
    except:
        return HttpResponseNotFound('<h1>订单未找到 404<h1>')
    refunds  = Refund.objects.filter(tid=tid)
    rfprods  = RefundProduct.objects.filter(trade_id=tid)
    if rfprods.count()<0:
        return HttpResponseNotFound('<h1>未找到退货商品 404<h1>')
    
    dt = datetime.datetime.now()
    merge_trade = MergeTrade.objects.create(
                                            user = origin_trade.user,
                                            seller_id = origin_trade.seller_id,
                                            seller_nick = origin_trade.seller_nick,
                                            buyer_nick = origin_trade.buyer_nick,
                                            type = pcfg.EXCHANGE_TYPE,
                                            shipping_type = origin_trade.shipping_type,
                                            logistics_company = origin_trade.logistics_company,
                                            receiver_name = origin_trade.receiver_name,
                                            receiver_state = origin_trade.receiver_state,
                                            receiver_city = origin_trade.receiver_city,
                                            receiver_district = origin_trade.receiver_district,
                                            receiver_address = origin_trade.receiver_address,
                                            receiver_zip = origin_trade.receiver_zip,
                                            receiver_mobile = origin_trade.receiver_mobile,
                                            receiver_phone = origin_trade.receiver_phone,
                                            sys_status = pcfg.WAIT_AUDIT_STATUS,
                                            status=pcfg.WAIT_SELLER_SEND_GOODS,
                                            created=dt,
                                            pay_time=dt,
                                            modified=dt
                                            )
    for prod in rfprods.filter(can_reuse=True):
        merge_order = MergeOrder()
        merge_order.merge_trade = merge_trade
        merge_order.title       = prod.title
        merge_order.sku_properties_name   = prod.property
        merge_order.outer_id       = prod.outer_id
        merge_order.outer_sku_id   = prod.outer_sku_id
        merge_order.seller_nick    = origin_trade.seller_nick
        merge_order.buyer_nick     = origin_trade.buyer_nick
        merge_order.gift_type      = pcfg.RETURN_GOODS_GIT_TYPE
        merge_order.sys_status     = pcfg.IN_EFFECT
        merge_order.created        = dt
        merge_order.save()
    
    refunds.update(is_reissue=True)
    rfprods.update(is_finish=True)    
    
    return HttpResponseRedirect('/admin/trades/mergetrade/?type__exact=exchange&sys_status=WAIT_AUDIT&q=%s'%str(merge_trade.id))  
   

@csrf_exempt
@staff_member_required   
def delete_trade_order(request,id):
    
    user_id      = request.user.id
    try:
        refund_prod  = RefundProduct.objects.get(id=id)
    except:
        HttpResponse(json.dumps({'code':1,'response_error':u'订单不存在'}),mimetype="application/json")
    
    refund_prod.delete()    
    ret_params = {'code':0,'response_content':{'success':True}}

    return HttpResponse(json.dumps(ret_params),mimetype="application/json")    


@csrf_exempt
@staff_member_required
def relate_refund_product(request):
    
    content      = request.REQUEST
    refund_tid   = content.get('refund_tid')
    rpid         = content.get('rpid')
    print refund_tid,rpid
    try:
        trade  = MergeTrade.objects.get(tid=refund_tid)
    except:
        return HttpResponse(json.dumps({'code':1,'response_error':u'订单不存在'}),mimetype="application/json")
        
    try:
        refund_prod  = RefundProduct.objects.get(id=rpid)
    except:
        return HttpResponse(json.dumps({'code':1,'response_error':u'退回商品不存在'}),mimetype="application/json")
    
    refund_prod.trade_id   = trade.tid   
    refund_prod.buyer_nick = trade.buyer_nick 
    refund_prod.save() 
    ret_params = {'code':0,'response_content':{'success':True}}

    return HttpResponse(json.dumps(ret_params),mimetype="application/json")    

 