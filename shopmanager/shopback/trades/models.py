#-*- coding:utf8 -*-
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.fenxiao.models import PurchaseOrder
from shopback.orders.models import Trade
from shopback.logistics.models import Logistics,LogisticsCompany
from shopback.refunds.models import Refund
from shopback.monitor.models import SystemConfig
from shopback.signals import merge_trade_signal,rule_signal,merge_buyer_trade_signal
import logging

logger = logging.getLogger('trades.handler')
FENXIAO_TYPE_NAME = 'fenxiao'


WAIT_AUDIT_STATUS = 'WAIT_AUDIT'
WAIT_PREPARE_SEND_STATUS = 'WAIT_PREPARE_SEND'
WAIT_SCAN_WEIGHT_STATUS = 'WAIT_SCAN_WEIGHT'
WAIT_CONFIRM_SEND_STATUS = 'WAIT_CONFIRM_SEND'
SYSTEM_SEND_TAOBAO_STATUS = 'SYSTEM_SEND_TAOBAO'
FINISHED_STATUS = 'FINISHED'
AUDITFAIL_STATUS = 'AUDITFAIL'
INVALID_STATUS = 'INVALID' 
ON_THE_FLY_STATUS= 'ON_THE_FLY' #客户端不可操作

SYS_STATUS = (
    (WAIT_AUDIT_STATUS,'待审核'),
    (WAIT_PREPARE_SEND_STATUS,'待发货准备'),
    (WAIT_SCAN_WEIGHT_STATUS,'待扫描称重'),
    (WAIT_CONFIRM_SEND_STATUS,'待确认发货'),
    (SYSTEM_SEND_TAOBAO_STATUS,'待更新发货状态'),
    (FINISHED_STATUS,'已发货'),
    (AUDITFAIL_STATUS,'问题单'),
    (INVALID_STATUS,'已作废'),
    (ON_THE_FLY_STATUS,'飞行模式')
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

    sys_status     = models.CharField(max_length=32,db_index=True,choices=SYS_STATUS,blank=True,default='')
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
 
class MergeBuyerTrade(models.Model):
    
    sub_tid    =  models.BigIntegerField(primary_key=True)
    main_tid   =  models.BigIntegerField()
    created    =  models.DateTimeField(null=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_trades_mergebuyertrade'
 
def set_storage_trade_sys_status(merge_trade,trade,has_refund,full_refund): 
    
    if trade.status == WAIT_SELLER_SEND_GOODS: 
        shipping_type = trade.shipping_type if hasattr(trade,'shipping_type') else trade.shipping
        is_need_merge = False
        #当前订单是否可以合单
        if (not has_refund or (has_refund and not full_refund)) and hasattr(trade,'buyer_nick'):
            try:
                MergeBuyerTrade.objects.get(sub_tid=trade.id)
            except MergeBuyerTrade.DoesNotExist:
                user_trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick,type=trade.type).exclude(tid=trade.id)\
                        .exclude(sys_status__in=(INVALID_STATUS,FINISHED_STATUS,SYSTEM_SEND_TAOBAO_STATUS,'',WAIT_CONFIRM_SEND_STATUS)).order_by('-created')
                if user_trades.count()>0:
                    main_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[ut.tid for ut in user_trades])
                    main_merge_trade = main_buyer_trades[0] if main_buyer_trades.count()>0 else user_trades[0]
                    if main_merge_trade.sys_status == WAIT_AUDIT_STATUS:
                        merge_trade.sys_status = ON_THE_FLY_STATUS
                        is_need_merge = True
                    else:
                        main_merge_trade.sys_status = AUDITFAIL_STATUS
                        main_merge_trade.reverse_audit_reason = '--买家要求合单'.decode('utf8')
                        rows = MergeTrade.objects.filter(tid=main_merge_trade.tid,).exclude(sys_status__in=
                            (WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS,FINISHED_STATUS,INVALID_STATUS))\
                            .update(sys_status=main_merge_trade.sys_status,reverse_audit_reason=main_merge_trade.reverse_audit_reason)
                        if rows > 0:
                            merge_trade.sys_status = ON_THE_FLY_STATUS
                            is_need_merge = True

                    if is_need_merge:
                        try:
                            MergeBuyerTrade.objects.create(sub_tid=trade.id,main_tid=main_merge_trade.tid)
                            merge_buyer_trade_signal.send(sender=Trade,sub_tid=trade.id,main_tid=main_merge_trade.tid)
                            #合单后对主订单重新进行留言匹配
                            rule_signal.send(sender='trade_rule',trade_id=main_merge_trade.tid)
                        except Exception,exc:
                            logger.error('%s'%exc,exc_info=True)
                    
        if not has_refund and merge_trade.sys_status != ON_THE_FLY_STATUS:
            system_config = SystemConfig.getconfig()
            seller_memo = trade.memo  if hasattr(trade,'memo') else trade.seller_memo
            buyer_message = trade.buyer_message if hasattr(trade,'buyer_message') else trade.supplier_memo
            
            #如果虚拟发货的商品，直接进入到待确认发货
            if system_config.is_rule_auto and not merge_trade.sys_status: 
                
                try:
                    #如果有订单信息不足规则匹配到，则抛出异常
                    rule_signal.send(sender='product_rule',trade_id=trade.id)
                except Exception,exc:
                    merge_trade.sys_status = WAIT_AUDIT_STATUS
                else:
                     
                    #如果有留言备注，则该单需要审核
                    if seller_memo or buyer_message:
                        merge_trade.sys_status = WAIT_AUDIT_STATUS
                    else:
                        #不需进入待审核的订单，直接将交易匹配信息填入
                        merge_trade.sys_status = WAIT_PREPARE_SEND_STATUS
                        if shipping_type in ('free','express','FAST','SELLER'):
                            default_company = LogisticsCompany.objects.all().order_by('-priority')[0]
                            merge_trade.logistics_company_code=default_company.code
                            merge_trade.logistics_company_name=default_company.name
                    #不在订单信息不足规则中的交易，则将订单系统备注规则匹配    
                    rule_signal.send(sender='trade_rule',trade_id=trade.id)
                    
                #如果订单指定使用平邮或EMS，则直接将物流信息更改为POST，EMS 
                if shipping_type in ('post','ems'):
                    post_company = LogisticsCompany.objects.filter(code=shipping_type.upper())
                    merge_trade.logistics_company_code=post_company.code
                    merge_trade.logistics_company_name=post_company.name 
                    
            #如果订单第一次入库，并且系统没有开启自动匹配规则，则所有订单进入待审核                  
            elif not merge_trade.sys_status :
                merge_trade.sys_status = WAIT_AUDIT_STATUS 
                if shipping_type in ('post','ems'):
                    post_company = LogisticsCompany.objects.filter(code=shipping_type.upper())
                    merge_trade.logistics_company_code=post_company.code
                    merge_trade.logistics_company_name=post_company.name
                    
            #如果订单非第一次入库，有新加留言则进入问题单
            elif not merge_trade.seller_memo and seller_memo and merge_trade.sys_status  not in (WAIT_AUDIT_STATUS,AUDITFAIL_STATUS):
                merge_trade.sys_status = AUDITFAIL_STATUS
                merge_trade.reverse_audit_times += 1
                merge_trade.reverse_audit_reason += '--卖家有新备注'.decode('utf8') 
                
        #全部退款的订单，如果状态不再作废或问题单域，则改为问题单        
        elif full_refund :
            merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.id)
            for merge_buyer_trade in merge_buyer_trades:    
                reverse_reason = '合单的主订单全退款'.decode('utf8')
                MergeTrade.objects.get(tid=merge_buyer_trade.sub_tid,sys_status=ON_THE_FLY_STATUS).update(sys_status=AUDITFAIL_STATUS,
                                       reverse_audit_reason=reverse_reason,reverse_audit_times=1,total_num=0)
            if merge_trade.sys_status not in (INVALID_STATUS,AUDITFAIL_STATUS,FINISHED_STATUS):
                    merge_trade.sys_status = AUDITFAIL_STATUS
                    merge_trade.reverse_audit_times += 1
                    merge_trade.reverse_audit_reason += '--买家要求全退款'.decode('utf8')
        elif has_refund:
            #如果有部分退款，并且是第一次入库，则times=1,该单重复入库的时候状态不变
            if  not merge_trade.sys_status:   
                merge_trade.sys_status = WAIT_AUDIT_STATUS
                merge_trade.reverse_audit_times =1
            elif merge_trade.sys_status == ON_THE_FLY_STATUS:
                if not is_need_merge:
                    try:
                        merge_buyer_trade = MergeBuyerTrade.objects.get(sub_tid=trade.id)
                    except:
                        logger.error('飞行模式订单(id:%d)部分退款时，对应主订单未找到'%(trade.id))
                    else:
                        try:
                            main_merge_trade =MergeTrade.objects.get(tid=merge_buyer_trade.main_tid)
                        except:
                            logger.error('主订单(id:%s)未找到'%(merge_buyer_trade.main_tid))
                        else:
                            main_merge_trade.sys_status = AUDITFAIL_STATUS
                            main_merge_trade.reverse_audit_reason = '--买家要求部分退款'.decode('utf8')
                            main_merge_trade.reverse_audit_times += 1
                            MergeTrade.objects.filter(tid=main_merge_trade.tid).exclude(sys_status__in=(FINISHED_STATUS,INVALID_STATUS))\
                                .update(sys_status=main_merge_trade.sys_status,reverse_audit_reason=main_merge_trade.reverse_audit_reason,
                                reverse_audit_times=main_merge_trade.reverse_audit_times)
                            merge_buyer_trade_signal.send(sender=Trade,sub_tid=trade.id,main_tid=main_merge_trade.tid)
                            #更新主订单备注信息
                            rule_signal.send(sender='trade_rule',trade_id=main_merge_trade.tid)
                            
            elif merge_trade.reverse_audit_times == 0:
                merge_trade.sys_status = AUDITFAIL_STATUS
                merge_trade.reverse_audit_times = 1
                merge_trade.reverse_audit_reason += '--买家要求部分退款'.decode('utf8')
   
            #部分退款交易，备注规则匹配  
            rule_signal.send(sender='trade_rule',trade_id=trade.id)          

    #如果淘宝订单状态已改变，而系统内部状态非最终状态，则将订单作废        
    elif merge_trade.sys_status:
         if merge_trade.sys_status not in (FINISHED_STATUS,INVALID_STATUS):
             merge_trade.sys_status = INVALID_STATUS  
             merge_trade.reverse_audit_reason += '--订单流程非正常结束'.decode('utf8')
    
    
    
        
def save_orders_trade_to_mergetrade(sender, trade, *args, **kwargs):

    merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
    merge_trade.user = trade.user
    merge_trade.seller_id = trade.seller_id
    merge_trade.seller_nick = trade.seller_nick
    merge_trade.buyer_nick = trade.buyer_nick
    merge_trade.type = trade.type
    merge_trade.shipping_type = trade.shipping_type
    merge_trade.payment = trade.payment
    merge_trade.total_fee = trade.total_fee
    merge_trade.discount_fee = trade.discount_fee
    merge_trade.adjust_fee = trade.adjust_fee
    merge_trade.post_fee = trade.post_fee
    merge_trade.alipay_no = trade.buyer_alipay_no
    merge_trade.seller_cod_fee = trade.seller_cod_fee
    merge_trade.buyer_cod_fee = trade.buyer_cod_fee
    merge_trade.cod_fee = trade.cod_fee
    merge_trade.cod_status = trade.cod_status
    merge_trade.buyer_message = trade.buyer_message
    merge_trade.seller_memo = trade.seller_memo
    merge_trade.created = trade.created 
    merge_trade.pay_time = trade.pay_time
    merge_trade.modified = trade.modified
    
    if not merge_trade.sys_status:
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
    
    orders = trade.trade_orders.all()
    has_refund = False
    full_refund = True
    total_num   = 0
    for order in orders:
        if order.refund_id :
            has_refund = True
            full_refund &= True
        else :  
            total_num += order.num
            full_refund &= False
    
    merge_trade.has_refund = has_refund
    merge_trade.total_num = total_num
    set_storage_trade_sys_status(merge_trade,trade,has_refund,full_refund)    
    MergeTrade.objects.filter(tid=trade.id).update(
        user = merge_trade.user,
        seller_id = merge_trade.seller_id,
        seller_nick = merge_trade.seller_nick,
        buyer_nick = merge_trade.buyer_nick,
        type = merge_trade.type,
        shipping_type = merge_trade.shipping_type,
        payment = merge_trade.payment,
        total_fee = merge_trade.total_fee,
        discount_fee = merge_trade.discount_fee,
        adjust_fee   = merge_trade.adjust_fee,
        post_fee = merge_trade.post_fee,
        alipay_no  = merge_trade.alipay_no,
        seller_cod_fee = merge_trade.seller_cod_fee,
        buyer_cod_fee  = merge_trade.buyer_cod_fee,
        cod_fee    = merge_trade.cod_fee,
        cod_status = merge_trade.cod_status,
        buyer_message = merge_trade.buyer_message,
        seller_memo = merge_trade.seller_memo,
        created = merge_trade.created,
        pay_time = merge_trade.pay_time,
        modified = merge_trade.modified,
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
        sys_status = merge_trade.sys_status,
        logistics_company_code = merge_trade.logistics_company_code,
        logistics_company_name = merge_trade.logistics_company_name,
        reverse_audit_times = merge_trade.reverse_audit_times,
        reverse_audit_reason = merge_trade.reverse_audit_reason, 
    )

merge_trade_signal.connect(save_orders_trade_to_mergetrade,sender=Trade,dispatch_uid='merge_trade')



def save_fenxiao_orders_to_mergetrade(sender, trade, *args, **kwargs):
    if not trade.id:
        return 
    merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
    merge_trade.user = trade.user
    merge_trade.seller_id = trade.seller_id
    merge_trade.seller_nick = trade.supplier_username
    merge_trade.buyer_nick = trade.distributor_username
    merge_trade.type = FENXIAO_TYPE_NAME
    merge_trade.shipping_type = SHIPPING_TYPE.get(trade.shipping,trade.shipping)
    merge_trade.payment = trade.distributor_payment
    merge_trade.total_fee = trade.total_fee
    merge_trade.post_fee = trade.post_fee
    merge_trade.alipay_no = trade.alipay_no

    merge_trade.buyer_message = trade.memo
    merge_trade.seller_memo = trade.supplier_memo
    merge_trade.created = trade.created 
    merge_trade.pay_time = trade.created
    merge_trade.modified = trade.modified
    
    if not merge_trade.sys_status and trade.status not in (TRADE_NO_CREATE_PAY,WAIT_BUYER_PAY,TRADE_CLOSED) :
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
    
    orders = trade.sub_purchase_orders.all()
    has_refund = False
    full_refund = True
    total_num   = 0
    for order in orders:
        is_refund = order.order_200_status in ('TRADE_CLOSED','TRADE_REFUNDING','TRADE_REFUNDED')
        if is_refund :
            has_refund = True
            full_refund &= True
        else :  
            total_num += order.num
            full_refund &= False
    
    merge_trade.has_refund = has_refund
    merge_trade.total_num = total_num
    set_storage_trade_sys_status(merge_trade,trade,has_refund,full_refund)
    MergeTrade.objects.filter(tid=trade.id).update(
        user = merge_trade.user,
        seller_id = merge_trade.seller_id,
        seller_nick = merge_trade.seller_nick,
        buyer_nick = merge_trade.buyer_nick,
        type = merge_trade.type,
        shipping_type = merge_trade.shipping_type,
        payment = merge_trade.payment,
        total_fee = merge_trade.total_fee,
        post_fee = merge_trade.post_fee,
        buyer_message = merge_trade.buyer_message,
        seller_memo = merge_trade.seller_memo,
        created = merge_trade.created,
        pay_time = merge_trade.pay_time,
        modified = merge_trade.modified,
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
        sys_status = merge_trade.sys_status,
        logistics_company_code = merge_trade.logistics_company_code,
        logistics_company_name = merge_trade.logistics_company_name,
        reverse_audit_times = merge_trade.reverse_audit_times,
        reverse_audit_reason = merge_trade.reverse_audit_reason, 
    )

merge_trade_signal.connect(save_fenxiao_orders_to_mergetrade,sender=PurchaseOrder,dispatch_uid='merge_purchaseorder')



        