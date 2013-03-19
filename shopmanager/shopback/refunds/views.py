#-*- encoding:utf8 -*-
import json
from django.http import HttpResponse
from django.conf import settings
from auth import staff_requried
from django.db.models import Q
from django.template.loader import render_to_string
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
        
        handling_refunds = Refund.objects.filter(has_good_return=True,
                                status__in=(pcfg.REFUND_WAIT_RETURN_GOODS,pcfg.REFUND_CONFIRM_GOODS))
        refund_dict  = {}
        
        for refund in handling_refunds:
            refund_tid = refund.tid
            if refund_dict.has_key(refund_tid):
                refund_dict[refund_tid]['order_num'] += 1
                refund_dict[refund_tid]['is_reissue'] &= refund.is_reissue
            else:
                refund_dict[refund_tid] = {'tid':refund_tid,
                                           'buyer_nick':refund.buyer_nick,
                                           'seller_nick':refund.seller_nick,
                                           'order_num':1,
                                           'created':refund.created,
                                           'reason':refund.reason,
                                           'desc':refund.desc,
                                           'company_name':refund.company_name,
                                           'sid':refund.sid,
                                           'is_reissue':refund.is_reissue,
                                           'cs_status':dict(CS_STATUS_CHOICES).get(refund.cs_status,u'状态不对'),
                                           'status':dict(REFUND_STATUS).get(refund.status,u'状态不对'),
                                           }
   
        return {'refund_trades':refund_dict,}
        
    def post(self, request, *args, **kwargs):
        
        content = request.REQUEST
        tid     = content.get('tid')
        if not tid :
            return '请输入交易ID'
        refund_orders = Refund.objects.filter(tid=tid)
        refund_products  = RefundProduct.objects.filter(trade_id=tid)
        
        op_str  = render_to_string('refunds/refund_order_product.html', 
                { 'refund_orders': refund_orders,'refund_products': refund_products ,'STATIC_URL':settings.STATIC_URL})
        
        return {'template_string':op_str,'trade_id':tid}
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
        refund_id  = content.get('refund_id')
        out_sid    = content.get('out_sid')
        company    = content.get('company')
        mobile     = content.get('mobile')
        phone      = content.get('phone')
        num        = content.get('num',1)
        
        try:
            refund = Refund.objects.get(refund_id=refund_id)
        except:
            return u'退款单未找到'
        
        tid  = refund.tid
        oid  = refund.oid
        
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
        
        rf_prod  = RefundProduct.objects.filter(outer_id='')
        if rf_prod.count() >0:
            rf = rf_prod[0]
        else:
            rf = RefundProduct()
        
        rf.buyer_nick =  refund.buyer_nick
        rf.buyer_mobile = mobile or refund.mobile
        rf.buyer_phone = phone or refund.phone
        rf.trade_id = refund.tid
        rf.oid      = refund.oid
        rf.out_sid =  out_sid or refund.sid
        rf.company =  company or refund.company_name
        
        rf.outer_id = outer_id
        rf.outer_sku_id = outer_sku_id
        rf.num   = num
        rf.can_reuse = content.get('can_reuse') == 'true' and True or False
        rf.title = prod_sku.product.name if prod_sku else prod.name
        rf.property = (prod_sku.properties_alias or prod_sku.properties_name) if prod_sku else ''
        
        rf.save()
        
        return rf  
    
    
def delete_trade_order(request,id):
    
    user_id      = request.user.id
    try:
        refund_prod  = RefundProduct.objects.get(id=id)
    except:
        HttpResponse(json.dumps({'code':1,'response_error':u'订单不存在'}),mimetype="application/json")
    
    refund_prod.delete()    
    ret_params = {'code':0,'response_content':{'success':True}}

    return HttpResponse(json.dumps(ret_params),mimetype="application/json")    

 