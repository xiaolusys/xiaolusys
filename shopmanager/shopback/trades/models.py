#-*- coding:utf8 -*-
import time
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from django.db.models import Sum
from shopback.orders.models import Trade,Order,REFUND_APPROVAL_STATUS,REFUND_WAIT_SELLER_AGREE,NO_REFUND,REFUND_STATUS,REFUND_SUCCESS
from shopback.items.models import Item,Product,ProductSku
from shopback.logistics.models import Logistics,LogisticsCompany
from shopback.fenxiao.models import PurchaseOrder,SubPurchaseOrder,FenxiaoProduct,TRADE_REFUNDING,TRADE_REFUNDED,TRADE_CLOSED\
    ,WAIT_CONFIRM_WAIT_SEND_GOODS,WAIT_CONFIRM_SEND_GOODS,WAIT_CONFIRM_GOODS_CONFIRM,CONFIRM_WAIT_SEND_GOODS,CONFIRM_SEND_GOODS,TRADE_REFUNDED,TRADE_REFUNDING
from shopback.refunds.models import Refund
from auth.utils import parse_datetime
from shopback.monitor.models import SystemConfig,Reason,NEW_MEMO_CODE,NEW_REFUND_CODE,NEW_MERGE_TRADE_CODE,WAITING_REFUND_CODE,\
    RULE_MATCH_CODE,OUT_GOOD_CODE,INVALID_END_CODE,POST_MODIFY_CODE
from shopback.signals import merge_trade_signal,rule_signal
import logging

logger = logging.getLogger('trades.handler')
FENXIAO_TYPE = 'fenxiao'
TAOBAO_TYPE  = 'taobao'

WAIT_AUDIT_STATUS = 'WAIT_AUDIT' #等待人工审核
WAIT_PREPARE_SEND_STATUS = 'WAIT_PREPARE_SEND' 
WAIT_CHECK_BARCODE_STATUS = 'WAIT_CHECK_BARCODE'
WAIT_SCAN_WEIGHT_STATUS = 'WAIT_SCAN_WEIGHT'
FINISHED_STATUS = 'FINISHED'
INVALID_STATUS = 'INVALID' 
REGULAR_REMAIN_STATUS = 'REGULAR_REMAIN'
ON_THE_FLY_STATUS= 'ON_THE_FLY' #合单
IN_EFFECT = "IN_EFFECT"

SYS_TRADE_STATUS = (
    (WAIT_AUDIT_STATUS,'问题单'),
    (WAIT_PREPARE_SEND_STATUS,'待发货准备'),
    (WAIT_CHECK_BARCODE_STATUS,'待扫描验货'),
    (WAIT_SCAN_WEIGHT_STATUS,'待扫描称重'),
    (FINISHED_STATUS,'已发货'),
    (INVALID_STATUS,'已作废'),
    (ON_THE_FLY_STATUS,'飞行模式'),
    (REGULAR_REMAIN_STATUS,'定时提醒')
)

SYS_ORDER_STATUS = (
    (IN_EFFECT ,'有效'),
    (INVALID_STATUS,'已作废'),
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
    (TRADE_NO_CREATE_PAY,'没有创建支付宝交易'),
    (WAIT_BUYER_PAY,'等待买家付款'),
    (WAIT_SELLER_SEND_GOODS,'等待卖家发货'),
    (WAIT_BUYER_CONFIRM_GOODS,'等待买家确认收货'),
    (TRADE_BUYER_SIGNED,'买家已签收,货到付款专用'),
    (TRADE_FINISHED,'交易成功'),
    (TRADE_CLOSED,'付款以后用户退款成功，交易自动关闭'),
    (TRADE_CLOSED_BY_TAOBAO,'付款以前，卖家或买家主动关闭交易'),
)

TAOBAO_ORDER_STATUS = (
    (TRADE_NO_CREATE_PAY,'没有创建支付宝交易'),
    (WAIT_BUYER_PAY,'等待买家付款'),
    (WAIT_SELLER_SEND_GOODS,'等待卖家发货'),
    (WAIT_BUYER_CONFIRM_GOODS,'等待买家确认收货'),
    (TRADE_BUYER_SIGNED,'买家已签收,货到付款专用'),
    (TRADE_FINISHED,'交易成功'),
    (TRADE_CLOSED,'付款以后用户退款成功，交易自动关闭'),
    (TRADE_CLOSED_BY_TAOBAO,'付款以前，卖家或买家主动关闭交易'),
    (WAIT_CONFIRM_WAIT_SEND_GOODS,"付款信息待确认，待发货"),
    (WAIT_CONFIRM_SEND_GOODS,"付款信息待确认，已发货"),
    (WAIT_CONFIRM_GOODS_CONFIRM,"付款信息待确认，已收货"),
    (CONFIRM_WAIT_SEND_GOODS,"付款信息已确认，待发货"),
    (CONFIRM_SEND_GOODS,"付款信息已确认，已发货"),
    (TRADE_REFUNDED,"已退款"),
    (TRADE_REFUNDING,"退款中"),
)

TRADE_TYPE = (
    ('fixed','一口价'),
    ('fenxiao','分销'),
    ('direct','内售'),
    ('auction','拍卖'),
    ('guarantee_trade','一口价、拍卖'),
    ('auto_delivery','自动发货'),
    ('independent_simple_trade','旺店入门版交易'),
    ('independent_shop_trade','旺店标准版交易'),
    ('ec','直冲'),
    ('cod','货到付款'),
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
    
    id    = BigIntegerAutoField(primary_key=True)
    tid   = models.BigIntegerField(unique=True,null=True,verbose_name='淘宝订单编号')
    
    user       = models.ForeignKey(User,null=True,related_name='merge_trades',verbose_name='所属店铺')
    seller_id  = models.CharField(max_length=64,blank=True,verbose_name='店铺ID')
    seller_nick = models.CharField(max_length=64,blank=True,verbose_name='店铺名称')
    buyer_nick  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='买家昵称')
    
    type = models.CharField(max_length=32,choices=TRADE_TYPE,blank=True,verbose_name='订单类型')
    shipping_type = models.CharField(max_length=12,blank=True,verbose_name='物流方式')
    
    total_num  =   models.IntegerField(null=True,default=0,verbose_name='商品数量')
    payment    =   models.CharField(max_length=10,blank=True,verbose_name='实付款')
    discount_fee = models.CharField(max_length=10,blank=True,verbose_name='折扣')
    adjust_fee =   models.CharField(max_length=10,blank=True,verbose_name='调整费用')
    post_fee   =   models.CharField(max_length=10,blank=True,verbose_name='物流费用')
    total_fee  =   models.CharField(max_length=10,blank=True,verbose_name='总费用')
    alipay_no  =   models.CharField(max_length=128,blank=True,verbose_name='用户支付宝帐号')
    
    seller_cod_fee = models.CharField(max_length=10,blank=True,verbose_name='卖家货到付款费用')
    buyer_cod_fee  = models.CharField(max_length=10,blank=True,verbose_name='买家货到付款费用')
    cod_fee        = models.CharField(max_length=10,blank=True,verbose_name='货到付款费用')
    cod_status     = models.CharField(max_length=32,blank=True,verbose_name='货到付款状态')
    
    weight        = models.CharField(max_length=10,blank=True,verbose_name='包裹重量')
    post_cost    = models.CharField(max_length=10,blank=True,verbose_name='物流成本')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name='买家留言')
    seller_memo = models.TextField(max_length=1000,blank=True,verbose_name='卖家备注')
    sys_memo    = models.TextField(max_length=500,blank=True,verbose_name='系统备注')
    
    created    = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='生成日期')
    pay_time   = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='付款日期')
    modified   = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='修改日期') 
    consign_time = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='发货日期')
    
    out_sid    = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='物流（快递）编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,blank=True,verbose_name='物流公司')
    receiver_name    =  models.CharField(max_length=64,blank=True,verbose_name='收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name='省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name='市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name='区')

    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name='详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name='邮编')
    receiver_mobile    =  models.CharField(max_length=20,blank=True,verbose_name='手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name='电话')
    
    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)
    
    reason_code = models.CharField(max_length=100,blank=True,verbose_name='问题编号')  #1|2|3 问题单原因编码集合
    status  = models.CharField(max_length=32,db_index=True,choices=TAOBAO_TRADE_STATUS,blank=True,verbose_name='淘宝订单状态')
        
    is_picking_print = models.BooleanField(default=False,verbose_name='打印发货单')
    is_express_print = models.BooleanField(default=False,verbose_name='打印物流单')
    is_send_sms      = models.BooleanField(default=False,verbose_name='短信提醒')
    has_refund       = models.BooleanField(default=False,verbose_name='有退款')
    has_memo         = models.BooleanField(default=False,verbose_name='有留言')
    remind_time      = models.DateTimeField(null=True,blank=True,verbose_name='定时日期')
    refund_num       = models.IntegerField(db_index=True,null=True,default=0,verbose_name='退款单数')  #退款数
    
    operator       =  models.CharField(max_length=32,verbose_name='操作员')
    sys_status     = models.CharField(max_length=32,db_index=True,choices=SYS_TRADE_STATUS,blank=True,default='',verbose_name='系统状态')
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
        verbose_name='订单'.decode('utf8')
    
    def __unicode__(self):
        return str(self.id)
    
    @property
    def user_full_address(self):
        return '%s%s%s%s%s'%(self.receiver_name,self.receiver_state,self.receiver_city,self.receiver_district,self.receiver_address)
    
    def append_reason_code(self,code):  
        reason_set = set(self.reason_code.split(','))
        old_len = len(reason_set)
        reason_set.add(str(code))
        new_len = len(reason_set)
        self.reason_code = ','.join(list(reason_set))
        MergeTrade.objects.filter(id=self.id).update(reason_code=self.reason_code)    
        return old_len<new_len
         
        
    def remove_reason_code(self,code):   
        reason_set = set(self.reason_code.split(','))
        try:
            reason_set.remove(str(code))
        except:
            return False
        else:
            self.reason_code = ','.join(list(reason_set))
            MergeTrade.objects.filter(id=self.id).update(reason_code=self.reason_code)
        return True
    
    def update_buyer_message(self,tid,msg):
        tid = str(tid)
        msg = msg.replace('|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        buyer_msg = self.buyer_message.split('|')
        msg_dict = {}
        for m in buyer_msg:
            m  = m.split(':')
            if len(m)==2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.tid)] = self.buyer_message.replace('|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        msg_dict[tid]=msg
        self.buyer_message = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
        MergeTrade.objects.filter(id=self.id).update(buyer_message=self.buyer_message)
        return self.buyer_message
    
    def remove_buyer_message(self,tid):
        tid = str(tid)
        buyer_msg = self.buyer_message.split('|')
        msg_dict = {}
        for m in buyer_msg:
            m  = m.split(':')
            if len(m)==2:
                msg_dict[m[0]] = m[1]
        if msg_dict:
            msg_dict.pop(tid,None)
            self.buyer_message = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
            MergeTrade.objects.filter(id=self.id).update(buyer_message=self.buyer_message)
        return self.buyer_message
        
        
    def update_seller_memo(self,tid,msg):
        tid = str(tid)
        msg = msg.replace('|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m  = m.split(':')
            if len(m)==2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.tid)] = self.seller_memo.replace('|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        msg_dict[tid]=msg
        self.seller_memo = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
        MergeTrade.objects.filter(id=self.id).update(seller_memo=self.seller_memo)
        return self.seller_memo
        
        
    def remove_seller_memo(self,tid):
        tid = str(tid)
        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m  = m.split(':')
            if len(m)==2:
                msg_dict[m[0]] = m[1]
        if msg_dict:
            msg_dict.pop(tid,None)
            self.seller_memo = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
            MergeTrade.objects.filter(id=self.id).update(buyer_message=self.seller_memo)
        return self.seller_memo
        
    def has_trade_refunding(self):
        #判断是否有等待退款的订单
        if self.type == 'fenxiao':
            sub_orders = SubPurchaseOrder.objects.filter(id=self.tid,status='TRADE_REFUNDING')
            if sub_orders.count()>0:
                return True
        else:
            orders = Order.objects.filter(trade=self.tid,refund_status=REFUND_WAIT_SELLER_AGREE)
            if orders.count()>0:
                return True
        return False
   
    @classmethod
    def judge_out_stock(cls,trade_id,trade_from):
        #判断是否有缺货，不支持分销平台
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
                        product_sku = ProductSku.objects.get(prod_outer_id=order.outer_id,outer_id=order.outer_sku_id)    
                    except:
                        pass
                    else:
                        is_out_stock  |= product_sku.out_stock
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
        #更新订单实际商品和退款商品数量，返回退款状态
        has_refund = False
        has_new_refund = False
        new_full_refund = False
        merge_trades = cls.objects.get(tid=trade_id)
        
        refund_orders_num = 0
        if trade_from == TAOBAO_TYPE:    
            trade   = Trade.objects.get(id=trade_id)
            refund_orders_num   = trade.trade_orders.exclude(refund_status=NO_REFUND).count()
            refund_approval_num = trade.trade_orders.filter(refund_status__in=REFUND_APPROVAL_STATUS).count()
            total_orders_num  = trade.trade_orders.count()
            quality   = trade.trade_orders.exclude(refund_status__in=REFUND_APPROVAL_STATUS)\
                .aggregate(real_nums=Sum('num'))['real_nums']
        else:            
            purchase_trade = PurchaseOrder.objects.get(id=trade_id)
            refund_approval_num = refund_orders_num = purchase_trade.sub_purchase_orders.filter(status__in=(TRADE_REFUNDED,TRADE_REFUNDING)).count()
            total_orders_num  = purchase_trade.sub_purchase_orders.count()
            quality   = purchase_trade.sub_purchase_orders.filter(status="WAIT_SELLER_SEND_GOODS")\
                .aggregate(real_nums=Sum('num'))['real_nums']
            
        if merge_trades.refund_num < refund_orders_num and refund_approval_num==total_orders_num:
            cls.objects.filter(tid=trade_id).update(total_num=quality,refund_num=refund_orders_num)
            new_full_refund = True
            has_new_refund = True
        elif merge_trades.refund_num < refund_orders_num:
            cls.objects.filter(tid=trade_id).update(total_num=quality,refund_num=refund_orders_num)
            has_new_refund = True    
        else:
            cls.objects.filter(tid=trade_id).update(total_num=quality)
        
        return refund_orders_num>0,has_new_refund,new_full_refund
    
    @classmethod
    def judge_rule_match(cls,trade_id,trade_from):
        
        #系统设置是否进行规则匹配
        config  = SystemConfig.getconfig()
        if not config.is_rule_auto:
            return False
        #分销部分不做规则匹配
        if trade_from == FENXIAO_TYPE:
            return False
        
        try:
            rule_signal.send(sender='product_rule',trade_id=trade_id)
        except:
            return True
        return False
    
    @classmethod
    def judge_merge_need(cls,trade_id,buyer_nick,trade_from,full_address):
        #分销部分不做规则匹配
        if trade_from == FENXIAO_TYPE:
            return False
        
        trades = cls.objects.filter(buyer_nick=buyer_nick,sys_status__in=(WAIT_PREPARE_SEND_STATUS,
                WAIT_AUDIT_STATUS)).exclude(tid=trade_id)
        
        for trade in trades:
            older_addr = trade.user_full_address
            trade_out_stock = cls.judge_out_stock(trade.tid, trade_from) 
            order_nums = Order.objects.filter(trade=trade.tid).exclude(refund_status__in=REFUND_APPROVAL_STATUS).count()
            #如果主订单不缺货，并且没有全退款,收货人急收货地址相同
            if not trade_out_stock and order_nums>0 and full_address==older_addr:
                return True
        
        return False
 
 
 
class MergeOrder(models.Model):
    
    id    = BigIntegerAutoField(primary_key=True)
    
    oid   = models.BigIntegerField(db_index=True,null=True,verbose_name='子订单编号')
    tid   = models.BigIntegerField(db_index=True,null=True,verbose_name='订单编号')
    
    cid    = models.BigIntegerField(db_index=True,null=True,verbose_name='商品分类')
    merge_trade = BigIntegerForeignKey(MergeTrade,null=True,related_name='merge_trade_orders',verbose_name='所属订单')

    num_iid  = models.CharField(max_length=64,blank=True,verbose_name='线上商品编号')
    title  =  models.CharField(max_length=128,verbose_name='商品标题')
    price  = models.CharField(max_length=12,blank=True,verbose_name='单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name='属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name='商品数量')
    
    outer_id = models.CharField(max_length=64,blank=True,verbose_name='订单商品外部编码')
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name='商品属性外部编码')
    
    total_fee = models.CharField(max_length=12,blank=True,verbose_name='总费用')
    payment = models.CharField(max_length=12,blank=True,verbose_name='实付款')
    discount_fee = models.CharField(max_length=12,blank=True,verbose_name='折扣')
    adjust_fee = models.CharField(max_length=12,blank=True,verbose_name='调整费用')

    sku_properties_name = models.CharField(max_length=256,blank=True,verbose_name='购买商品规格')
    
    refund_id = models.BigIntegerField(null=True,blank=True,verbose_name='退款号')
    refund_status = models.CharField(max_length=40,choices=REFUND_STATUS,blank=True,verbose_name='退款状态')
    
    pic_path = models.CharField(max_length=128,blank=True,verbose_name='商品图片')
    
    seller_nick = models.CharField(max_length=32,blank=True,db_index=True,verbose_name='卖家昵称')
    buyer_nick  = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='买家昵称')
     
    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)
    
    created       =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='创建日期')
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='付款日期')
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='发货日期')
    
    status = models.CharField(max_length=32,choices=TAOBAO_ORDER_STATUS,blank=True,verbose_name='淘宝订单状态')
    sys_status = models.CharField(max_length=32,choices=SYS_ORDER_STATUS,blank=True,default='',verbose_name='系统订单状态')
    
    class Meta:
        db_table = 'shop_trades_mergeorder'
        unique_together = ("oid","tid")
        verbose_name='子订单'.decode('utf8')
                        
        
class MergeBuyerTrade(models.Model):
    
    sub_tid    =  models.BigIntegerField(primary_key=True)
    main_tid   =  models.BigIntegerField(db_index=True)
    created    =  models.DateTimeField(null=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_trades_mergebuyertrade'
        verbose_name='合单记录'.decode('utf8')


def merge_trade_maker(sub_tid,main_tid):
    #合单操作
    trade      = Trade.objects.get(id=sub_tid)
    main_merge_trade = MergeTrade.objects.get(tid=main_tid)
    update_rows = MergeTrade.objects.filter(tid=main_tid,sys_status__in=(WAIT_AUDIT_STATUS,WAIT_PREPARE_SEND_STATUS))\
        .update(sys_status=WAIT_AUDIT_STATUS) 
    
    if update_rows>0:
        MergeBuyerTrade.objects.get_or_create(sub_tid=sub_tid,main_tid=main_tid)
        main_merge_trade.append_reason_code(NEW_MERGE_TRADE_CODE)
        orders = Order.objects.filter(trade=sub_tid)
        merge_order = MergeOrder()
        
        total_num = 0
        payment  = 0
        total_fee = 0
        discount_fee = 0
        for order in orders:
            for field in order._meta.fields:
                hasattr(merge_order,field.name) and setattr(merge_order,field.name,getattr(order,field.name))
            merge_order.id  = None
            merge_order.merge_trade = main_merge_trade
            merge_order.tid = main_tid
            merge_order.sys_status = IN_EFFECT
            merge_order.save()
            if order.refund_status not in REFUND_APPROVAL_STATUS:
                total_num += order.num
                payment   += float(order.payment)
                total_fee += float(order.total_fee)
                discount_fee += float(order.discount_fee)
        
        if trade.buyer_message:
            main_merge_trade.update_buyer_message(sub_tid,trade.buyer_message)
        if trade.seller_memo:
            main_merge_trade.update_seller_memo(sub_tid,trade.seller_memo)
        MergeTrade.objects.filter(tid=main_tid).update(total_num = total_num + main_merge_trade.total_num,
                                                       payment   = payment + float(main_merge_trade.payment),
                                                       total_fee = total_fee + float(main_merge_trade.total_fee),
                                                       discount_fee = discount_fee + float(main_merge_trade.discount_fee))
        rule_signal.send(sender='merge_trade_rule',trade_tid=main_tid)
        
        return True
        
    return False


    

def trade_download_controller(merge_trade,trade,trade_from,is_first_save):
    shipping_type = trade.shipping if trade_from==FENXIAO_TYPE else trade.shipping_type
    seller_memo   = trade.memo  if hasattr(trade,'memo') else trade.seller_memo
    buyer_message = trade.buyer_message if hasattr(trade,'buyer_message') else trade.supplier_memo
     
    merge_trade.has_memo = seller_memo or buyer_message

    if trade.status == WAIT_SELLER_SEND_GOODS:
        #新留言
        has_new_memo = merge_trade.seller_memo != seller_memo or merge_trade.buyer_message != buyer_message
        if has_new_memo:
            merge_trade.append_reason_code(NEW_MEMO_CODE)
            merge_trade.buyer_message = trade.buyer_message
            merge_trade.seller_memo   = trade.seller_memo
        #新退款
        has_refund,has_new_refund,full_new_refund = MergeTrade.judge_new_refund(trade.id, trade_from) #新退款，新的全退款
        if has_new_refund:
            merge_trade.append_reason_code(NEW_REFUND_CODE)
        #退款中
        wait_refunding = merge_trade.has_trade_refunding()
        if wait_refunding:
            merge_trade.append_reason_code(WAITING_REFUND_CODE)
        else:
            merge_trade.remove_reason_code(WAITING_REFUND_CODE)
        #设置订单是否有退款属性    
        merge_trade.has_refund = has_refund
        #初次入库 
        if is_first_save:
            #缺货 
            out_stock      =  MergeTrade.judge_out_stock(trade.id, trade_from)
            if out_stock:
                merge_trade.append_reason_code(OUT_GOOD_CODE)
            #规则匹配
            is_rule_match  =  MergeTrade.judge_rule_match(trade.id, trade_from)    
            if is_rule_match: 
                merge_trade.append_reason_code(RULE_MATCH_CODE)

            full_address = merge_trade.user_full_address
            #订单合并   
            is_merge_success = False
            if not full_new_refund:
                is_need_merge = MergeTrade.judge_merge_need(trade.id,trade.buyer_nick,trade_from,full_address)
                if is_need_merge:
                    trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick,sys_status__in=
                                                (WAIT_PREPARE_SEND_STATUS,WAIT_AUDIT_STATUS)).exclude(tid=trade.id).order_by('-created')
                    if trades.count()>0:
                        merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[t.tid for t in trades])
                        #如果有已有合并记录，则将现有主订单作为合并主订单
                        main_tid = None
                        if merge_buyer_trades.count()>0:
                            main_merge_tid = merge_buyer_trades[0].main_tid
                            main_trade = MergeTrade.objects.get(tid=main_merge_tid)
                            if main_trade.user_full_address == full_address:
                                main_tid = main_merge_tid
                        #如果没有则将按时间排序的第一符合条件的订单作为主订单
                        if not main_tid:
                            for t in trades:
                                if t.user_full_address == full_address:
                                    main_tid = t.tid
                                    break
                        if main_tid:  
                            #进行合单
                            is_merge_success = merge_trade_maker(trade.id,main_tid)
                            if is_merge_success:
                                 merge_trade.append_reason_code(NEW_MERGE_TRADE_CODE)
            #如果合单成功则将新单置为飞行模式                 
            if is_merge_success:
                merge_trade.sys_status = ON_THE_FLY_STATUS
            #有问题则进入问题单域
            elif has_new_memo or has_new_refund or wait_refunding or out_stock or is_rule_match:
                merge_trade.sys_status = WAIT_AUDIT_STATUS
            else:
                merge_trade.sys_status = WAIT_PREPARE_SEND_STATUS
                
            if shipping_type in ('free','express','FAST','SELLER'):
                receiver_city = merge_trade.receiver_city
                default_company = LogisticsCompany.get_recommend_express(receiver_city)
                merge_trade.logistics_company = default_company
            elif shipping_type in ('post','ems'):
                post_company = LogisticsCompany.objects.get(code=shipping_type.upper())
                merge_trade.logistics_company = post_company
            
        #再次入库
        else: 
            #如过该交易是合并后的子订单，如果有新留言或新退款，则需要将他的状态添加到合并主订单上面，
            #并将主订单置为问题单，如果全退，则将子订单的留言备注从主订单删除，并清除合并记录
            if merge_trade.sys_status == ON_THE_FLY_STATUS:
                merge_buyer_trade = MergeBuyerTrade.objects.get(sub_tid=trade.id)
                main_tid = merge_buyer_trade.main_tid
                #如果有新退款
                if has_new_refund:     
                    merge_trade.append_reason_code(NEW_REFUND_CODE)
                    for order in trade.trade_orders.all(): 
                        MergeOrder.objects.filter(oid=order.oid,tid=main_tid).update(status=order.status)  
                    main_merge_trade = MergeTrade.objects.get(tid=main_tid)
                    #全退款
                    if full_new_refund:
                        main_buyer_trade.delete()
                        main_merge_trade.remove_seller_memo(trade.id)
                        main_merge_trade.remove_buyer_message(trade.id)
                    MergeTrade.objects.filter(tid=main_tid,sys_status__in=(WAIT_AUDIT_STATUS,WAIT_PREPARE_SEND_STATUS))\
                        .update(sys_status=WAIT_AUDIT_STATUS)
                    main_merge_trade.append_reason_code(NEW_REFUND_CODE)
                    rule_signal.send(sender='merge_trade_rule',trade_tid=main_tid)    
                #新留言备注
                elif has_new_memo:
                    main_trade = MergeBuyerTrade.objects.get(tid=merge_trade.tid)
                    main_trade.update_seller_memo(tid,trade.seller_memo)
                    merge_trade.append_reason_code(NEW_MEMO_CODE)
                    MergeTrade.objects.filter(tid=main_tid,sys_status__in=(WAIT_AUDIT_STATUS,WAIT_PREPARE_SEND_STATUS))\
                        .update(sys_status=WAIT_AUDIT_STATUS)
                    main_merge_trade.append_reason_code(NEW_MEMO_CODE)
            elif merge_trade.sys_status in (WAIT_PREPARE_SEND_STATUS,WAIT_AUDIT_STATUS):
                #判断当前单是否是合并主订单
                try:
                    MergeBuyerTrade.objects.get(main_tid=trade.id)
                except MergeBuyerTrade.DoesNotExist:
                    is_main_trade = False
                except MergeBuyerTrade.MultipleObjectsReturned:
                    is_main_trade = True
                else:
                    is_main_trade = True
                
                if has_new_refund:
                    #如果主订单全退款，则主订单及子订单全部进入问题单，子订单需重新审批,合并记录全删除
                    if full_new_refund and is_main_trade:
                        merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.id)
                        for buyer_trades in merge_buyer_trades:
                            MergeTrade.objects.filter(tid=buyer_trades.sub_tid).update(sys_status=WAIT_AUDIT_STATUS)
                            buyer_trades.delete()
                    merge_trade.sys_status = WAIT_AUDIT_STATUS
                    merge_trade.append_reason_code(NEW_REFUND_CODE)
                elif has_new_memo:
                    merge_trade.sys_status = WAIT_AUDIT_STATUS
                    merge_trade.append_reason_code(NEW_MEMO_CODE)
                else:
                    merge_trade.append_reason_code(POST_MODIFY_CODE)
      
    #如果淘宝订单状态已改变，而系统内部状态非最终状态，则将订单作废        
    elif merge_trade.sys_status:
        if merge_trade.sys_status not in (FINISHED_STATUS,INVALID_STATUS):
            merge_trade.sys_status = INVALID_STATUS  
            merge_trade.append_reason_code(INVALID_END_CODE)
    
     
def save_orders_trade_to_mergetrade(sender, trade, *args, **kwargs):

    merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
    
    is_first_save = not merge_trade.sys_status 
    if is_first_save and trade.status not in (TRADE_NO_CREATE_PAY,WAIT_BUYER_PAY):
        #保存时
        merge_trade.receiver_name = trade.receiver_name
        merge_trade.receiver_state = trade.receiver_state
        merge_trade.receiver_city = trade.receiver_city
        merge_trade.receiver_district = trade.receiver_district
        merge_trade.receiver_address = trade.receiver_address
        merge_trade.receiver_zip = trade.receiver_zip
        merge_trade.receiver_mobile = trade.receiver_mobile
        merge_trade.receiver_phone = trade.receiver_phone
        merge_trade.save()
    merge_trade.status = trade.status
    
    dt = trade.created
    merge_trade.year  = dt.year
    merge_trade.hour  = dt.hour
    merge_trade.month = dt.month
    merge_trade.day   = dt.day
    merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1
    
    trade_from = TAOBAO_TYPE
    trade_download_controller(merge_trade,trade,trade_from,is_first_save)    
    MergeTrade.objects.filter(tid=trade.id).update(
        user = trade.user,
        seller_id = trade.seller_id,
        seller_nick = trade.seller_nick,
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
        buyer_message = merge_trade.buyer_message,
        seller_memo   = merge_trade.seller_memo,
        logistics_company = merge_trade.logistics_company,
        created = trade.created,
        pay_time = trade.pay_time,
        modified = trade.modified,
        consign_time = trade.consign_time,
        status = merge_trade.status,
        year  = merge_trade.year,
        hour  = merge_trade.hour,
        month = merge_trade.month,
        day   = merge_trade.day,
        week  = merge_trade.week,
        has_refund = merge_trade.has_refund,
        has_memo = merge_trade.has_memo,
        sys_status = merge_trade.sys_status,
    )
    #保存商城或C店订单到抽象全局抽象订单表
    for order in trade.trade_orders.all():
        merge_order,state = MergeOrder.objects.get_or_create(oid=order.oid,tid=trade.id)
        if state:
            MergeOrder.objects.filter(id=merge_order.id).update(
                tid = trade.id,
                merge_trade = merge_trade,
                num_iid = order.num_iid,
                title  = order.title,
                price  = order.price,
                sku_id = order.sku_id,
                num = order.num,
                outer_id = order.outer_id,
                outer_sku_id = order.outer_sku_id,
                total_fee = order.total_fee,
                payment = order.payment,
                sku_properties_name = order.sku_properties_name,
                refund_status = order.refund_status,
                pic_path = order.pic_path,
                seller_nick = order.seller_nick,
                buyer_nick  = order.buyer_nick,
                year  = order.year,
                month = order.month,
                week  = order.week,
                day   = order.day,
                hour  = order.hour,
                created  = order.created,
                pay_time = order.pay_time,
                consign_time = order.consign_time,
                status   = order.status,
                sys_status = IN_EFFECT
            )
        else:
            MergeOrder.objects.filter(id=merge_order.id).update(
                refund_status = order.refund_status,
                payment = order.payment,
                pay_time = order.pay_time,
                consign_time = order.consign_time,
                status   = order.status
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
        merge_trade.save()
    merge_trade.status = trade.status
    
    dt = trade.created
    merge_trade.year  = dt.year
    merge_trade.hour  = dt.hour
    merge_trade.month = dt.month
    merge_trade.day   = dt.day
    merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1

    trade_from = FENXIAO_TYPE
    trade_download_controller(merge_trade,trade,trade_from,is_first_save)
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
        consign_time = trade.consign_time,
        status = merge_trade.status,
        year  = merge_trade.year,
        hour  = merge_trade.hour,
        month = merge_trade.month,
        day   = merge_trade.day,
        week  = merge_trade.week,
        has_refund = merge_trade.has_refund,
        total_num = merge_trade.total_num,
        has_memo = merge_trade.has_memo,
        sys_status = merge_trade.sys_status,
    )
    #保存分销订单到抽象全局抽象订单表
    for order in trade.sub_purchase_orders.all():
        merge_order,state = MergeOrder.objects.get_or_create(oid=order.tc_order_id,tid=trade.id)
        fenxiao_product = FenxiaoProduct.get_or_create(trade.user.visitor_id,order.pid)
        if order.status == TRADE_REFUNDING:
            refund_status = REFUND_WAIT_SELLER_AGREE
        elif order.status == TRADE_REFUNDED:
            refund_status = REFUND_SUCCESS
        elif refund_status != TRADE_CLOSED:
            refund_status = NO_REFUND
        if state:    
            MergeOrder.objects.filter(id=merge_order.id).update(
                tid = trade.id,
                merge_trade = merge_trade,
                num_iid = fenxiao_product.item_id,
                title  = order.title,
                price  = order.price,
                sku_id = order.sku_id,
                num    = order.num,
                outer_id = order.item_outer_id,
                outer_sku_id = order.sku_outer_id,
                total_fee = order.total_fee,
                payment = order.distributor_payment,
                sku_properties_name = order.properties_values,
                refund_status = refund_status,
                pic_path = fenxiao_product.pictures and fenxiao_product.pictures.split(',')[0] or '',
                seller_nick = merge_trade.seller_nick,
                buyer_nick  = merge_trade.buyer_nick,
                year  = merge_trade.year,
                month = merge_trade.month,
                week  = merge_trade.week,
                day   = merge_trade.day,
                hour  = merge_trade.hour,
                created  = order.created,
                pay_time = merge_trade.created,
                consign_time = merge_trade.consign_time,
                status   = order.status,
                sys_status = IN_EFFECT
            )
        else:
            MergeOrder.objects.filter(id=merge_order.id).update(
                refund_status = refund_status,
                payment       = order.distributor_payment,
                consign_time  = merge_trade.consign_time,
                status        = order.status
            )

merge_trade_signal.connect(save_fenxiao_orders_to_mergetrade,sender=PurchaseOrder,dispatch_uid='merge_purchaseorder')


class ReplayPostTrade(models.Model):
    #重现发货表单
    operator   =  models.CharField(max_length=32,verbose_name='操作员')
    post_data  =  models.TextField(blank=True,verbose_name='发货清单数据')
    created    =  models.DateTimeField(null=True,auto_now=True,verbose_name='创建日期')
    
    class Meta:
        db_table = 'shop_trades_replayposttrade'
        verbose_name='已发货清单'.decode('utf8')
        
        