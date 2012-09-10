#-*- coding:utf8 -*-
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.orders.models import Trade,REFUND_APPROVAL_STATUS,REFUND_WAIT_SELLER_AGREE
from shopback.items.models import Item,Product,ProductSku
from shopback.logistics.models import Logistics,LogisticsCompany
from shopback.fenxiao.models import PurchaseOrder,SubPurchaseOrder
from shopback.refunds.models import Refund
from shopback.monitor.models import SystemConfig
from shopback.signals import merge_trade_signal,rule_signal,merge_buyer_trade_signal
import logging

logger = logging.getLogger('trades.handler')
FENXIAO_TYPE = 'fenxiao'
TAOBAO_TYPE  = 'taobao'


WAIT_PREPARE_SEND_STATUS = 'WAIT_PREPARE_SEND'
WAIT_CHECK_BARCODE_STATUS = 'WAIT_CHECK_BARCODE'
WAIT_SCAN_WEIGHT_STATUS = 'WAIT_SCAN_WEIGHT'
WAIT_CONFIRM_SEND_STATUS = 'WAIT_CONFIRM_SEND'
SYSTEM_SEND_TAOBAO_STATUS = 'SYSTEM_SEND_TAOBAO' 
FINISHED_STATUS = 'FINISHED'
AUDITFAIL_STATUS = 'AUDITFAIL'
INVALID_STATUS = 'INVALID' 
REGULAR_REMAIN_STATUS = 'REGULAR_REMAIN'
ON_THE_FLY_STATUS= 'ON_THE_FLY' #客户端不可操作

SYS_STATUS = (
    (WAIT_PREPARE_SEND_STATUS,'待发货准备'),
    (WAIT_CHECK_BARCODE_STATUS,'待扫描验货'),
    (WAIT_SCAN_WEIGHT_STATUS,'待扫描称重'),
    (WAIT_CONFIRM_SEND_STATUS,'待确认发货'),
    (SYSTEM_SEND_TAOBAO_STATUS,'待更新发货状态'),
    (FINISHED_STATUS,'已发货'),
    (AUDITFAIL_STATUS,'问题单'),
    (INVALID_STATUS,'已作废'),
    (ON_THE_FLY_STATUS,'飞行模式'),
    (REGULAR_REMAIN_STATUS,'定时提醒')
)


TRADE_NO_CREATE_PAY = 'TRADE_NO_CREATE_PAY'
WAIT_BUYER_PAY      = 'WAIT_BUYER_PAY'
WAIT_SELLER_SEND_GOODS = 'WAIT_SELLER_SEND_GOODS'
WAIT_BUYER_CONFIRM_GOODS = 'WAIT_BUYER_CONFIRM_GOODS'
TRADE_BUYER_SIGNED = 'TRADE_BUYER_SIGNED'
TRADE_FINISHED     = 'TRADE_FINISHED'
TRADE_CLOSED       = 'TRADE_CLOSED'
TRADE_CLOSED_BY_TAOBAO = 'TRADE_CLOSED_BY_TAOBAO'

TAOBAO_TRADE_STATUS = (
    ('TRADE_NO_CREATE_PAY','没有创建支付宝交易'),
    ('WAIT_BUYER_PAY','等待买家付款'),
    ('WAIT_SELLER_SEND_GOODS','等待卖家发货'),
    ('WAIT_BUYER_CONFIRM_GOODS','等待买家确认收货'),
    ('TRADE_BUYER_SIGNED','买家已签收,货到付款专用'),
    ('TRADE_FINISHED','交易成功'),
    ('TRADE_CLOSED','付款以后用户退款成功，交易自动关闭'),
    ('TRADE_CLOSED_BY_TAOBAO','付款以前，卖家或买家主动关闭交易'),
)


TRADE_TYPE = (
    ('fixed','一口价'),
    ('auction','拍卖'),
    ('guarantee_trade','一口价、拍卖'),
    ('auto_delivery','自动发货'),
    ('independent_simple_trade','旺店入门版交易'),
    ('independent_shop_trade','旺店标准版交易'),
    ('ec','直冲'),
    ('cod','货到付款'),
    ('fenxiao','分销'),
    ('game_equipment','游戏装备'),
    ('shopex_trade','ShopEX交易'),
    ('netcn_trade','万网交易'),
    ('external_trade','统一外部交易'),
)
SHIPPING_TYPE = {
    'FAST':'express',
    'EMS':'ems',
    'ORDINARY':'post',
    'SELLER':'free',
}

class MergeTrade(models.Model):

    tid   =  models.BigIntegerField(primary_key=True)
    
    user       = models.ForeignKey(User,null=True,related_name='merge_trades')
    seller_id  = models.CharField(max_length=64,blank=True)
    seller_nick = models.CharField(max_length=64,blank=True)
    buyer_nick  = models.CharField(max_length=64,blank=True)
    
    type = models.CharField(max_length=32,choices=TRADE_TYPE,blank=True)
    shipping_type = models.CharField(max_length=12,blank=True)
    
    total_num  =   models.IntegerField(null=True,default=0)
    payment    =   models.CharField(max_length=10,blank=True)
    discount_fee = models.CharField(max_length=10,blank=True)
    adjust_fee =   models.CharField(max_length=10,blank=True)
    post_fee   =   models.CharField(max_length=10,blank=True)
    total_fee  =   models.CharField(max_length=10,blank=True)
    alipay_no  =   models.CharField(max_length=128,blank=True)
    
    seller_cod_fee = models.CharField(max_length=10,blank=True)
    buyer_cod_fee  = models.CharField(max_length=10,blank=True)
    cod_fee        = models.CharField(max_length=10,blank=True)
    cod_status     = models.CharField(max_length=32,blank=True)
    
    weight        = models.CharField(max_length=10,blank=True)
    post_cost    = models.CharField(max_length=10,blank=True)
    
    buyer_message = models.TextField(max_length=1000,blank=True)
    seller_memo = models.TextField(max_length=1000,blank=True)
    sys_memo    = models.TextField(max_length=500,blank=True)
    
    created    = models.DateTimeField(db_index=True,null=True,blank=True)
    pay_time   = models.DateTimeField(db_index=True,null=True,blank=True)
    modified   = models.DateTimeField(db_index=True,null=True,blank=True) 
    consign_time = models.DateTimeField(db_index=True,null=True,blank=True)
    
    out_sid    = models.CharField(max_length=64,db_index=True,blank=True)
    logistics_company_code  = models.CharField(max_length=64,blank=True)
    logistics_company_name  = models.CharField(max_length=64,blank=True)
    receiver_name    =  models.CharField(max_length=64,blank=True)
    receiver_state   =  models.CharField(max_length=16,blank=True)
    receiver_city    =  models.CharField(max_length=16,blank=True)
    receiver_district  =  models.CharField(max_length=16,blank=True)

    receiver_address   =  models.CharField(max_length=128,blank=True)
    receiver_zip       =  models.CharField(max_length=10,blank=True)
    receiver_mobile    =  models.CharField(max_length=20,blank=True)
    receiver_phone     =  models.CharField(max_length=20,blank=True)
    
    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)
    
    reverse_audit_times = models.IntegerField(default=0)
    reverse_audit_reason = models.TextField(max_length=1000,blank=True)
    status  = models.CharField(max_length=32,db_index=True,choices=TAOBAO_TRADE_STATUS,blank=True)
        
    is_picking_print = models.BooleanField(default=False)
    is_express_print = models.BooleanField(default=False)
    is_send_sms      = models.BooleanField(default=False)
    has_refund       = models.BooleanField(default=False)
    out_goods        = models.BooleanField(default=False)
    has_memo         = models.BooleanField(default=False)
    remind_time      = models.DateTimeField(blank=True)
    refund_num       = models.IntegerField(db_index=True,null=True,default=0)
    
    sys_status     = models.CharField(max_length=32,db_index=True,choices=SYS_STATUS,blank=True,default='')
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
        
        
    def has_trade_refunding(self):
        if self.type == 'fenxiao':
            sub_orders = SubPurchaseOrder.objects.filter(id=self.tid,status='TRADE_REFUNDING')
            if sub_orders.count()>0:
                return True
        else:
            orders = Order.objects.filter(id=self.tid,refund_status=REFUND_WAIT_SELLER_AGREE)
            if orders.count()>0:
                return True
        return False
        
    @classmethod
    def judge_out_stock(cls,trade_id,trade_from):
        if trade_from == FENXIAO_TYPE:
            return False
        
        is_out_stock = False
        try:
            trade = Trade.objects.get(id=trade_id)
        except Trade.DoesNotExist:
            logger.error('trade(tid:%d) does not exist'%trade_id)
        else:
            orders = trade.trade_orders.exclude(refund_status__in=REFUND_APPROVAL_STATUS)
            for order in orders:
                if order.outer_sku_id:
                    try:
                        product_sku = ProductSku.objects.get(outer_id=order.outer_sku_id)    
                    except:
                        pass
                    else:
                        is_out_stock |= product_sku.out_stock
                elif order.outer_id:
                    try:
                        product = Product.objects.get(outer_id=order.outer_id)
                    except:
                        pass
                    else:
                        is_out_stock |= product.out_stock
                        
        return is_out_stock
    
    @classmethod
    def judge_new_refund(cls,trade_id,trade_from):
        has_new_refund = False
        new_full_refund = False
        merge_trades = cls.objects.get(tid=trade_id)
        
        refund_orders_num = 0
        if trade_from == TAOBAO_TYPE:    
            trade   = Trade.objects.get(id=trade_id)
            refund_orders_num = trade.trade_orders.exclude(refund_status='').count()
            total_orders_num  = trade.trade_orders.count()
        else:            
            purchase_trade = PurchaseOrder.objects.get(id=trade_id)
            refund_orders_num = purchase_trade.sub_purchase_orders.filter(status__in=('TRADE_REFUNDED','TRADE_REFUNDING')).count()
            total_orders_num  = purchase_trade.sub_purchase_orders.count()
            
        if merge_trades.refund_num < refund_orders_num and refund_orders_num == total_orders_num:
            cls.objects.filter(tid=trade_id).update(refund_num=refund_orders_num)
            new_full_refund = True
            has_new_refund = True
        elif merge_trades.refund_num < refund_orders_num:
            cls.objects.filter(tid=trade_id).update(refund_num=refund_orders_num)
            has_new_refund = True    
        
        return has_new_refund,new_full_refund
    
    @classmethod
    def judge_rule_match(cls,trade_id,trade_from):
        if trade_from == FENXIAO_TYPE:
            return False
        
        has_rule_match = False
        try:
            rule_signal.send(sender='product_rule',trade_id=trade_id)
        except:
            has_rule_match = True
            
        return has_rule_match
     
                        
        
class MergeBuyerTrade(models.Model):
    
    sub_tid    =  models.BigIntegerField(primary_key=True)
    main_tid   =  models.BigIntegerField()
    created    =  models.DateTimeField(null=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_trades_mergebuyertrade'



def set_storage_trade_sys_status(merge_trade,trade,trade_from,is_first_save):
    shipping_type = trade.shipping if trade_from==FENXIAO_TYPE else trade.shipping_type
    seller_memo   = trade.memo  if hasattr(trade,'memo') else trade.seller_memo
    buyer_message = trade.buyer_message if hasattr(trade,'buyer_message') else trade.supplier_memo
    
    has_new_memo = merge_trade.seller_memo != seller_memo or merge_trade.buyer_message != buyer_message
    has_new_refund,full_new_refund = MergeTrade.judge_new_refund(trade.id, trade_from) #新退款，新的全退款

    merge_trade.has_memo = has_new_memo
    merge_trade.has_refund = has_new_refund
    if trade.status == WAIT_SELLER_SEND_GOODS:
        #初次入库 
        if is_first_save: 
            #无退款或部分退款
            if not full_new_refund:
                is_out_stock = MergeTrade.judge_out_stock(trade.id, trade_from)
                #缺货
                if is_out_stock:
                    merge_trade.out_goods = True
                    merge_trade.sys_status = AUDITFAIL_STATUS
                    merge_trade.reverse_audit_reason = '订单缺货'.decode('utf8')
                else:
                    is_need_merge = False
                    #分销订单不进行合单
                    if trade_from==TAOBAO_TYPE:
                        user_trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick).exclude(tid=trade.id).filter(sys_status__in=
                                (INVALID_STATUS,FINISHED_STATUS,'',REGULAR_REMAIN_STATUS)).order_by('-created')
                        is_need_merge = True if user_trades.count()>0 else False

                    #合单
                    if is_need_merge:
                        merge_trade.sys_status = ON_THE_FLY_STATUS
                        merge_trade.reverse_audit_reason = '订单需合并'.decode('utf8')
                        
                        main_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[ut.tid for ut in user_trades])
                        if main_buyer_trades.count()>0:
                            main_merge_trade = MergeTrade.objects.get(tid=main_buyer_trades[0].main_tid)
                        else:
                            main_merge_trade = user_trades[0] 
                        
                        if main_merge_trade.sys_status in (WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS):
                            main_merge_trade.sys_status = AUDITFAIL_STATUS
                            main_merge_trade.reverse_audit_reason = '--买家要求合单(该订单已扫描称重，需找出重新发货)'.decode('utf8')
                        else:
                            main_merge_trade.sys_status = AUDITFAIL_STATUS
                            main_merge_trade.reverse_audit_reason = '--买家要求合单'.decode('utf8')
                        update_rows = MergeTrade.objects.filter(tid=main_merge_trade.tid,).exclude(sys_status__in=(FINISHED_STATUS,INVALID_STATUS))\
                            .update(sys_status=main_merge_trade.sys_status,reverse_audit_reason=main_merge_trade.reverse_audit_reason) 
                        
                        if update_rows>0:
                            MergeBuyerTrade.objects.create(sub_tid=trade.id,main_tid=main_merge_trade.tid)
                            merge_buyer_trade_signal.send(sender=Trade,sub_tid=trade.id,main_tid=main_merge_trade.tid)
                            rule_signal.send(sender='trade_rule',trade_id=main_merge_trade.tid)
                    else:
                        has_rule_match = MergeTrade.judge_rule_match(trade.id, trade_from)
                        #规则匹配
                        if has_rule_match:
                            merge_trade.sys_status = ON_THE_FLY_STATUS
                            merge_trade.reverse_audit_reason = '订单有规则匹配'.decode('utf8')
                        else:
                            #有留言
                            if has_new_memo:
                                merge_trade.sys_status = AUDITFAIL_STATUS
                                merge_trade.reverse_audit_reason = '有留言'.decode('utf8')
                            else:
                                merge_trade.sys_status = WAIT_PREPARE_SEND_STATUS
                #进行留言匹配
                rule_signal.send(sender='trade_rule',trade_id=trade.id)
                if shipping_type in ('free','express','FAST','SELLER'):
                    default_company = LogisticsCompany.objects.all().order_by('-priority')[0]
                    merge_trade.logistics_company_code=default_company.code
                    merge_trade.logistics_company_name=default_company.name 
                elif shipping_type in ('post','ems'):
                    post_company = LogisticsCompany.objects.filter(code=shipping_type.upper())
                    merge_trade.logistics_company_code=post_company.code
                    merge_trade.logistics_company_name=post_company.name                
            else:
                merge_trade.sys_status = AUDITFAIL_STATUS
                merge_trade.reverse_audit_reason = '订单全退款'.decode('utf8')
        #再次入库
        else:
            #当前订单在待匹配状态
            if merge_trade.sys_status == ON_THE_FLY_STATUS:
                try:
                    merge_buyer_trade = MergeBuyerTrade.objects.get(sub_tid=trade.id)
                except:
                    #如果待匹配全退款,其他状态不变
                    if full_new_refund:
                        merge_trade.sys_status = AUDITFAIL_STATUS
                        merge_trade.reverse_audit_reason += '订单全退款'.decode('utf8')
                else:
                    #如果全退款
                    if full_new_refund:
                        merge_trade.sys_status = AUDITFAIL_STATUS
                        merge_trade.reverse_audit_reason += '合单订单全退款'.decode('utf8')
          
                        main_trade = MergeTrade.objects.get(tid=merge_buyer_trade.main_tid)
                        main_trade.sys_status = AUDITFAIL_STATUS
                        main_trade.reverse_audit_reason += ('合单子订单(%d)全退款'.decode('utf8'))%trade.id
                        MergeTrade.objects.filter(tid=merge_buyer_trade.main_tid)\
                            .update(reverse_audit_reason=main_trade.reverse_audit_reason,sys_status=main_trade.sys_status)    
                            
                        MergeBuyerTrade.objects.filter(sub_tid=trade.id).delete()
                    #无退款或部分退款则需要重新合单
                    else:
                        main_trade = MergeTrade.objects.get(tid=merge_buyer_trade.main_tid)
                        main_trade.sys_status = AUDITFAIL_STATUS
                        main_trade.reverse_audit_reason += ('合单子订单(%d)部分退款'.decode('utf8'))%trade.id if has_new_refund else '子订单更新'.decode('utf8')
                        MergeTrade.objects.filter(tid=merge_buyer_trade.main_tid)\
                            .update(reverse_audit_reason=main_trade.reverse_audit_reason,sys_status=main_trade.sys_status)
                        
                        merge_buyer_trade_signal.send(sender=Trade,sub_tid=trade.id,main_tid=merge_buyer_trade.main_tid)
                            
            elif  merge_trade.sys_status == REGULAR_REMAIN_STATUS: 
                #全退款
                if full_new_refund:
                    merge_trade.sys_status = AUDITFAIL_STATUS
                    merge_trade.reverse_audit_reason += '定时提醒订单全退款'.decode('utf8')
                    
            elif  merge_trade.sys_status in (WAIT_PREPARE_SEND_STATUS,WAIT_CHECK_BARCODE_STATUS,
                                        WAIT_SCAN_WEIGHT_STATUS,WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS,AUDITFAIL_STATUS):      
                
                merge_trade.sys_status = AUDITFAIL_STATUS
                merge_trade.reverse_audit_reason += ('订单全退款'.decode('utf8') if full_new_refund else '订单部分退款'.decode('utf8'))\
                        if has_new_refund else '子订单更新'.decode('utf8')   
           
            rule_signal.send(sender='trade_rule',trade_id=trade.id)             
    #如果淘宝订单状态已改变，而系统内部状态非最终状态，则将订单作废        
    elif merge_trade.sys_status:
        if merge_trade.sys_status not in (FINISHED_STATUS,INVALID_STATUS):
            merge_trade.sys_status = INVALID_STATUS  
            merge_trade.reverse_audit_reason += '--订单流程非正常结束'.decode('utf8')
    
 
    
        
def save_orders_trade_to_mergetrade(sender, trade, *args, **kwargs):

    merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
    
    is_first_save = not merge_trade.sys_status 
    if is_first_save:
        merge_trade.receiver_name = trade.receiver_name
        merge_trade.receiver_state = trade.receiver_state
        merge_trade.receiver_city = trade.receiver_city
        merge_trade.receiver_district = trade.receiver_district
        merge_trade.receiver_address = trade.receiver_address
        merge_trade.receiver_zip = trade.receiver_zip
        merge_trade.receiver_mobile = trade.receiver_mobile
        merge_trade.receiver_phone = trade.receiver_phone
    merge_trade.status = trade.status
    
    dt = trade.created
    merge_trade.year  = dt.year
    merge_trade.hour  = dt.hour
    merge_trade.month = dt.month
    merge_trade.day   = dt.day
    merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1
    
    trade_from = TAOBAO_TYPE
    set_storage_trade_sys_status(merge_trade,trade,trade_from,is_first_save)    
    MergeTrade.objects.filter(tid=trade.id).update(
        user = trade.user,
        seller_id = trade.seller_id,
        seller_nick = merge_trade.seller_nick,
        buyer_nick = trade.buyer_nick,
        type = trade.type,
        shipping_type = trade.shipping_type,
        payment = trade.payment,
        total_fee = trade.total_fee,
        discount_fee = trade.discount_fee,
        adjust_fee   = trade.adjust_fee,
        post_fee = trade.post_fee,
        alipay_no  = trade.buyer_alipay_no,
        seller_cod_fee = trade.seller_cod_fee,
        buyer_cod_fee  = trade.buyer_cod_fee,
        cod_fee    = trade.cod_fee,
        cod_status = trade.cod_status,
        buyer_message = trade.buyer_message,
        seller_memo = trade.seller_memo,
        created = trade.created,
        pay_time = trade.pay_time,
        modified = trade.modified,
        receiver_name = merge_trade.receiver_name,
        receiver_state = merge_trade.receiver_state,
        receiver_city  = merge_trade.receiver_city,
        receiver_district = merge_trade.receiver_district, 
        receiver_address = merge_trade.receiver_address,
        receiver_zip = merge_trade.receiver_zip,
        receiver_mobile = merge_trade.receiver_mobile,
        receiver_phone = merge_trade.receiver_phone,
        status = merge_trade.status,
        year  = merge_trade.year,
        hour  = merge_trade.hour,
        month = merge_trade.month,
        day   = merge_trade.day,
        week  = merge_trade.week,
        has_refund = merge_trade.has_refund,
        total_num = merge_trade.total_num,
        has_memo = merge_trade.has_memo,
        out_goods = merge_trade.out_goods,
        sys_status = merge_trade.sys_status,
        logistics_company_code = merge_trade.logistics_company_code,
        logistics_company_name = merge_trade.logistics_company_name,
        reverse_audit_reason = merge_trade.reverse_audit_reason, 
    )

merge_trade_signal.connect(save_orders_trade_to_mergetrade,sender=Trade,dispatch_uid='merge_trade')



def save_fenxiao_orders_to_mergetrade(sender, trade, *args, **kwargs):
    if not trade.id:
        return 
    merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
    
    is_first_save = not merge_trade.sys_status 
    if is_first_save and trade.status not in (TRADE_NO_CREATE_PAY,WAIT_BUYER_PAY,TRADE_CLOSED) :
        logistics = Logistics.get_or_create(trade.seller_id,trade.id)
        merge_trade.receiver_name = logistics.receiver_name
        merge_trade.receiver_address = logistics.location
        merge_trade.receiver_mobile = logistics.receiver_mobile
        merge_trade.receiver_phone = logistics.receiver_phone
    merge_trade.status = trade.status
    
    dt = trade.created
    merge_trade.year  = dt.year
    merge_trade.hour  = dt.hour
    merge_trade.month = dt.month
    merge_trade.day   = dt.day
    merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1

    trade_from = FENXIAO_TYPE
    set_storage_trade_sys_status(merge_trade,trade,trade_from,is_first_save)
    MergeTrade.objects.filter(tid=trade.id).update(
        user = trade.user,
        seller_id = trade.seller_id,
        seller_nick = trade.supplier_username,
        buyer_nick = trade.distributor_username,
        type = FENXIAO_TYPE,
        shipping_type = SHIPPING_TYPE.get(trade.shipping,trade.shipping),
        payment = trade.distributor_payment,
        total_fee = trade.total_fee,
        post_fee = trade.post_fee,
        buyer_message = trade.memo,
        seller_memo = trade.supplier_memo,
        created = trade.created,
        pay_time = trade.created,
        modified = trade.modified,
        receiver_name = merge_trade.receiver_name,
        receiver_address = merge_trade.receiver_address,
        receiver_mobile = merge_trade.receiver_mobile,
        receiver_phone = merge_trade.receiver_phone,
        status = merge_trade.status,
        year  = merge_trade.year,
        hour  = merge_trade.hour,
        month = merge_trade.month,
        day   = merge_trade.day,
        week  = merge_trade.week,
        has_refund = merge_trade.has_refund,
        total_num = merge_trade.total_num,
        has_memo = merge_trade.has_memo,
        out_goods = merge_trade.out_goods,
        sys_status = merge_trade.sys_status,
        logistics_company_code = merge_trade.logistics_company_code,
        logistics_company_name = merge_trade.logistics_company_name,
        reverse_audit_reason = merge_trade.reverse_audit_reason, 
    )

merge_trade_signal.connect(save_fenxiao_orders_to_mergetrade,sender=PurchaseOrder,dispatch_uid='merge_purchaseorder')



        