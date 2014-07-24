#-*- coding:utf8 -*-
import time
import json
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from bitfield import BitField
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.base import log_action, CHANGE
from shopback.orders.models import Trade,Order,STEP_TRADE_STATUS
from shopback.trades.managers import MergeTradeManager
from shopback.items.models import Item,Product,ProductSku
from shopback.logistics.models import Logistics,LogisticsCompany,DestCompany
from shopback.fenxiao.models import PurchaseOrder,SubPurchaseOrder,FenxiaoProduct
from shopback.refunds.models import Refund,REFUND_STATUS
from shopback import paramconfig as pcfg
from shopback.monitor.models import SystemConfig,Reason
from shopback.signals import merge_trade_signal,rule_signal,recalc_fee_signal
from auth import apis
from common.utils import (parse_datetime ,
                          get_yesterday_interval_time ,
                          update_model_fields)
import logging

logger = logging.getLogger('django.request')

SYS_TRADE_STATUS = (
    (pcfg.WAIT_AUDIT_STATUS,u'问题单'),
    (pcfg.WAIT_PREPARE_SEND_STATUS,u'待发货准备'),
    (pcfg.WAIT_CHECK_BARCODE_STATUS,u'待扫描验货'),
    (pcfg.WAIT_SCAN_WEIGHT_STATUS,u'待扫描称重'),
    (pcfg.FINISHED_STATUS,u'已完成'),
    (pcfg.INVALID_STATUS,u'已作废'),
    (pcfg.ON_THE_FLY_STATUS,u'飞行模式'),
    (pcfg.REGULAR_REMAIN_STATUS,u'定时提醒'),
)

SYS_ORDER_STATUS = (
    (pcfg.IN_EFFECT ,u'有效'),
    (pcfg.INVALID_STATUS,u'无效'),
)

TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY,u'订单创建'),
    (pcfg.WAIT_BUYER_PAY,u'待付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,u'待发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,u'待确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,u'货到付款签收'),
    (pcfg.TRADE_FINISHED,u'交易成功'),
    (pcfg.TRADE_CLOSED,u'退款交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,u'未付款关闭'),
)

TAOBAO_ORDER_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY,u'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY,u'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,u'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,u'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,u'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED,u'交易成功'),
    (pcfg.TRADE_CLOSED,u'退款成功，交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,u'付款以前关闭交易'),
    (pcfg.WAIT_CONFIRM_WAIT_SEND_GOODS,u"付款信息待确认，待发货"),
    (pcfg.WAIT_CONFIRM_SEND_GOODS,u"付款信息待确认，已发货"),
    (pcfg.WAIT_CONFIRM_GOODS_CONFIRM,u"付款信息待确认，已收货"),
    (pcfg.CONFIRM_WAIT_SEND_GOODS,u"付款信息已确认，待发货"),
    (pcfg.CONFIRM_SEND_GOODS,u"付款信息已确认，已发货"),
    (pcfg.TRADE_REFUNDED,u"已退款"),
    (pcfg.TRADE_REFUNDING,u"退款中"),
)

TRADE_TYPE = (
    (pcfg.TAOBAO_TYPE,u'淘宝&商城'),
    (pcfg.FENXIAO_TYPE,u'淘宝分销'),
    (pcfg.JD_TYPE,u'京东'),
    (pcfg.YHD_TYPE,u'一号店'),
    (pcfg.DD_TYPE,u'当当'),
    (pcfg.WX_TYPE,u'微信小店'),
    (pcfg.AMZ_TYPE,u'亚马逊'),
    (pcfg.DIRECT_TYPE,u'内售'),
    (pcfg.REISSUE_TYPE,u'补发'),
    (pcfg.EXCHANGE_TYPE,u'退换货'),
)

COD_STATUS = (
    (pcfg.COD_NEW_CREATED,u'初始状态'),
    (pcfg.COD_ACCEPTED_BY_COMPANY,u'接单成功'),
    (pcfg.COD_REJECTED_BY_COMPANY,u'接单失败'),
    (pcfg.COD_RECIEVE_TIMEOUT,u'接单超时'),
    (pcfg.COD_TAKEN_IN_SUCCESS,u'揽收成功'),
    (pcfg.COD_TAKEN_IN_FAILED,u'揽收失败'),
    (pcfg.COD_TAKEN_TIMEOUT,u'揽收超时'),
    (pcfg.COD_SIGN_IN,u'签收成功'),
    (pcfg.COD_REJECTED_BY_OTHER_SIDE,u'签收失败'),
    (pcfg.COD_WAITING_TO_BE_SENT,u'订单等待发送给物流公司'),
    (pcfg.COD_CANCELED,u'用户取消物流订单'),
)

SHIPPING_TYPE_CHOICE = (
    (pcfg.EXPRESS_SHIPPING_TYPE,u'快递'),
    (pcfg.POST_SHIPPING_TYPE,u'平邮'),
    (pcfg.EMS_SHIPPING_TYPE,u'EMS'),
    (pcfg.EXTRACT_SHIPPING_TYPE,u'无需物流'),
)

PRIORITY_TYPE = (
    (pcfg.PRIORITY_HIG,u'高'),
    (pcfg.PRIORITY_MID,u'中'),
    (pcfg.PRIORITY_LOW,u'低'),
)

GIFT_TYPE = (
    (pcfg.REAL_ORDER_GIT_TYPE  ,u'实付'),
    (pcfg.CS_PERMI_GIT_TYPE    ,u'赠送'),
    (pcfg.OVER_PAYMENT_GIT_TYPE,u'满就送'),
    (pcfg.COMBOSE_SPLIT_GIT_TYPE,u'拆分'),
    (pcfg.RETURN_GOODS_GIT_TYPE,u'退货'),
    (pcfg.CHANGE_GOODS_GIT_TYPE,u'换货')
)

class MergeTrade(models.Model):
    
    SYS_TRADE_STATUS = SYS_TRADE_STATUS
    TAOBAO_TRADE_STATUS = TAOBAO_TRADE_STATUS
    TRADE_TYPE       = TRADE_TYPE
    COD_STATUS       = COD_STATUS
    SHIPPING_TYPE_CHOICE = SHIPPING_TYPE_CHOICE
    PRIORITY_TYPE    = PRIORITY_TYPE
    
    id    = BigIntegerAutoField(primary_key=True,db_index=True,verbose_name=u'订单ID')
    
    tid   = models.CharField(max_length=32,
                             default=lambda:'HYD%d'%int(time.time()*10**5),
                             verbose_name=u'原单ID')  
    user       = models.ForeignKey(User,related_name='merge_trades',verbose_name=u'所属店铺')
    buyer_nick  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'买家昵称')
    
    type        = models.CharField(max_length=32,choices=TRADE_TYPE,
                                  blank=True,verbose_name=u'订单类型')
    shipping_type = models.CharField(max_length=12,blank=True,
                                     choices=SHIPPING_TYPE_CHOICE,verbose_name=u'物流方式')
    
    order_num  =   models.IntegerField(default=0,verbose_name=u'单数')
    prod_num   =   models.IntegerField(default=0,verbose_name=u'品类数')
    payment    =   models.FloatField(default=0.0,verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0,verbose_name=u'折扣')
    adjust_fee =   models.FloatField(default=0.0,verbose_name=u'调整费用')
    post_fee   =   models.FloatField(default=0.0,verbose_name=u'物流费用')
    total_fee  =   models.FloatField(default=0.0,verbose_name=u'总费用')
    
    is_cod         =   models.BooleanField(default=False,verbose_name=u'货到付款')
    seller_cod_fee = models.FloatField(default=0.0,verbose_name=u'COD卖家费用')
    buyer_cod_fee  = models.FloatField(default=0.0,verbose_name=u'COD买家费用')
    cod_fee        = models.FloatField(default=0.0,verbose_name=u'COD费用')
    cod_status     = models.CharField(max_length=32,blank=True,
                                      choices=COD_STATUS,verbose_name=u'COD状态')
    
    weight        = models.CharField(max_length=10,blank=True,verbose_name=u'包裹重量')
    post_cost     = models.FloatField(default=0.0,verbose_name=u'物流成本')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name=u'买家留言')
    seller_memo   = models.TextField(max_length=1000,blank=True,verbose_name=u'卖家备注')
    sys_memo      = models.TextField(max_length=1000,blank=True,verbose_name=u'系统备注')
    seller_flag   = models.IntegerField(null=True,verbose_name=u'淘宝旗帜')
    
    created      = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'生成日期')
    pay_time     = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    modified     = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'修改日期') 
    consign_time = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'发货日期')
    send_time    = models.DateTimeField(null=True,blank=True,verbose_name=u'预售日期')
    weight_time  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'称重日期')
    charge_time  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'揽件日期')
    
    is_brand_sale  = models.BooleanField(default=False,verbose_name=u'品牌特卖') 
    is_force_wlb   = models.BooleanField(default=False,verbose_name=u'物流宝') 
    trade_from     = BitField(flags=(pcfg.TF_WAP,
                                     pcfg.TF_HITAO,
                                     pcfg.TF_TOP,
                                     pcfg.TF_TAOBAO,
                                     pcfg.TF_JHS),verbose_name=u'交易来源')
    
    is_lgtype      = models.BooleanField(default=False,verbose_name=u'速递') 
    lg_aging       = models.DateTimeField(null=True,blank=True,verbose_name=u'速递送达时间')
    lg_aging_type  = models.CharField(max_length=20,blank=True,verbose_name=u'速递类型')
    
    buyer_rate     = models.BooleanField(default=False,verbose_name=u'买家已评')  
    seller_rate    = models.BooleanField(default=False,verbose_name=u'卖家已评')  
    seller_can_rate = models.BooleanField(default=False,verbose_name=u'卖家可评') 
    is_part_consign = models.BooleanField(default=False,verbose_name=u'分单发货')  
    
    out_sid         = models.CharField(max_length=64,db_index=True,
                                       blank=True,verbose_name=u'物流编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,
                                           blank=True,verbose_name=u'物流公司')
    receiver_name    =  models.CharField(max_length=25,db_index=True,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=24,db_index=True,
                                           blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,db_index=True,
                                           blank=True,verbose_name=u'电话')
    
    step_paid_fee      = models.CharField(max_length=10,blank=True,verbose_name=u'分阶付款金额')
    step_trade_status  = models.CharField(max_length=32,choices=STEP_TRADE_STATUS,
                                          blank=True,verbose_name=u'分阶付款状态')
    
    reason_code = models.CharField(max_length=100,blank=True,verbose_name=u'问题编号')  #1,2,3 问题单原因编码集合
    status      = models.CharField(max_length=32,db_index=True,choices=TAOBAO_TRADE_STATUS,
                                        blank=True,verbose_name=u'订单状态')
        
    is_picking_print = models.BooleanField(default=False,verbose_name=u'发货单')
    is_express_print = models.BooleanField(default=False,verbose_name=u'物流单')
    is_send_sms      = models.BooleanField(default=False,verbose_name=u'发货通知')
    has_refund       = models.BooleanField(default=False,verbose_name=u'待退款')
    has_out_stock    = models.BooleanField(default=False,verbose_name=u'缺货')
    has_rule_match   = models.BooleanField(default=False,verbose_name=u'有匹配')
    has_memo         = models.BooleanField(default=False,verbose_name=u'有留言')
    has_merge        = models.BooleanField(default=False,verbose_name=u'有合单')
    has_sys_err      = models.BooleanField(default=False,verbose_name=u'系统错误')
    remind_time      = models.DateTimeField(null=True,blank=True,verbose_name=u'提醒日期')
    refund_num       = models.IntegerField(null=True,default=0,verbose_name=u'退款单数')  #退款单数
    
    is_qrcode        = models.BooleanField(default=False,verbose_name=u'热敏订单')
    qrcode_msg       = models.CharField(max_length=32,blank=True,verbose_name=u'打印信息')
    
    can_review       = models.BooleanField(default=False,verbose_name=u'复审') 
    priority       =  models.IntegerField(db_index=True,default=0,
                                          choices=PRIORITY_TYPE,verbose_name=u'优先级')
    operator       =  models.CharField(max_length=32,blank=True,verbose_name=u'发货员')
    is_locked      =  models.BooleanField(default=False,verbose_name=u'锁定')
    is_charged     =  models.BooleanField(default=False,verbose_name=u'揽件')
    sys_status     =  models.CharField(max_length=32,db_index=True,
                                       choices=SYS_TRADE_STATUS,blank=True,
                                       default='',verbose_name=u'系统状态')
    
    reserveo       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义1')       
    reservet       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义2') 
    reserveh       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义3') 
    
    objects   = MergeTradeManager()
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
        unique_together = ("tid","user")
        verbose_name=u'订单'
        verbose_name_plural = u'订单列表'
        permissions = [
                       ("can_trade_modify", u"修改订单状态权限"),
                       ("can_trade_aduit", u"审核订单权限"),
                       ("sync_trade_post_taobao", u"同步淘宝发货权限"),
                       ("merge_order_action", u"合并订单权限"),
                       ("pull_order_action", u"重新下载订单权限"),
                       ("unlock_trade_action", u"订单解锁权限"),
                       ("export_finance_action",u"订单金额导出权限"),
                       ("export_logistic_action",u"物流信息导出权限"),
                       ("export_buyer_action",u"买家信息导出权限"),
                       ("export_yunda_action",u"韵达信息导出权限")
                       ]

    def __unicode__(self):
        return '<%s,%s>'%(str(self.id),self.buyer_nick)
    
    @property
    def total_num(self):
        """ 订单商品总数 """
        return self.inuse_orders.aggregate(total_num=Sum('num')).get('total_num') or 0
        
    @property
    def inuse_orders(self):
        return self.merge_orders.filter(sys_status=pcfg.IN_EFFECT)  
         
    @property
    def buyer_full_address(self):
        return '%s%s%s%s%s%s%s'%(self.receiver_name.strip(),
                                 self.receiver_mobile.strip(),
                                 self.receiver_phone.strip(),
                                 self.receiver_state.strip(),
                                 self.receiver_city.strip(),
                                 self.receiver_district.strip(),
                                 self.receiver_address.strip())
    
    @property
    def can_change_order(self):
        return self.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                   pcfg.WAIT_CHECK_BARCODE_STATUS,
                                   pcfg.WAIT_SCAN_WEIGHT_STATUS)
    
    @property
    def can_reverse_order(self):
        return self.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                   pcfg.WAIT_SCAN_WEIGHT_STATUS)
    
    def isPostScan(self):
        return self.status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                               pcfg.WAIT_SCAN_WEIGHT_STATUS)
    
    
    
    def update_inventory(self,update_returns=True,update_changes=True):
        #自提直接更新订单库存信息
        
        post_orders = self.inuse_orders     
        if not update_returns:
            post_orders.exclude(gift_type = pcfg.RETURN_GOODS_GIT_TYPE)
            
        if not update_changes:
            post_orders.exclude(gift_type = pcfg.CHANGE_GOODS_GIT_TYPE)

        for order in post_orders:   
            outer_sku_id = order.outer_sku_id
            outer_id  = order.outer_id
            order_num = order.num

            prod     = None
            prod_sku = None
            is_reverse = order.gift_type != pcfg.RETURN_GOODS_GIT_TYPE 
            
            if outer_sku_id and outer_id:
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
                prod_sku.update_quantity(order_num,dec_update=is_reverse)
            elif outer_id:
                prod  = Product.objects.get(outer_id=outer_id)
                prod.update_collect_num(order_num,dec_update=is_reverse)
            else:
                raise Exception('订单商品没有商家编码')
            if order.gift_type in (pcfg.REAL_ORDER_GIT_TYPE,pcfg.COMBOSE_SPLIT_GIT_TYPE):
                if prod_sku:
                    prod_sku.update_wait_post_num(order_num,dec_update=True)
                else:
                    prod.update_wait_post_num(order_num,dec_update=True)
            
        return True            
       
    @classmethod
    def get_trades_wait_post_prod_num(cls,outer_id,outer_sku_id):
        """ 获取订单商品待发数"""
        wait_nums = MergeOrder.objects.filter(outer_id=outer_id,outer_sku_id=outer_sku_id,
            merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS,sys_status=pcfg.IN_EFFECT)\
            .aggregate(sale_nums=Sum('num')).get('sale_nums')
        return wait_nums or 0
    
    def append_reason_code(self,code):  
        
        reason_set = set(self.reason_code.split(','))
        reason_set.add(str(code))
        self.reason_code = ','.join(list(reason_set))
        
        if code in (pcfg.POST_MODIFY_CODE,
                    pcfg.POST_SUB_TRADE_ERROR_CODE,
                    pcfg.COMPOSE_RULE_ERROR_CODE,
                    pcfg.PULL_ORDER_ERROR_CODE,
                    pcfg.PAYMENT_RULE_ERROR_CODE,
                    pcfg.MERGE_TRADE_ERROR_CODE):
            self.has_sys_err = True
        
        if (self.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                               pcfg.WAIT_SCAN_WEIGHT_STATUS) and 
                               self.can_review):
            self.can_review = False
            log_action(self.user.user.id,self,CHANGE,
                       u'新问题(编号：%s)'%self.reason_code)
        
        update_model_fields(self,update_fields=['reason_code',
                                                'has_sys_err',
                                                'can_review'])
        
        rows = MergeTrade.objects.filter(id=self.id,
                                         sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,
                                         is_locked=False)\
                                         .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        if rows > 0:
            self.sys_status = pcfg.WAIT_AUDIT_STATUS
        
        
    def remove_reason_code(self,code):   
        reason_set = set(self.reason_code.split(','))
        try:
            reason_set.remove(str(code))
        except:
            return False
        else:
            self.reason_code = ','.join(list(reason_set))
            
            update_model_fields(self,update_fields=['reason_code',])
        return True
    
    def has_reason_code(self,code):
        reason_set = set(self.reason_code.split(','))
        return str(code) in reason_set
    
    def update_buyer_message(self,trade_id,msg):

        msg = msg.replace('|','，'.decode('utf8'))\
                 .replace(':','：'.decode('utf8'))
        buyer_msg = self.buyer_message.split('|')
        
        msg_dict = {}
        for m in buyer_msg:
            m  = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.id)] = (self.buyer_message
                                        .replace('|','，'.decode('utf8'))
                                        .replace(':','：'.decode('utf8')))
        msg_dict[str(trade_id)] = msg
        self.buyer_message = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
        
        update_model_fields(self,update_fields=['buyer_message'])
        self.append_reason_code(pcfg.NEW_MEMO_CODE)
        
        return self.buyer_message
    
    def remove_buyer_message(self,trade_id):
        
        buyer_msg = self.buyer_message.split('|')
        msg_dict = {}
        for m in buyer_msg:
            m  = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
                
        if msg_dict:
            msg_dict.pop(int(trade_id),None)
            self.buyer_message = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
            
            update_model_fields(self,update_fields=['buyer_message'])
            
        return self.buyer_message
        
        
    def update_seller_memo(self,trade_id,msg):
        
        msg = msg.replace('|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m  = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.id)] = self.seller_memo.replace('|','，'.decode('utf8'))\
                    .replace(':','：'.decode('utf8'))
        msg_dict[str(trade_id)] = msg
        self.seller_memo = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
        
        update_model_fields(self,update_fields=['seller_memo'])
        
        self.append_reason_code(pcfg.NEW_MEMO_CODE)
        
        return self.seller_memo
        
        
    def remove_seller_memo(self,trade_id):
        
        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m  = m.split(':')
            if len(m)==2:
                msg_dict[m[0]] = m[1]
        if msg_dict:
            msg_dict.pop(str(trade_id),None)
            self.seller_memo = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
            
            update_model_fields(self,update_fields=['seller_memo'])
            
        return self.seller_memo
    
#平台名称与存储编码映射
TF_CODE_MAP = {
   pcfg.TF_WAP:MergeTrade.trade_from.WAP,
   pcfg.TF_HITAO:MergeTrade.trade_from.HITAO,
   pcfg.TF_TOP:MergeTrade.trade_from.TOP,
   pcfg.TF_TAOBAO:MergeTrade.trade_from.TAOBAO,
   pcfg.TF_JHS:MergeTrade.trade_from.JHS,
}

def recalc_trade_fee(sender,trade_id,*args,**kwargs):
    
    trade = MergeTrade.objects.get(id=trade_id)
    
    fee_dict   = trade.merge_orders.aggregate(total_total_fee=Sum('total_fee'),
                                      total_payment=Sum('payment'),
                                      total_discount_fee=Sum('discount_fee'),
                                      total_adjust_fee=Sum('adjust_fee'))
    
    trade.total_fee = fee_dict.get('total_total_fee') 
    trade.payment = fee_dict.get('total_payment') 
    trade.discount_fee = fee_dict.get('total_discount_fee') 
    trade.adjust_fee = fee_dict.get('total_adjust_fee') 
    
    update_model_fields(trade,update_fields=['total_fee',
                                             'payment',
                                             'discount_fee',
                                             'adjust_fee'])
    

recalc_fee_signal.connect(recalc_trade_fee, sender=MergeTrade)

class MergeOrder(models.Model):
    
    SYS_ORDER_STATUS    = SYS_ORDER_STATUS
    TAOBAO_ORDER_STATUS = TAOBAO_ORDER_STATUS
    GIFT_TYPE           = GIFT_TYPE
    
    id    = BigIntegerAutoField(primary_key=True)
    oid   = models.CharField(max_length=32,
                             default=lambda:'HYO%d'%int(time.time()*10**5),
                             verbose_name=u'原单ID')
    merge_trade = BigIntegerForeignKey(MergeTrade,
                                       related_name='merge_orders',
                                       verbose_name=u'所属订单')
    
    cid    = models.BigIntegerField(db_index=True,null=True,verbose_name=u'商品分类')
    num_iid  = models.CharField(max_length=64,blank=True,verbose_name=u'线上商品编号')
    title  =  models.CharField(max_length=128,blank=True,verbose_name=u'商品标题')
    price  = models.FloatField(default=0.0,verbose_name=u'单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name=u'商品数量')
    
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
    
    total_fee    = models.FloatField(default=0.0,verbose_name=u'总费用')
    payment      = models.FloatField(default=0.0,verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0,verbose_name=u'折扣')
    adjust_fee   = models.FloatField(default=0.0,verbose_name=u'调整费用')

    sku_properties_name = models.CharField(max_length=256,blank=True,
                                           verbose_name=u'购买商品规格')
    
    refund_id = models.BigIntegerField(null=True,blank=True,verbose_name=u'退款号')
    refund_status = models.CharField(max_length=40,choices=REFUND_STATUS,
                                     blank=True,verbose_name=u'退款状态')
    
    pic_path = models.CharField(max_length=128,blank=True,verbose_name=u'商品图片')
    
    seller_nick = models.CharField(max_length=32,blank=True,db_index=True,verbose_name=u'卖家昵称')
    buyer_nick  = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'买家昵称')
    
    created       =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'创建日期')
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'发货日期')
    
    out_stock   = models.BooleanField(default=False,verbose_name=u'缺货')
    is_merge    = models.BooleanField(default=False,verbose_name=u'合并') 
    is_rule_match    = models.BooleanField(default=False,verbose_name=u'匹配')
    is_reverse_order = models.BooleanField(default=False,verbose_name=u'追改')
    gift_type   = models.IntegerField(choices=GIFT_TYPE,default=0,verbose_name=u'类型')
    
    status = models.CharField(max_length=32,choices=TAOBAO_ORDER_STATUS,
                              blank=True,verbose_name=u'订单状态')
    sys_status = models.CharField(max_length=32,
                                  choices=SYS_ORDER_STATUS,
                                  blank=True,
                                  default='',
                                  verbose_name=u'系统状态')
    
    class Meta:
        db_table = 'shop_trades_mergeorder_c'
        unique_together = ("oid","merge_trade")
        verbose_name=u'订单商品'
        verbose_name_plural = u'订单商品列表'
        
    def __unicode__(self):
        return '<%s,%s>'%(str(self.id),self.outer_id)
        
    def isEffect(self):    
        return self.sys_status == pcfg.IN_EFFECT
    
    def isInvalid(self):    
        return self.sys_status == pcfg.INVALID_STATUS
            
    @classmethod
    def get_yesterday_orders_totalnum(cls,shop_user_id,outer_id,outer_sku_id):
        """ 获取某店铺昨日某商品销售量，与总销量 """
        
        st_f,st_t = get_yesterday_interval_time()
        orders    = cls.objects.filter(merge_trade__pay_time__gte=st_f,
                                       merge_trade__pay_time__lte=st_t,
                                       outer_id=outer_id,
                                       outer_sku_id=outer_sku_id)
        total_num = orders.count()
        user_order_num = orders.filter(merge_trade__user__id=shop_user_id).count()
        
        return total_num,user_order_num
    
    @classmethod
    @transaction.commit_on_success
    def gen_new_order(cls,trade_id,outer_id,outer_sku_id,num,gift_type=pcfg.REAL_ORDER_GIT_TYPE
                      ,status=pcfg.WAIT_SELLER_SEND_GOODS,is_reverse=False,payment='0'):
        
        merge_trade = MergeTrade.objects.get(id=trade_id)
        product = Product.objects.get(outer_id=outer_id)
        sku_properties_name = ''
        productsku = None
        if outer_sku_id:
            try:
                productsku = ProductSku.objects.get(outer_id=outer_sku_id,product__outer_id=outer_id)
                sku_properties_name = productsku.name
            except Exception,exc:
                 logger.error(exc.message,exc_info=True)
                 merge_trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
        merge_order = MergeOrder.objects.create(
            merge_trade = merge_trade,
            outer_id = outer_id,
            price = product.std_sale_price,
            payment = payment,
            num = num,
            title = product.name,
            outer_sku_id = outer_sku_id,
            sku_properties_name = sku_properties_name,
            refund_status = pcfg.NO_REFUND,
            seller_nick = merge_trade.user.nick,
            buyer_nick = merge_trade.buyer_nick,
            created = merge_trade.created,
            pay_time = merge_trade.pay_time,
            consign_time = merge_trade.consign_time,
            gift_type = gift_type,
            is_reverse_order = is_reverse,
            out_stock = (productsku.is_out_stock if productsku else product.is_out_stock),
            status = status,
            sys_status = pcfg.IN_EFFECT,
        )
        post_save.send(sender=cls, instance=merge_order) #通知消息更新主订单
        return merge_order

    def getSimpleName(self):
        
        try:
            prod = Product.objects.get(outer_id=self.outer_id)
            prodSku = None
            if self.outer_sku_id:
                prodSku = ProductSku.objects.get(outer_id=self.outer_sku_id,
                                                 product=prod)
            return prod.name + (prodSku and prodSku.name or '') + ' x ' +str(self.num)
        except:
            return self.title +' x '+str(self.num)
            
    
def refresh_trade_status(sender,instance,*args,**kwargs):
    #更新主订单的状态
    merge_trade   = instance.merge_trade
    
    if (merge_trade.buyer_nick and 
        (not instance.seller_nick or not instance.buyer_nick)):
        instance.seller_nick = merge_trade.user.nick
        instance.buyer_nick  = merge_trade.buyer_nick
        instance.created     = merge_trade.created
        instance.pay_time    = merge_trade.pay_time
        
        update_model_fields(instance,update_fields=['seller_nick',
                                                    'buyer_nick',
                                                    'created',
                                                    'pay_time'])
    
    effect_orders         = merge_trade.inuse_orders
    merge_trade.order_num = effect_orders.aggregate(
                        total_num=Sum('num'))['total_num'] or 0
    
    prod_num      = effect_orders.values_list('outer_id').distinct().count()
    merge_trade.prod_num = prod_num
    
    if merge_trade.status in(pcfg.WAIT_SELLER_SEND_GOODS,
                             pcfg.WAIT_BUYER_CONFIRM_GOODS):
        
        merge_trade.has_refund     = MergeTrade.objects.isTradeRefunding(merge_trade)
        merge_trade.has_out_stock  = effect_orders.filter(out_stock=True).count()>0
        merge_trade.has_rule_match = effect_orders.filter(is_rule_match=True).count()>0
        
        if not merge_trade.has_out_stock:
            merge_trade.remove_reason_code(pcfg.OUT_GOOD_CODE)    
    
    if (not merge_trade.reason_code and 
        merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS and 
        merge_trade.logistics_company and 
        merge_trade.sys_status == pcfg.WAIT_AUDIT_STATUS and 
        merge_trade.type not in (pcfg.DIRECT_TYPE,
                                 pcfg.REISSUE_TYPE,
                                 pcfg.EXCHANGE_TYPE)):
        
        merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
        
    update_model_fields(merge_trade,update_fields=['order_num',
                                                   'prod_num',
                                                   'has_refund',
                                                   'has_out_stock',
                                                   'has_rule_match',
                                                   'sys_status'])
        
post_save.connect(refresh_trade_status, sender=MergeOrder)


class MergeBuyerTrade(models.Model):
    
    sub_tid    =  models.BigIntegerField(primary_key=True)
    main_tid   =  models.BigIntegerField(db_index=True)
    created    =  models.DateTimeField(null=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_trades_mergebuyertrade_c'
        verbose_name = u'合单记录'
        verbose_name_plural = u'合单列表'
        
    def __unicode__(self):
        return '<%d,%d>'%(self.sub_tid,self.main_tid)
    
    @classmethod
    def getMergeType(cls,id):
        """
        0,no merge,
        1,sub merge trade,
        2,main merge trade
        """
        try:
            cls.objects.get(sub_tid=id)
        except cls.DoesNotExist:
            merges = cls.objects.filter(main_tid=id)
            if merges.count()>0:
                return pcfg.MAIN_MERGE_TYPE
            return pcfg.NO_MERGE_TYPE
        return pcfg.SUB_MERGE_TYPE


REPLAY_TRADE_STATUS = (
    (pcfg.RP_INITIAL_STATUS,u'初始状态'),
    (pcfg.RP_WAIT_ACCEPT_STATUS,u'待接单'),
    (pcfg.RP_WAIT_CHECK_STATUS,u'待验单'),
    (pcfg.RP_ACCEPT_STATUS,u'已验单'),
    (pcfg.RP_CANCEL_STATUS,u'已作废'),
)

class ReplayPostTrade(models.Model):
    """ 已发货清单 """
    
    operator   =  models.CharField(max_length=32,db_index=True,verbose_name=u'发货人')
    
    fid        =  models.BigIntegerField(default=0,verbose_name=u'父批次号') #正常0，合并-1，合并子单 父ID
    
    post_data  =  models.TextField(blank=True,verbose_name=u'清单数据')
    
    order_num  =  models.BigIntegerField(default=0,verbose_name=u'发货单数')
    trade_ids  =  models.TextField(blank=True,verbose_name=u'订单编号')
    
    succ_num   =  models.BigIntegerField(default=0,verbose_name=u'成功单数')
    succ_ids   =  models.TextField(blank=True,verbose_name=u'成功订单ID')
    
    created    =  models.DateTimeField(null=True,db_index=True,
                                       auto_now_add=True,verbose_name=u'创建日期')
    finished   =  models.DateTimeField(blank=True,db_index=True,
                                       null=True,verbose_name=u'完成日期')
    
    receiver   =  models.CharField(max_length=32,db_index=True,
                                   blank=True,verbose_name=u'接单人')
    rece_date  =  models.DateTimeField(blank=True,null=True,
                                       db_index=True,verbose_name=u'接单时间')
    check_date =  models.DateTimeField(blank=True,null=True,
                                       db_index=True,verbose_name=u'验收时间')
    
    status     =  models.IntegerField(default=0,db_index=True,
                                      choices=REPLAY_TRADE_STATUS,
                                      verbose_name=u'状态')
    
    class Meta:
        db_table = 'shop_trades_replayposttrade'
        verbose_name = u'已发货清单'
        verbose_name_plural = u'发货清单列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>'%(self.id,self.operator,
                                self.receiver,
                                dict(REPLAY_TRADE_STATUS).get(self.status,''))    
        
    def merge(self,post_trades):
        """合并多批发货清单"""
        
        if post_trades.count()==0:
            return False
        
        all_id_set = set()
        for t in post_trades:
            all_id_set.update(t.trade_ids.split(','))
            
        self.order_num = len(all_id_set)
        self.trade_ids = ','.join(all_id_set)
        self.fid       = -1
        self.save()
        #生成合并后的发货清单
        from shopback.trades.tasks import get_replay_results
        get_replay_results(self)
        
        for t in post_trades:
            t.fid     = self.id
            t.status  = pcfg.RP_CANCEL_STATUS
            t.save()
            
        return True
        
    def split(self):
        """拆分已合并的发货清单"""
        if self.fid != -1 or self.status != pcfg.RP_WAIT_ACCEPT_STATUS:
            raise Exception(u'不符合拆分条件')

        replay_trades = ReplayPostTrade.objects.filter(
                           fid=self.id,
                           status=pcfg.RP_CANCEL_STATUS)    
        for t in replay_trades:
            t.status = pcfg.RP_WAIT_ACCEPT_STATUS
            t.fid    = 0
            t.save()
        
        self.status = pcfg.RP_CANCEL_STATUS
        self.save()
        return True
    
    
