#-*- coding:utf8 -*-
import time
import json
import datetime
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from django.db.models import Sum
from shopback.orders.models import Trade,Order
from shopback.items.models import Item,Product,ProductSku
from shopback.logistics.models import Logistics,LogisticsCompany
from shopback.fenxiao.models import PurchaseOrder,SubPurchaseOrder,FenxiaoProduct
from shopback.refunds.models import Refund,REFUND_STATUS
from auth.utils import parse_datetime
from shopback import paramconfig as pcfg
from shopback.monitor.models import SystemConfig,Reason
from shopback.signals import merge_trade_signal,rule_signal
import logging

logger = logging.getLogger('trades.handler')


SYS_TRADE_STATUS = (
    (pcfg.WAIT_AUDIT_STATUS,'问题单'),
    (pcfg.WAIT_PREPARE_SEND_STATUS,'待发货准备'),
    (pcfg.WAIT_CHECK_BARCODE_STATUS,'待扫描验货'),
    (pcfg.WAIT_SCAN_WEIGHT_STATUS,'待扫描称重'),
    (pcfg.FINISHED_STATUS,'已发货'),
    (pcfg.INVALID_STATUS,'已作废'),
    (pcfg.ON_THE_FLY_STATUS,'飞行模式'),
    (pcfg.REGULAR_REMAIN_STATUS,'定时提醒')
)

OUT_STOCK_KEYWORD = [u'到',u'到货',u'预售']

SYS_ORDER_STATUS = (
    (pcfg.IN_EFFECT ,'有效'),
    (pcfg.INVALID_STATUS,'无效'),
)

TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY,'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY,'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED,'交易成功'),
    (pcfg.TRADE_CLOSED,'退款成功交易自动关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,'付款前关闭交易'),
)

TAOBAO_ORDER_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY,'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY,'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED,'交易成功'),
    (pcfg.TRADE_CLOSED,'退款成功，交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,'付款以前关闭交易'),
    (pcfg.WAIT_CONFIRM_WAIT_SEND_GOODS,"付款信息待确认，待发货"),
    (pcfg.WAIT_CONFIRM_SEND_GOODS,"付款信息待确认，已发货"),
    (pcfg.WAIT_CONFIRM_GOODS_CONFIRM,"付款信息待确认，已收货"),
    (pcfg.CONFIRM_WAIT_SEND_GOODS,"付款信息已确认，待发货"),
    (pcfg.CONFIRM_SEND_GOODS,"付款信息已确认，已发货"),
    (pcfg.TRADE_REFUNDED,"已退款"),
    (pcfg.TRADE_REFUNDING,"退款中"),
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

PRIORITY_TYPE = (
    (-1,'低'),
    (0,'中'),
    (1,'高'),
)

GIFT_TYPE = (
    (pcfg.REAL_ORDER_GIT_TYPE,'实付订单'),
    (pcfg.CS_PERMI_GIT_TYPE,'客服赠送'),
    (pcfg.OVER_PAYMENT_GIT_TYPE,'满就送'),
    (pcfg.COMBOSE_SPLIT_GIT_TYPE,'组合拆分'),
)

class MergeTrade(models.Model):
    
    id    = BigIntegerAutoField(primary_key=True)
    tid   = models.BigIntegerField(unique=True,null=True,verbose_name='淘宝订单编号')
    
    user       = models.ForeignKey(User,null=True,related_name='merge_trades',verbose_name='所属店铺')
    seller_id  = models.CharField(max_length=64,blank=True,verbose_name='店铺ID')
    seller_nick = models.CharField(max_length=64,blank=True,verbose_name='店铺名称')
    buyer_nick  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='买家昵称')
    
    type       = models.CharField(max_length=32,choices=TRADE_TYPE,blank=True,verbose_name='订单类型')
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
    post_cost     = models.CharField(max_length=10,blank=True,verbose_name='物流成本')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name='买家留言')
    seller_memo = models.TextField(max_length=1000,blank=True,verbose_name='卖家备注')
    sys_memo    = models.TextField(max_length=500,blank=True,verbose_name='系统备注')
    seller_flag    = models.IntegerField(null=True,verbose_name='淘宝旗帜')
    
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
    
    reason_code = models.CharField(max_length=100,blank=True,verbose_name='问题编号')  #1|2|3 问题单原因编码集合
    status  = models.CharField(max_length=32,db_index=True,choices=TAOBAO_TRADE_STATUS,blank=True,verbose_name='淘宝订单状态')
        
    is_picking_print = models.BooleanField(default=False,verbose_name='打印发货单')
    is_express_print = models.BooleanField(default=False,verbose_name='打印物流单')
    is_send_sms      = models.BooleanField(default=False,verbose_name='短信提醒')
    has_refund       = models.BooleanField(default=False,verbose_name='待退款')
    has_out_stock    = models.BooleanField(default=False,verbose_name='缺货')
    has_rule_match   = models.BooleanField(default=False,verbose_name='有匹配')
    has_memo         = models.BooleanField(default=False,verbose_name='有留言')
    has_merge        = models.BooleanField(default=False,verbose_name='有合单')
    remind_time      = models.DateTimeField(null=True,blank=True,verbose_name='提醒日期')
    refund_num       = models.IntegerField(null=True,default=0,verbose_name='退款单数')  #退款单数
    
    priority       = models.IntegerField(db_index=True,default=0,choices=PRIORITY_TYPE,verbose_name='优先级')
    operator       =  models.CharField(max_length=32,blank=True,verbose_name='发货员')
    sys_status     = models.CharField(max_length=32,db_index=True,choices=SYS_TRADE_STATUS,blank=True,default='',verbose_name='系统状态')
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
        verbose_name=u'订单'
        permissions = (
             ("can_trade_modify", "能否修改订单状态"),
             ("can_trade_aduit", "能否审核订单信息"),
        )

    def __unicode__(self):
        return str(self.id)
    
    @property
    def inuse_orders(self):
        return self.merge_trade_orders.filter(status=pcfg.WAIT_SELLER_SEND_GOODS,sys_status=pcfg.IN_EFFECT)\
                .exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
        
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
        orders = self.merge_trade_orders.filter(refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
        if orders.count()>0:
            return True
        return False
   
    
    @classmethod
    def judge_out_stock(cls,trade_id,trade_from):
        #判断是否有缺货
        is_out_stock = False
        try:
            trade = MergeTrade.objects.get(tid=trade_id)
        except Trade.DoesNotExist:
            logger.error('trade(tid:%d) does not exist'%trade_id)
        else:
            orders = trade.merge_trade_orders.exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
            for order in orders:
                is_order_out = False
                if order.outer_sku_id:
                    try:
                        product_sku = ProductSku.objects.get(prod_outer_id=order.outer_id,outer_id=order.outer_sku_id)    
                    except:
                        pass
                    else:
                        is_order_out  |= product_sku.out_stock or product_sku.quantity <= 0
  
                elif order.outer_id:
                    try:
                        product = Product.objects.get(outer_id=order.outer_id)
                    except:
                        pass
                    else:
                        is_order_out |= product.out_stock or product.collect_num <= 0
                
                if not is_order_out:
                    #预售关键字匹配        
                    for kw in OUT_STOCK_KEYWORD:
                        try:
                            order.sku_properties_name.index(kw)
                        except:
                            pass
                        else:
                            is_order_out = True
                            break
                
                if is_order_out:
                     MergeOrder.objects.filter(tid=trade_id,oid=order.oid).update(out_stock=True)
                is_out_stock |= is_order_out
                
        return is_out_stock
    
    @classmethod
    def judge_full_refund(cls,trade_id,trade_from):
        #更新订单实际商品和退款商品数量，返回退款状态

        merge_trade = cls.objects.get(tid=trade_id)  

        refund_approval_num = merge_trade.merge_trade_orders.filter(refund_status__in=pcfg.REFUND_APPROVAL_STATUS
                            ,gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()
        total_orders_num  = merge_trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()

        if refund_approval_num==total_orders_num:
            return True
        
        return False

    @classmethod
    def judge_new_refund(cls,trade_id,trade_from):
        #判断是否有新退款
        merge_trade = cls.objects.get(tid=trade_id)
        refund_orders_num   = merge_trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE)\
            .exclude(Q(is_merge=True)|Q(refund_status=pcfg.NO_REFUND)).count()
        
        if refund_orders_num >merge_trade.refund_num:
            return True
        
        return False
        
    @classmethod
    def judge_rule_match(cls,trade_id,trade_from):
        
        #系统设置是否进行规则匹配
        config  = SystemConfig.getconfig()
        if not config.is_rule_auto:
            return False
        if trade_from == pcfg.FENXIAO_TYPE:
            return True
        try:
            rule_signal.send(sender='product_rule',trade_tid=trade_id)
        except Exception,exc:
            return True
        return False
    
    @classmethod
    def judge_need_merge(cls,trade_id,buyer_nick,trade_from,full_address):
        #是否需要合单      
        trades = cls.objects.filter(buyer_nick=buyer_nick,sys_status__in=(pcfg.WAIT_PREPARE_SEND_STATUS,
                pcfg.WAIT_AUDIT_STATUS,pcfg.REGULAR_REMAIN_STATUS)).exclude(tid=trade_id)
        is_need_merge = False
        if trade_from == pcfg.TAOBAO_TYPE:
            if trades.count() > 0:
                for trade in trades:
                    trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                is_need_merge = True
        else:
            for trade in trades:
                if trade.full_address == full_address:
                    trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                    is_need_merge = True
        return is_need_merge

    @classmethod
    def judge_need_pull(cls,trade_id,modified):
        #judge is need to pull trade from taobao
        need_pull = False
        try:
            obj = cls.objects.get(tid=trade_id)
        except:
            need_pull = True
        else:
            if not obj.modified or obj.modified < modified:
                need_pull = True
        return need_pull
 
   
class MergeOrder(models.Model):
    
    id    = BigIntegerAutoField(primary_key=True)
    
    oid   = models.BigIntegerField(db_index=True,null=True,blank=True,verbose_name='子订单编号')
    tid   = models.BigIntegerField(db_index=True,null=True,verbose_name='订单编号')
    
    cid    = models.BigIntegerField(db_index=True,null=True,verbose_name='商品分类')
    merge_trade = BigIntegerForeignKey(MergeTrade,null=True,related_name='merge_trade_orders',verbose_name='所属订单')

    num_iid  = models.CharField(max_length=64,blank=True,verbose_name='线上商品编号')
    title  =  models.CharField(max_length=128,verbose_name='商品标题')
    price  = models.CharField(max_length=12,blank=True,verbose_name='单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name='属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name='商品数量')
    
    outer_id = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='商品外部编码')
    outer_sku_id = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='规格外部编码')
    
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
    
    created       =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='创建日期')
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='付款日期')
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='发货日期')
    
    out_stock   = models.BooleanField(default=False,verbose_name='缺货')
    is_merge    = models.BooleanField(default=False,verbose_name='合并') 
    is_rule_match   = models.BooleanField(default=False,verbose_name='匹配')
    gift_type   = models.IntegerField(choices=GIFT_TYPE,default=0,verbose_name='赠品类型')
    
    status = models.CharField(max_length=32,choices=TAOBAO_ORDER_STATUS,blank=True,verbose_name='淘宝订单状态')
    sys_status = models.CharField(max_length=32,choices=SYS_ORDER_STATUS,blank=True,default='',verbose_name='系统订单状态')
    
    class Meta:
        db_table = 'shop_trades_mergeorder'
        unique_together = ("oid","tid")
        verbose_name=u'子订单'
    
    @classmethod
    def gen_new_order(cls,trade_id,outer_id,outer_sku_id,num,gift_type=pcfg.REAL_ORDER_GIT_TYPE):
        
        merge_trade,state = MergeTrade.objects.get_or_create(id=trade_id)
        product = Product.objects.get(outer_id=outer_id)
        sku_properties_name = ''
        if outer_sku_id:
            try:
                productsku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
                sku_properties_name = productsku.properties_name
            except Exception,exc:
                 logger.error(exc.message,exc_info=True)
                 sku_properties_name = u'该规格编码没有入库'
        merge_order = MergeOrder.objects.create(
            tid = merge_trade.tid,
            merge_trade = merge_trade,
            outer_id = outer_id,
            price = product.price,
            payment = '0',
            num = num,
            title = product.name,
            outer_sku_id = outer_sku_id,
            sku_properties_name = sku_properties_name,
            refund_status = pcfg.NO_REFUND,
            seller_nick = merge_trade.seller_nick,
            buyer_nick = merge_trade.buyer_nick,
            year = merge_trade.year,
            month = merge_trade.month,
            week  = merge_trade.week,
            day   = merge_trade.day,
            hour  = merge_trade.hour,
            created = merge_trade.created,
            pay_time = merge_trade.pay_time,
            consign_time = merge_trade.consign_time,
            gift_type = gift_type,
            status = pcfg.WAIT_SELLER_SEND_GOODS,
            sys_status = pcfg.IN_EFFECT
            )
        return merge_order


def refresh_trade_status(sender,instance,*args,**kwargs):
    #更新主订单的状态
    if not instance.seller_nick or instance.buyer_nick:
        instance.seller_nick = merge_trade.seller_nick
        instance.buyer_nick  = merge_trade.buyer_nick
        instance.created     = merge_trade.created
        instance.pay_time    = merge_trade.pay_time
        instance.save()
        return 
    merge_trade   = instance.merge_trade
    has_refunding = merge_trade.has_trade_refunding()
    out_stock     = merge_trade.merge_trade_orders.filter(out_stock=True,status=pcfg.WAIT_SELLER_SEND_GOODS).count()>0
    has_merge     = merge_trade.merge_trade_orders.filter(is_merge=True).count()>0
    has_rule_match = merge_trade.merge_trade_orders.filter(is_rule_match=True)
    
    merge_trade.has_refund = has_refunding
    merge_trade.has_out_stock = out_stock
    merge_trade.has_merge = has_merge
    merge_trade.has_rule_match = has_rule_match

    merge_trade.save()
        
post_save.connect(refresh_trade_status, sender=MergeOrder)

class MergeBuyerTrade(models.Model):
    
    sub_tid    =  models.BigIntegerField(primary_key=True)
    main_tid   =  models.BigIntegerField(db_index=True)
    created    =  models.DateTimeField(null=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_trades_mergebuyertrade'
        verbose_name='合单记录'.decode('utf8')
        
    def __unicode__(self):
        return '<%d,%d>'%(sub_tid,main_tid)
    
    @classmethod
    def get_merge_type(cls,tid):
        """
        0,no merge,
        1,sub merge trade,
        2,main merge trade
        """
        try:
            cls.objects.get(sub_tid=tid)
        except cls.DoesNotExist:
            merges = cls.objects.filter(main_tid=tid)
            if merges.count()>0:
                return 2
            return 0
        return 1

def merge_order_maker(sub_tid,main_tid):
    #合单操作
    sub_trade      = MergeTrade.objects.get(tid=sub_tid)
    main_merge_trade = MergeTrade.objects.get(tid=main_tid)
    
    main_merge_trade.merge_trade_orders.filter(oid=None).delete()
    main_merge_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    orders = sub_trade.merge_trade_orders.exclude(oid=None)
    merge_order = MergeOrder()
    
    total_num    = 0
    payment      = 0
    total_fee    = 0
    discount_fee = 0
    for order in orders:
        for field in order._meta.fields:
            hasattr(merge_order,field.name) and setattr(merge_order,field.name,getattr(order,field.name))
        merge_order.id  = None
        merge_order.merge_trade = main_merge_trade
        merge_order.tid = main_tid
        merge_order.is_merge = True
        merge_order.sys_status = pcfg.IN_EFFECT
        merge_order.save()
        if order.refund_status not in pcfg.REFUND_APPROVAL_STATUS :
            total_num += order.num
            payment   += float(order.payment )
            total_fee += float(order.total_fee )
            discount_fee += float(order.discount_fee or 0)
    
    if sub_trade.buyer_message:
        main_merge_trade.update_buyer_message(sub_tid,sub_trade.buyer_message)
    if sub_trade.seller_memo:
        main_merge_trade.update_seller_memo(sub_tid,sub_trade.seller_memo)
    MergeTrade.objects.filter(tid=main_tid).update(has_merge = True,
                                                   total_num = total_num + main_merge_trade.total_num,
                                                   payment   = payment + float(main_merge_trade.payment ),
                                                   total_fee = total_fee + float(main_merge_trade.total_fee ),
                                                   discount_fee = discount_fee + float(main_merge_trade.discount_fee or 0))
    
    MergeBuyerTrade.objects.get_or_create(sub_tid=sub_tid,main_tid=main_tid)
    MergeTrade.objects.filter(tid=main_tid,out_sid='',status=pcfg.WAIT_SELLER_SEND_GOODS).update(sys_status=pcfg.WAIT_AUDIT_STATUS) 
    MergeTrade.objects.get(tid=sub_tid).append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    
    return True


def merge_order_remover(main_tid):
    #拆单操作
    main_trade = MergeTrade.objects.get(tid=main_tid)
    main_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    main_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE) 
    main_trade.has_merge = False
    main_trade.save()
    
    main_trade.merge_trade_orders.filter(Q(oid=None)|Q(is_merge=True)).delete()
    
    sub_merges = MergeBuyerTrade.objects.filter(main_tid=main_tid)
    for sub_merge in sub_merges:   
        sub_tid  = sub_merge.sub_tid
        sub_merge_trade = MergeTrade.objects.get(tid=sub_tid)
        sub_merge_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
        sub_merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        MergeTrade.objects.filter(tid=sub_merge_trade.tid,sys_status=pcfg.ON_THE_FLY_STATUS).update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        
    MergeBuyerTrade.objects.filter(main_tid=main_tid).delete()
    

def trade_download_controller(merge_trade,trade,trade_from,first_pay_load):
    
    shipping_type = trade.shipping if hasattr(trade,'shipping') else trade.shipping_type
    seller_memo   = trade.memo  if hasattr(trade,'memo') else trade.seller_memo
    buyer_message = trade.buyer_message if hasattr(trade,'buyer_message') else trade.supplier_memo   
 
    merge_trade.has_memo = seller_memo or buyer_message
    merge_trade.buyer_message = buyer_message 
    merge_trade.seller_memo   = seller_memo
    
    if trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
        #新留言
        if merge_trade.has_memo:
            merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)

        #退款中
        wait_refunding = merge_trade.has_trade_refunding()
        if wait_refunding:
            merge_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)
        #设置订单是否有待退款属性    
        merge_trade.has_refund = wait_refunding
        
        has_full_refund = MergeTrade.judge_full_refund(trade.id, trade_from)
        has_new_refund  = MergeTrade.judge_new_refund(trade.id, trade_from)

        #如果首次付款后入库
        if first_pay_load:  
            #缺货 
            out_stock      =  MergeTrade.judge_out_stock(trade.id, trade_from)
            if out_stock:
                merge_trade.append_reason_code(pcfg.OUT_GOOD_CODE)
            #设置订单是否有缺货属性    
            merge_trade.has_out_stock = out_stock
            
            #规则匹配
            is_rule_match  =  MergeTrade.judge_rule_match(trade.id, trade_from)    
            if is_rule_match: 
                merge_trade.append_reason_code(pcfg.RULE_MATCH_CODE)
            #设置订单是否有缺货属性    
            merge_trade.has_rule_match = is_rule_match
    
            full_address = merge_trade.user_full_address
            #订单合并   
            is_merge_success = False #是否合并成功
            is_need_merge    = False #是否有合并的可能
            main_tid = None  #主订单ID
            if not has_full_refund  and trade_from == pcfg.TAOBAO_TYPE:
                is_need_merge = MergeTrade.judge_need_merge(trade.id,trade.buyer_nick,trade_from,full_address)
                if is_need_merge :
                    merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                    trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick,sys_status__in=
                                                (pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS,pcfg.REGULAR_REMAIN_STATUS))\
                                                .exclude(tid=trade.id).order_by('-pay_time')
                                                
                    merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[t.tid for t in trades])
                    #如果有已有合并记录，则将现有主订单作为合并主订单
                    if merge_buyer_trades.count()>0:
                        main_merge_tid = merge_buyer_trades[0].main_tid
                        main_trade = MergeTrade.objects.get(tid=main_merge_tid)
                        if main_trade.user_full_address == full_address:
                            main_tid = main_merge_tid
                    #如果入库订单不缺货,没有待退款，则进行合单操作
                    if trades.count()>0 and not out_stock and not wait_refunding:
                        #如果没有则将按时间排序的第一符合条件的订单作为主订单
                        can_merge = True
                        if not main_tid:
                            for t in trades:
                                full_refund = MergeTrade.judge_full_refund(t.tid,t.type)
                                if not main_tid and not full_refund and not t.has_out_stock and not t.has_refund and t.user_full_address == full_address:
                                    main_tid = t.tid
                                if t.has_out_stock or t.has_refund:
                                    can_merge = False
                                    break
                                    
                        if main_tid and can_merge:  
                            #进行合单
                            is_merge_success = merge_order_maker(trade.id,main_tid)
   
                    #如果入库订单缺货,待退款，则将同名的单置放入待审核区域
                    elif trades.count()>0 and out_stock or wait_refunding:
                        if main_tid :
                            merge_order_remover(main_tid)
                        for t in trades:
                            if t.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
                                MergeTrade.objects.filter(id=t.id,out_sid='').update(sys_status=pcfg.WAIT_AUDIT_STATUS)
                            else:
                                MergeTrade.objects.filter(id=t.id).update(sys_status=pcfg.WAIT_AUDIT_STATUS,has_merge=False)
                    
            #如果合单成功则将新单置为飞行模式                 
            if is_merge_success:
                merge_trade.sys_status = pcfg.ON_THE_FLY_STATUS
            #有问题则进入问题单域
            elif merge_trade.has_memo or wait_refunding or out_stock or is_rule_match or is_need_merge:
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
            else:
                merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                #进入待发货区域，需要进行商品规则匹配
                rule_signal.send(sender='merge_trade_rule',trade_tid=trade.id)
            
            #更新物流公司信息    
            if is_need_merge and main_tid:
                main_trade = MergeTrade.objects.get(tid=main_tid)
                merge_trade.logistics_company = main_trade.logistics_company
            elif shipping_type in ('free','express','FAST','SELLER'):
                receiver_state = merge_trade.receiver_state
                default_company = LogisticsCompany.get_recommend_express(receiver_state)
                merge_trade.logistics_company = default_company
            elif shipping_type in ('post','ems'):
                post_company = LogisticsCompany.objects.get(code=shipping_type.upper())
                merge_trade.logistics_company = post_company
        #非付款后首次入库
        else:
            #再次入库，现在只针对非担保交易的分销订单
            if has_new_refund:
                merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)

                merge_type  = MergeBuyerTrade.get_merge_type(trade.id)
                if merge_type == 0:    
                    MergeTrade.objects.filter(tid=trade.id,out_sid='').update(sys_status=pcfg.WAIT_AUDIT_STATUS,has_refund=True)
                elif merge_type == 1:
                    main_tid = MergeBuyerTrade.objects.get(sub_tid=trade.id).main_tid
                    merge_order_remover(main_tid)
                else:
                    merge_order_remover(notify.tid)
            
            if merge_trade.reason_code and merge_trade.out_sid == '' and merge_trade.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
     
    elif trade.status==pcfg.WAIT_BUYER_CONFIRM_GOODS:
        if merge_trade.sys_status in pcfg.WAIT_DELIVERY_STATUS:
            merge_trade.sys_status = pcfg.INVALID_STATUS
    #如果淘宝订单状态已改变，而系统内部状态非最终状态，则将订单作废        
    elif merge_trade.sys_status:
        if merge_trade.sys_status not in (pcfg.FINISHED_STATUS,pcfg.INVALID_STATUS):
            merge_trade.sys_status = pcfg.INVALID_STATUS  
            merge_trade.append_reason_code(pcfg.INVALID_END_CODE)
    #更新系统订单状态
    MergeTrade.objects.filter(tid=trade.id).update(
            buyer_message = merge_trade.buyer_message,
            seller_memo   = merge_trade.seller_memo,
            logistics_company = merge_trade.logistics_company,
            has_refund = merge_trade.has_refund,
            has_memo = merge_trade.has_memo,
            has_out_stock = merge_trade.has_out_stock,
            has_rule_match = merge_trade.has_rule_match,
            sys_status = merge_trade.sys_status,
    )
    
     
def save_orders_trade_to_mergetrade(sender, tid, *args, **kwargs):
    
    try:
        trade = Trade.objects.get(id=tid)
        merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
        
        first_pay_load = not merge_trade.sys_status 
        if first_pay_load:
            #保存地址
            merge_trade.receiver_name = trade.receiver_name 
            merge_trade.receiver_state   = trade.receiver_state 
            merge_trade.receiver_city = trade.receiver_city 
            merge_trade.receiver_district = trade.receiver_district 
            merge_trade.receiver_address = trade.receiver_address 
            merge_trade.receiver_zip  = trade.receiver_zip 
            merge_trade.receiver_mobile  = trade.receiver_mobile 
            merge_trade.receiver_phone = trade.receiver_phone 
            merge_trade.save()
      
        #保存商城或C店订单到抽象全局抽象订单表
        for order in trade.trade_orders.all():
            merge_order,state = MergeOrder.objects.get_or_create(oid=order.oid,tid=trade.id,merge_trade = merge_trade,)
            if state:
                MergeOrder.objects.filter(id=merge_order.id).update(
                    tid = trade.id,
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
                    created  = order.created,
                    pay_time = order.pay_time,
                    consign_time = order.consign_time,
                    status   = order.status,
                    sys_status = pcfg.IN_EFFECT
                    )
            else:
                MergeOrder.objects.filter(id=merge_order.id).update(
                    refund_status = order.refund_status,
                    payment = order.payment,
                    pay_time = order.pay_time,
                    consign_time = order.consign_time,
                    status   = order.status
                    )
        #保存基本订单信息
        merge_trade.status = trade.status
        dt = trade.created
        merge_trade.year  = dt.year
        merge_trade.hour  = dt.hour
        merge_trade.month = dt.month
        merge_trade.day   = dt.day
        merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1 
        trade_from = pcfg.FENXIAO_TYPE if trade.type==pcfg.FENXIAO_TYPE else pcfg.TAOBAO_TYPE   
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
            buyer_message = trade.buyer_message,
            seller_memo   = trade.seller_memo,
            seller_flag   = trade.seller_flag,
            created = trade.created,
            pay_time = trade.pay_time,
            modified = trade.modified,
            consign_time = trade.consign_time,
            status = merge_trade.status,
        )
        #设置系统内部状态信息
        trade_download_controller(merge_trade,trade,trade_from,first_pay_load) 
  
    except Exception,exc:
        logger.error(exc.message,exc_info=True)

merge_trade_signal.connect(save_orders_trade_to_mergetrade,sender=Trade,dispatch_uid='merge_trade')        


def save_fenxiao_orders_to_mergetrade(sender, tid, *args, **kwargs):
    try:
        if not tid:
            return 
        trade = PurchaseOrder.objects.get(id=tid)
        merge_trade,state = MergeTrade.objects.get_or_create(tid=trade.id)
        
        first_pay_load = not merge_trade.sys_status 
        if first_pay_load :
            logistics = Logistics.get_or_create(trade.seller_id,trade.id)
            location = json.loads(logistics.location or 'null')
        
            merge_trade.receiver_name = logistics.receiver_name 
            merge_trade.receiver_zip  = (location.get('zip','') if location else '') 
            merge_trade.receiver_mobile = logistics.receiver_mobile 
            merge_trade.receiver_phone = logistics.receiver_phone 

            merge_trade.receiver_state = (location.get('state','') if location else '') 
            merge_trade.receiver_city  = (location.get('city','') if location else '') 
            merge_trade.receiver_district = (location.get('district','') if location else '') 
            merge_trade.receiver_address  = (location.get('address','') if location else '') 
            merge_trade.save()

        #保存分销订单到抽象全局抽象订单表
        for order in trade.sub_purchase_orders.all():
            merge_order,state = MergeOrder.objects.get_or_create(oid=order.tc_order_id,tid=trade.id,merge_trade = merge_trade)
            fenxiao_product = FenxiaoProduct.get_or_create(trade.user.visitor_id,order.item_id)
            if order.status == pcfg.TRADE_REFUNDING:
                refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
            elif order.status == pcfg.TRADE_REFUNDED:
                refund_status = pcfg.REFUND_SUCCESS
            else:
                refund_status = pcfg.NO_REFUND
            if state:    
                MergeOrder.objects.filter(id=merge_order.id).update(
                    tid = trade.id,
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
                    created  = order.created,
                    pay_time = merge_trade.created,
                    consign_time = merge_trade.consign_time,
                    status   = pcfg.FENXIAO_TAOBAO_STATUS_MAP.get(order.status,order.status),
                    sys_status = pcfg.IN_EFFECT
                )
            else:
                MergeOrder.objects.filter(id=merge_order.id).update(
                    refund_status = refund_status,
                    payment       = order.distributor_payment,
                    consign_time  = merge_trade.consign_time,
                    status        = order.status
                )

        merge_trade.status = trade.status 
        dt = trade.created
        merge_trade.year  = dt.year
        merge_trade.hour  = dt.hour
        merge_trade.month = dt.month
        merge_trade.day   = dt.day
        merge_trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1
        
        trade_from = pcfg.FENXIAO_TYPE
        MergeTrade.objects.filter(tid=trade.id).update(
            user = trade.user,
            seller_id = trade.seller_id,
            seller_nick = trade.supplier_username,
            buyer_nick = trade.distributor_username,
            type = pcfg.FENXIAO_TYPE,
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
            seller_flag  = trade.supplier_flag,
            status = merge_trade.status,
        )
        #更新系统内部状态
        trade_download_controller(merge_trade,trade,trade_from,first_pay_load)
        
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
    
merge_trade_signal.connect(save_fenxiao_orders_to_mergetrade,sender=PurchaseOrder,dispatch_uid='merge_purchaseorder')


class ReplayPostTrade(models.Model):
    #重现发货表单
    operator   =  models.CharField(max_length=32,verbose_name='操作员')
    post_data  =  models.TextField(blank=True,verbose_name='发货清单数据')
    created    =  models.DateTimeField(null=True,auto_now=True,verbose_name='创建日期')
    
    class Meta:
        db_table = 'shop_trades_replayposttrade'
        verbose_name='已发货清单'.decode('utf8')

        
        
