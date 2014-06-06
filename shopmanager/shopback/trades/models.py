#-*- coding:utf8 -*-
import time
import json
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from bitfield import BitField
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User,Customer
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
from django.db import IntegrityError, transaction
from auth import apis
from common.utils import parse_datetime ,get_yesterday_interval_time, update_model_fields
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
    (pcfg.EMPTY_STATUS,u'空状态'),
)

OUT_STOCK_KEYWORD = [u'到',u'预售']

SYS_ORDER_STATUS = (
    (pcfg.IN_EFFECT ,u'有效'),
    (pcfg.INVALID_STATUS,u'无效'),
)

TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY,u'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY,u'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,u'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,u'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,u'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED,u'交易成功'),
    (pcfg.TRADE_CLOSED,u'退款成功交易自动关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,u'付款前关闭交易'),
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
    (pcfg.TAOBAO_TYPE,u'一口价'),
    (pcfg.FENXIAO_TYPE,u'分销'),
    (pcfg.DIRECT_TYPE,u'内售'),
    (pcfg.REISSUE_TYPE,u'补发'),
    (pcfg.EXCHANGE_TYPE,u'退换货'),
    (pcfg.COD_TYPE,u'货到付款'),
    (pcfg.AUTO_DELIVERY_TYPE,u'自动发货'),
    (pcfg.GUARANTEE_TYPE,u'一口价、拍卖'),
    (pcfg.AUCTION_TYPE,u'拍卖'),
)

COD_TYPE = (
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
    (pcfg.PRIORITY_HIG,u'低'),
    (pcfg.PRIORITY_MID,u'中'),
    (pcfg.PRIORITY_LOW,u'高'),
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
    
    EMPTY_STATUS = pcfg.EMPTY_STATUS
    WAIT_AUDIT_STATUS = pcfg.WAIT_AUDIT_STATUS
    WAIT_PREPARE_SEND_STATUS  = pcfg.WAIT_PREPARE_SEND_STATUS
    WAIT_CHECK_BARCODE_STATUS = pcfg.WAIT_CHECK_BARCODE_STATUS
    WAIT_SCAN_WEIGHT_STATUS = pcfg.WAIT_SCAN_WEIGHT_STATUS
    FINISHED_STATUS = pcfg.FINISHED_STATUS
    INVALID_STATUS  = pcfg.INVALID_STATUS
    ON_THE_FLY_STATUS = pcfg.ON_THE_FLY_STATUS
    REGULAR_REMAIN_STATUS = pcfg.REGULAR_REMAIN_STATUS
    
    TRADE_NO_CREATE_PAY = pcfg.TRADE_NO_CREATE_PAY
    WAIT_BUYER_PAY = pcfg.WAIT_BUYER_PAY
    WAIT_SELLER_SEND_GOODS = pcfg.WAIT_SELLER_SEND_GOODS
    WAIT_BUYER_CONFIRM_GOODS = pcfg.WAIT_BUYER_CONFIRM_GOODS
    TRADE_BUYER_SIGNED = pcfg.TRADE_BUYER_SIGNED
    TRADE_FINISHED = pcfg.TRADE_FINISHED
    TRADE_CLOSED = pcfg.TRADE_CLOSED
    TRADE_CLOSED_BY_TAOBAO = pcfg.TRADE_CLOSED_BY_TAOBAO
     
    TAOBAO_TYPE = pcfg.TAOBAO_TYPE
    FENXIAO_TYPE = pcfg.FENXIAO_TYPE
    DIRECT_TYPE = pcfg.DIRECT_TYPE
    REISSUE_TYPE = pcfg.REISSUE_TYPE
    EXCHANGE_TYPE = pcfg.EXCHANGE_TYPE
    COD_TYPE = pcfg.COD_TYPE
    AUTO_DELIVERY_TYPE = pcfg.AUTO_DELIVERY_TYPE
    GUARANTEE_TYPE = pcfg.GUARANTEE_TYPE
    AUCTION_TYPE   = pcfg.AUCTION_TYPE
    
    PRIORITY_HIG = pcfg.PRIORITY_HIG
    PRIORITY_MID = pcfg.PRIORITY_MID
    PRIORITY_LOW = pcfg.PRIORITY_LOW
     
    Sys_status = SYS_TRADE_STATUS
    Status     = TAOBAO_TRADE_STATUS
    Type       = TRADE_TYPE
    Priority   = PRIORITY_TYPE
    
    id    = BigIntegerAutoField(primary_key=True,db_index=True,verbose_name=u'订单ID')
    
    tid   = models.CharField(max_length=32,
                             default=lambda:'HYD%d'%int(time.time()*10**5),
                             verbose_name=u'原单ID')  
    user       = models.ForeignKey(User,related_name='merge_trades',verbose_name=u'所属店铺')
    buyer_nick  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'买家昵称')
    
    type        = models.CharField(max_length=32,choices=Type,
                                  blank=True,verbose_name=u'订单类型')
    shipping_type = models.CharField(max_length=12,blank=True,
                                     choices=SHIPPING_TYPE_CHOICE,verbose_name=u'物流方式')
    
    order_num  =   models.IntegerField(default=0,verbose_name=u'单数')
    prod_num   =   models.IntegerField(default=0,verbose_name=u'品类数')
    payment    =   models.CharField(max_length=10,blank=True,verbose_name=u'实付款')
    discount_fee = models.CharField(max_length=10,blank=True,verbose_name=u'折扣')
    adjust_fee =   models.CharField(max_length=10,blank=True,verbose_name=u'调整费用')
    post_fee   =   models.CharField(max_length=10,blank=True,verbose_name=u'物流费用')
    total_fee  =   models.CharField(max_length=10,blank=True,verbose_name=u'总费用')
    alipay_no  =   models.CharField(max_length=128,blank=True,verbose_name=u'用户支付宝帐号')
    
    seller_cod_fee = models.CharField(max_length=10,blank=True,verbose_name=u'卖家货到付款费用')
    buyer_cod_fee  = models.CharField(max_length=10,blank=True,verbose_name=u'买家货到付款费用')
    cod_fee        = models.CharField(max_length=10,blank=True,verbose_name=u'货到付款费用')
    cod_status     = models.CharField(max_length=32,blank=True,
                                      choices=COD_TYPE,verbose_name=u'货到付款状态')
    
    weight        = models.CharField(max_length=10,blank=True,verbose_name=u'包裹重量')
    post_cost     = models.CharField(max_length=10,blank=True,verbose_name=u'物流成本')
    
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
    
    out_sid         = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'物流编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,blank=True,verbose_name=u'物流公司')
    receiver_name    =  models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=20,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,db_index=True,blank=True,verbose_name=u'电话')
    
    step_paid_fee      = models.CharField(max_length=10,blank=True,verbose_name=u'分阶付款金额')
    step_trade_status  = models.CharField(max_length=32,choices=STEP_TRADE_STATUS,
                                          blank=True,verbose_name=u'分阶付款状态')
    
    reason_code = models.CharField(max_length=100,blank=True,verbose_name=u'问题编号')  #1,2,3 问题单原因编码集合
    status      = models.CharField(max_length=32,db_index=True,choices=Status,
                                        blank=True,verbose_name=u'淘宝订单状态')
        
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
    qrcode_msg       = models.CharField(max_length=32,blank=True,verbose_name=u'条码错误')
    
    can_review       = models.BooleanField(default=False,verbose_name=u'复审') 
    priority       =  models.IntegerField(db_index=True,default=0,
                                          choices=Priority,verbose_name=u'优先级')
    operator       =  models.CharField(max_length=32,blank=True,verbose_name=u'发货员')
    is_locked      =  models.BooleanField(default=False,verbose_name=u'锁定')
    is_charged     =  models.BooleanField(default=False,verbose_name=u'揽件')
    sys_status     =  models.CharField(max_length=32,db_index=True,
                    choices=Sys_status,blank=True,default='',verbose_name=u'系统状态')
    
    reserveo       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义1')       
    reservet       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义2') 
    reserveh       =  models.CharField(max_length=64,blank=True,verbose_name=u'自定义3') 
    
    objects   = MergeTradeManager()
    
    class Meta:
        db_table = 'shop_trades_mergetrade'
        unique_together = ("user","tid")
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
                                 self.receiver_mobile.strip() or self.receiver_phone.strip(),
                                 self.receiver_state.strip(),
                                 self.receiver_city.strip(),
                                 self.receiver_district.strip(),
                                 self.receiver_address.strip(),
                                 self.receiver_zip.strip())
    
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
        return self.status in (self.WAIT_CHECK_BARCODE_STATUS,
                               self.WAIT_SCAN_WEIGHT_STATUS)
    
    def is_post_success(self):
        """ 判断订单淘宝发货成功 """
        if not self.tid:
            return False
        
        user_id = self.user.visitor_id
        response = apis.taobao_logistics_orders_get(tid=self.tid,tb_user_id=user_id,fields='out_sid,tid')
        trade_dicts = response['logistics_orders_get_response']['shippings']['shipping']
        
        if len(trade_dicts)>0:
            trade_dict = trade_dicts[0]
            out_sid = trade_dict.get('out_sid','') 
            if out_sid and out_sid == self.out_sid:
                return True
            elif out_sid and out_sid != self.out_sid: 
                raise Exception(u'系统快递单号与线上发货快递单号不一致')
            else:
                raise Exception(u'订单未发货')    
        else:       
            raise Exception(u'订单物流信息未查到')
    
    
    def send_trade_to_taobao(self,company_code=None,out_sid=None,retry_times=3):
        """ 订单在淘宝后台发货 """
        
        trade_id   = self.tid
        trade_type = self.type
        seller_id  = self.user.visitor_id
        company_code = company_code or self.logistics_company.code.split('_')[0]
        out_sid    = out_sid or self.out_sid
        
        if trade_type in (pcfg.EXCHANGE_TYPE,pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return False
        try:
            #如果货到付款
            if trade_type == pcfg.COD_TYPE:
                response = apis.taobao_logistics_online_send(tid=trade_id,out_sid=out_sid
                                              ,company_code=company_code,tb_user_id=seller_id)  
                #response = {'logistics_online_send_response': {'shipping': {'is_success': True}}}
                if not response['logistics_online_send_response']['shipping']['is_success']:
                    raise Exception(u'订单(%d)淘宝发货失败'%trade_id)
            else: 
                response = apis.taobao_logistics_offline_send(tid=trade_id,out_sid=out_sid
                                              ,company_code=company_code,tb_user_id=seller_id)  
                #response = {'logistics_offline_send_response': {'shipping': {'is_success': True}}}
                if not response['logistics_offline_send_response']['shipping']['is_success']:
                    raise Exception(u'订单(%d)淘宝发货失败'%trade_id)
        except apis.LogisticServiceBO4Exception,exc:
            return self.is_post_success()
        except apis.LogisticServiceB60Exception,exc:
            #如果系统没有该单号成功发货的记录，则改变快递名称，重新发货
            ts = MergeTrade.objects.filter(is_express_print=True,
                                           sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                           pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                           pcfg.FINISHED_STATUS),
                                           out_sid=out_sid)
            if ts.count() > 0:
                raise exc
                
            self.send_trade_to_taobao(company_code=u'%s送'%self.logistics_company.name)
            
        except Exception,exc:
            retry_times = retry_times - 1
            if retry_times<=0:
                logger.error(exc.message or u'订单发货出错',exc_info=True)
                raise exc
            #time.sleep(0.1)
            self.send_trade_to_taobao(company_code,out_sid,retry_times=retry_times)
             
        return True
    
    def isOrderMatch(self):
        try:
            post_orders = self.inuse_orders     
            for order in post_orders: 
                Product.objects.get(outer_id=order.outer_id)
                if order.outer_sku_id:
                    ProductSku.objects.get(outer_id=order.outer_sku_id,
                                           product__outer_id=order.outer_id)
            return True
        except:
            return True
    
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
            is_reverse = (False if order.gift_type == pcfg.RETURN_GOODS_GIT_TYPE else True)
            
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
       
    def save_customer(self):
        """ 保存客户信息 """
        
        if not (self.receiver_mobile or self.receiver_phone):
            return 
   
        customer,state     = Customer.objects.get_or_create(nick=self.buyer_nick,
                                                            mobile=self.receiver_mobile,
                                                            phone=self.receiver_phone)
        customer.name      = self.receiver_name
        customer.zip       = self.receiver_zip
        customer.address   = self.receiver_address
        customer.city      = self.receiver_city
        customer.state     = self.receiver_state
        customer.district  = self.receiver_district
        customer.save()
        
        trades        = MergeTrade.objects.filter(buyer_nick=self.buyer_nick,
                        receiver_mobile=self.receiver_mobile,
                        status__in=pcfg.ORDER_SUCCESS_STATUS).exclude(is_express_print=False,
                        sys_status=pcfg.FINISHED_STATUS).order_by('-pay_time')
        trade_num     = trades.count()
        if trades.count()>0 and trade_num != customer.buy_times:
            total_nums    =  trades.count()
            total_payment = trades.aggregate(total_payment=Sum('payment')).get('total_payment') or 0
            
            customer.last_buy_time = trades[0].pay_time
            customer.buy_times     = trades.count()
            customer.avg_payment   = float(round(float(total_payment)/total_nums,2))
            customer.save()
            
            
    @classmethod
    def get_trades_wait_post_prod_num(cls,outer_id,outer_sku_id):
        """ 获取订单商品待发数"""
        wait_nums = MergeOrder.objects.filter(outer_id=outer_id,outer_sku_id=outer_sku_id,
            merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS,sys_status=pcfg.IN_EFFECT)\
            .aggregate(sale_nums=Sum('num')).get('sale_nums')
        return wait_nums or 0
    
    def append_reason_code(self,code):  
        reason_set = set(self.reason_code.split(','))
        old_len = len(reason_set)
        reason_set.add(str(code))
        new_len = len(reason_set)
        self.reason_code = ','.join(list(reason_set))
        if code in (pcfg.POST_MODIFY_CODE,pcfg.POST_SUB_TRADE_ERROR_CODE,
                    pcfg.COMPOSE_RULE_ERROR_CODE,pcfg.PULL_ORDER_ERROR_CODE,
                    pcfg.PAYMENT_RULE_ERROR_CODE,pcfg.MERGE_TRADE_ERROR_CODE,
                    pcfg.OUTER_ID_NOT_MAP_CODE):
            self.has_sys_err = True
        if self.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS or pcfg.WAIT_SCAN_WEIGHT_STATUS) and self.can_review:
            self.can_review = False
            log_action(self.user.user.id,self,CHANGE,u'订单有新问题(%s)，取消复审'%self.reason_code)
        update_model_fields(self,update_fields=['reason_code','has_sys_err','can_review'])
        
        rows = MergeTrade.objects.filter(id=self.id,sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,out_sid='')\
            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        if rows >0:
            self.sys_status = pcfg.WAIT_AUDIT_STATUS
        
        return old_len<new_len
         
        
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
            if len(m)==2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.id)] = self.buyer_message.replace(
                        '|','，'.decode('utf8')).replace(':','：'.decode('utf8'))
        msg_dict[str(id)]=msg
        self.buyer_message = '|'.join(['%s:%s'%(k,v) for k,v in msg_dict.items()])
        
        update_model_fields(self,update_fields=['buyer_message'])
        
        self.append_reason_code(pcfg.NEW_MEMO_CODE)
        
        return self.buyer_message
    
    def remove_buyer_message(self,trade_id):
        
        buyer_msg = self.buyer_message.split('|')
        msg_dict = {}
        for m in buyer_msg:
            m  = m.split(':')
            if len(m)==2:
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
    
        
    def has_order_refunding(self):
        #判断是否有等待退款的订单
        orders = self.merge_orders.filter(refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
        if orders.count()>0:
            return True
        return False
   
    
    @classmethod
    def judge_out_stock(cls,trade_id):
        #判断是否有缺货
        is_out_stock = False
        try:
            trade = MergeTrade.objects.get(id=trade_id)
        except Trade.DoesNotExist:
            logger.error('trade(id:%d) does not exist'%trade_id)
        else:
            orders = trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)
            for order in orders:
                is_order_out = False
                if order.outer_sku_id:
                    try:
                        product_sku = ProductSku.objects.get(product__outer_id=order.outer_id,outer_id=order.outer_sku_id)    
                    except:
                        trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                        order.is_rule_match=True
                    else:
                        is_order_out  |= product_sku.is_out_stock
                        #更新待发数
                        product_sku.update_wait_post_num(order.num)
                elif order.outer_id:
                    try:
                        product = Product.objects.get(outer_id=order.outer_id)
                    except:
                        trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                        order.is_rule_match=True
                    else:
                        is_order_out |= product.is_out_stock
                        #更新待发数
                        product.update_wait_post_num(order.num)
                
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
                    order.out_stock=True
                    order.save()
                is_out_stock |= is_order_out
                
        if not is_out_stock:
            trade.remove_reason_code(pcfg.OUT_GOOD_CODE)
        else:
            trade.append_reason_code(pcfg.OUT_GOOD_CODE)
            
        return is_out_stock

    
    @classmethod
    def judge_full_refund(cls,trade_id):
        #更新订单实际商品和退款商品数量，返回退款状态

        merge_trade = cls.objects.get(id=trade_id)  

        refund_approval_num = merge_trade.merge_orders.filter(refund_status__in=pcfg.REFUND_APPROVAL_STATUS
                            ,gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()
        total_orders_num  = merge_trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()

        if refund_approval_num==total_orders_num:
            return True
        
        return False

    @classmethod
    def judge_new_refund(cls,trade_id):
        #判断是否有新退款
        merge_trade = cls.objects.get(id=trade_id)
        refund_orders_num   = merge_trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE)\
            .exclude(Q(is_merge=True)|Q(refund_status=pcfg.NO_REFUND)).count()
        
        if refund_orders_num >merge_trade.refund_num:
            merge_trade.refund_num = refund_orders_num
            update_model_fields(merge_trade,update_fields=['refund_num'])
            
            return True
        return False
        
    @classmethod
    def judge_rule_match(cls,trade_id):
        
        #系统设置是否进行规则匹配
        config  = SystemConfig.getconfig()
        if not config.is_rule_auto:
            return False
        
        merge_trade = cls.objects.get(id=trade_id)
        try:
            rule_signal.send(sender='product_rule',trade_id=trade_id)
        except:
            merge_trade.append_reason_code(pcfg.RULE_MATCH_CODE)
            return True
        else:
            return False
        
    @classmethod
    def get_merge_queryset(cls,buyer_nick,receiver_name,receiver_mobile):
        
        q = Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
        if receiver_mobile:
            q = q|Q(receiver_mobile=receiver_mobile)|Q(receiver_phone=receiver_mobile)
        
        trades = cls.objects.filter(q)
        
        return trades
        
    @classmethod
    def judge_need_merge(cls,trade_id,buyer_nick,receiver_name,receiver_mobile):
        #是否需要合单 
        if not receiver_name:   
            return False  
            
        queryset = cls.get_merge_queryset(buyer_nick,receiver_name,receiver_mobile)
        trades = queryset.exclude(id=trade_id).exclude(
                    sys_status__in=('',pcfg.FINISHED_STATUS,pcfg.INVALID_STATUS))
        is_need_merge = False
        
        if trades.count() > 0:
            for trade in trades:
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
            if not obj.modified or obj.modified < modified or not obj.sys_status:
                need_pull = True
        return need_pull


    def judge_jhs_wlb(self):
        """ 判断订单是聚划算物流宝发货 """
        need_wlb = False
        try:
            rule_signal.send(sender='ju_hua_suan',trade_id=self.id)
        except:
            self.append_reason_code(pcfg.TRADE_BY_JHS_CODE)
            need_wlb = True
        else:
            need_wlb = False
            
        return need_wlb


def recalc_trade_fee(sender,trade_id,*args,**kwargs):
    
    trade = MergeTrade.objects.get(id=trade_id)
    
    fee_dict   = trade.merge_orders.aggregate(total_total_fee=Sum('total_fee'),
                                      total_payment=Sum('payment'),
                                      total_discount_fee=Sum('discount_fee'),
                                      total_adjust_fee=Sum('adjust_fee'))
    
    trade.total_fee = fee_dict.total_total_fee 
    trade.payment = fee_dict.total_payment 
    trade.discount_fee = fee_dict.total_discount_fee 
    trade.adjust_fee = fee_dict.total_adjust_fee 
    
    update_model_fields(trade,update_fields=['total_fee',
                                             'payment',
                                             'discount_fee',
                                             'adjust_fee'])
    

recalc_fee_signal.connect(recalc_trade_fee, sender=MergeTrade)

class MergeOrder(models.Model):
    
    id    = BigIntegerAutoField(primary_key=True)
    
    oid   = models.CharField(max_length=32,
                             default=lambda:'HYO%d'%int(time.time()*10**5),
                             verbose_name=u'原单ID')
    merge_trade = BigIntegerForeignKey(MergeTrade,
                                       related_name='merge_orders',
                                       verbose_name=u'所属订单')
    
    cid    = models.BigIntegerField(db_index=True,null=True,verbose_name=u'商品分类')
    num_iid  = models.CharField(max_length=64,blank=True,verbose_name=u'线上商品编号')
    title  =  models.CharField(max_length=128,verbose_name=u'商品标题')
    price  = models.CharField(max_length=12,blank=True,verbose_name=u'单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name=u'商品数量')
    
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
    
    total_fee = models.CharField(max_length=12,blank=True,verbose_name=u'总费用')
    payment = models.CharField(max_length=12,blank=True,verbose_name=u'实付款')
    discount_fee = models.CharField(max_length=12,blank=True,verbose_name=u'折扣')
    adjust_fee = models.CharField(max_length=12,blank=True,verbose_name=u'调整费用')

    sku_properties_name = models.CharField(max_length=256,blank=True,verbose_name=u'购买商品规格')
    
    refund_id = models.BigIntegerField(null=True,blank=True,verbose_name=u'退款号')
    refund_status = models.CharField(max_length=40,choices=REFUND_STATUS,blank=True,verbose_name=u'退款状态')
    
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
    
    status = models.CharField(max_length=32,choices=TAOBAO_ORDER_STATUS,blank=True,verbose_name=u'淘宝订单状态')
    sys_status = models.CharField(max_length=32,choices=SYS_ORDER_STATUS,blank=True,default='',verbose_name=u'系统订单状态')
    
    class Meta:
        db_table = 'shop_trades_mergeorder'
        unique_together = ("merge_trade","oid")
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
        orders    = cls.objects.filter(merge_trade__pay_time__gte=st_f,merge_trade__pay_time__lte=st_t
                        ,outer_id=outer_id,outer_sku_id=outer_sku_id)
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
        
        update_model_fields(instance,update_fields=['seller_nick','buyer_nick','created','pay_time'])
    
    effect_orders = merge_trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)
    order_num     = effect_orders.count()#
    merge_trade.order_num = order_num
    
    prod_num      = effect_orders.values_list('outer_id').distinct().count()
    merge_trade.prod_num = prod_num
    
    if merge_trade.status in(pcfg.WAIT_SELLER_SEND_GOODS,pcfg.WAIT_BUYER_CONFIRM_GOODS):
        has_refunding  = merge_trade.has_trade_refunding()
        out_stock      = effect_orders.filter(out_stock=True).count()>0
        has_rule_match = effect_orders.filter(is_rule_match=True).count()>0
        
        merge_trade.has_refund = has_refunding
        merge_trade.has_out_stock = out_stock
        merge_trade.has_rule_match = has_rule_match
    
        if not out_stock:
            merge_trade.remove_reason_code(pcfg.OUT_GOOD_CODE)    
    
    if (not merge_trade.reason_code and 
        merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS and 
        merge_trade.logistics_company and 
        merge_trade.sys_status==pcfg.WAIT_AUDIT_STATUS and 
        merge_trade.type not in (pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE,pcfg.EXCHANGE_TYPE)):
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
        db_table = 'shop_trades_mergebuyertrade'
        verbose_name = u'合单记录'
        verbose_name_plural = u'合单列表'
        
    def __unicode__(self):
        return '<%d,%d>'%(self.sub_tid,self.main_tid)
    
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

@transaction.commit_on_success
def merge_order_maker(sub_tid,main_tid):
    #合单操作
    
    MergeTrade.objects.filter(tid=main_tid,out_sid='',status=pcfg.WAIT_SELLER_SEND_GOODS)\
            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
    
    sub_trade      = MergeTrade.objects.get(tid=sub_tid)
    main_merge_trade = MergeTrade.objects.get(tid=main_tid)
    
    payment      = 0
    total_fee    = 0
    discount_fee = 0
    post_fee     = float(sub_trade.post_fee or 0 ) + float(main_merge_trade.post_fee or 0)
    is_reverse_order = main_merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS)
    for order in sub_trade.merge_orders.all():
        try:
            if order.oid:
                merge_order,state = MergeOrder.objects.get_or_create(oid=order.oid,
                                                                     merge_trade=main_merge_trade)
            else:
                merge_order = MergeOrder()
        except:
            merge_order = MergeOrder()
        
        for field in order._meta.fields:
            if field.name not in ('id','tid','merge_trade'):
                setattr(merge_order,field.name,getattr(order,field.name))
        
        merge_order.merge_trade = main_merge_trade
        merge_order.is_merge    = True
        merge_order.sys_status  = order.sys_status
        merge_order.is_reverse_order = is_reverse_order
        merge_order.save()
        
        if order.sys_status == pcfg.IN_EFFECT:
            payment   += float(order.payment or 0)
            total_fee += float(order.total_fee or 0)
            discount_fee += float(order.discount_fee or 0)
    
    if sub_trade.buyer_message:
        main_merge_trade.update_buyer_message(sub_tid,sub_trade.buyer_message)
        main_merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        
    if sub_trade.seller_memo:
        main_merge_trade.update_seller_memo(sub_tid,sub_trade.seller_memo)
        main_merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        
    MergeTrade.objects.filter(tid=main_tid).update(payment = payment + float(main_merge_trade.payment ),
                                                   total_fee = total_fee + float(main_merge_trade.total_fee ),
                                                   discount_fee = discount_fee + float(main_merge_trade.discount_fee or 0),
                                                   post_fee = post_fee)
    
    MergeBuyerTrade.objects.get_or_create(sub_tid=sub_tid,main_tid=main_tid) 
            
    sub_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    if sub_trade.has_merge:
        MergeBuyerTrade.objects.filter(main_tid=sub_trade.tid).update(main_tid=main_tid)
                                                  
    #判断是否还有订单需要合并,如果没有，则去掉需合单问题编号
    queryset = MergeTrade.get_merge_queryset(main_merge_trade.buyer_nick,main_merge_trade.receiver_name,
                                main_merge_trade.receiver_mobile or main_merge_trade.receiver_phone)
    if queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.REGULAR_REMAIN_STATUS))\
        .exclude(id__in=(sub_trade.id,main_merge_trade.id)).count()==0:
        main_merge_trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
    sub_trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
    
    log_action(main_merge_trade.user.user.id,main_merge_trade,CHANGE,u'订单合并成功（%s,%s）'%(main_tid,sub_tid))
    
    if not main_merge_trade.reason_code and not main_merge_trade.out_sid:
        main_merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
        main_merge_trade.save()
    else:
        main_merge_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    return True

@transaction.commit_on_success
def merge_order_remover(main_tid):
    #拆单操作
    main_trade = MergeTrade.objects.get(tid=main_tid)
    
    if not main_trade.has_merge:
        return
    
    if main_trade.type == pcfg.TAOBAO_TYPE:
        trade = Trade.objects.get(id=main_tid)
        main_trade.payment    = trade.payment
        main_trade.total_fee  = trade.total_fee
        main_trade.post_fee   = trade.post_fee
        main_trade.adjust_fee = trade.adjust_fee
        main_trade.discount_fee = trade.discount_fee
    elif main_trade.type == pcfg.FENXIAO_TYPE:
        purchase_order = PurchaseOrder.objects.get(id=main_tid)
        main_trade.payment   = purchase_order.distributor_payment
        main_trade.post_fee  = purchase_order.post_fee
        main_trade.total_fee = purchase_order.total_fee
    main_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    main_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE) 
    main_trade.has_merge = False
    update_model_fields(main_trade,update_fields=['payment','total_fee','post_fee','adjust_fee','discount_fee','has_merge'])
    
    main_trade.merge_orders.filter(Q(oid=None)|Q(is_merge=True)).delete()
    sub_merges = MergeBuyerTrade.objects.filter(main_tid=main_tid)
    for sub_merge in sub_merges:    
        sub_tid  = sub_merge.sub_tid
        sub_merge_trade = MergeTrade.objects.get(tid=sub_tid)
        sub_merge_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
        sub_merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        main_trade.remove_buyer_message(sub_tid)
        main_trade.remove_seller_memo(sub_tid)
        MergeTrade.objects.filter(tid=sub_tid).update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        
    MergeBuyerTrade.objects.filter(main_tid=main_tid).delete()
    
    log_action(main_trade.user.user.id,main_trade,CHANGE,u'订单取消合并成功')
    
    rule_signal.send(sender='combose_split_rule',trade_id=main_trade.id)
    rule_signal.send(sender='payment_rule',trade_id=main_trade.id) 
    
@transaction.commit_on_success
def drive_merge_trade_action(trade_id):
    """ 合单驱动程序 """
    is_merge_success = False
    main_tid   = None 
    merge_trade      = MergeTrade.objects.get(id=trade_id)
    trades     =  []
    try:
        if merge_trade.has_merge:
            return is_merge_success,merge_trade.tid
            
        if merge_trade.status != pcfg.WAIT_SELLER_SEND_GOODS:
            return is_merge_success,main_tid
        
        buyer_nick      = merge_trade.buyer_nick               #买家昵称
        receiver_mobile = merge_trade.receiver_mobile          #收货手机
        receiver_name    = merge_trade.receiver_name           #收货人
        receiver_address = merge_trade.receiver_address        #收货地址
        full_address     = merge_trade.buyer_full_address      #详细地址
        scan_merge_trades = MergeTrade.objects.filter(Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
                |Q(receiver_mobile=receiver_mobile),sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS))
        #如果有可能需合并的订单在待扫描区域，则主动合单程序不执行，手动合单
        if scan_merge_trades.count()>0:
            return is_merge_success,main_tid
        
        wait_refunding   = merge_trade.has_trade_refunding()   #待退款

        trades = MergeTrade.objects.filter(buyer_nick=buyer_nick,receiver_name=receiver_name,receiver_address=receiver_address
                                    ,sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS,pcfg.REGULAR_REMAIN_STATUS)
                                    ,is_force_wlb=False).order_by('pay_time')        
         
        #如果有已有合并记录，则将现有主订单作为合并主订单                           
        has_merge_trades = trades.filter(has_merge=True)                  
        if has_merge_trades.count()>0:
            main_tid = has_merge_trades[0].tid

        #如果入库订单没有待退款，则进行合单操作
        if trades.count()>0 and not wait_refunding:
            #如果没有则将按时间排序的第一符合条件的订单作为主订单
            can_merge = True
            if not main_tid:
                for t in trades.exclude(id=trade_id):
                    full_refund = MergeTrade.judge_full_refund(t.id)
                    if not full_refund and not t.has_refund and t.buyer_full_address == full_address:
                        main_tid = t.tid
                        break
                    if t.has_refund:
                        can_merge = False
                        break
                        
            if main_tid and can_merge:  
                #进行合单
                is_merge_success = merge_order_maker(merge_trade.tid,main_tid)
                main_trade = MergeTrade.objects.get(tid=main_tid)
                #合并后金额匹配
                rule_signal.send(sender='payment_rule',trade_id=main_trade.id)
        #如果入库订单待退款，则将同名的单置放入待审核区域
        elif trades.count()>0 or wait_refunding:
            if main_tid :
                merge_order_remover(main_tid)
            for t in trades:
                if t.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
                    if t.out_sid == '':
                        t.sys_status=pcfg.WAIT_AUDIT_STATUS
                        t.save()
                else:
                    t.sys_status=pcfg.WAIT_AUDIT_STATUS
                    t.has_merge=False
                    t.save()
    except Exception,exc:        
        logger.error(exc.message+'-- merge trade fail --',exc_info=True)
        merge_trade.append_reason_code(pcfg.MERGE_TRADE_ERROR_CODE)   
        for trade in trades:
            trade.append_reason_code(pcfg.MERGE_TRADE_ERROR_CODE)
       
    return is_merge_success,main_tid


def trade_download_controller(merge_trade,trade,trade_from,first_pay_load):
    
    shipping_type = merge_trade.shipping_type or 'null'
    seller_memo   = trade.memo  if hasattr(trade,'memo') else trade.seller_memo
    buyer_message = trade.buyer_message if hasattr(trade,'buyer_message') else trade.supplier_memo   
 
    merge_trade.has_memo = seller_memo or buyer_message
    has_new_buyer_message    = merge_trade.buyer_message != buyer_message 
    has_new_seller_memo  = merge_trade.seller_memo  != seller_memo
    
    merge_trade.buyer_message = buyer_message 
    merge_trade.seller_memo   = seller_memo
    
    #新留言
    if has_new_buyer_message or has_new_seller_memo:
        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        merge_type = MergeBuyerTrade.get_merge_type(trade.id)
        if merge_type == 1:
            mbt = MergeBuyerTrade.objects.get(sub_tid=merge_trade.tid)
            MergeTrade.objects.get(tid=mbt.main_tid).append_reason_code(pcfg.NEW_MEMO_CODE)
            
    if trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
        
        #给订单分配快递
        if not merge_trade.logistics_company:
            receiver_state = merge_trade.receiver_state
            receiver_city  = merge_trade.receiver_city
            receiver_district  = merge_trade.receiver_district
            try:
                if shipping_type.lower() == pcfg.EXPRESS_SHIPPING_TYPE.lower():
                    #如果聚划算订单，则判断是否有指定使用某快递
                    if merge_trade.trade_from&MergeTrade.trade_from.JHS:
                        assign_logistic = DestCompany.get_destcompany_by_addr(receiver_state,receiver_city,receiver_district)
                        if assign_logistic:
                            merge_trade.logistics_company = assign_logistic
                        else:
                            sys_config  = SystemConfig.getconfig()
                            if sys_config.jhs_logistic_code:
                                merge_trade.logistics_company = LogisticsCompany.objects.get(
                                                                code=sys_config.jhs_logistic_code.upper())
                            
                    if not merge_trade.logistics_company:
                        default_company = LogisticsCompany.get_recommend_express(receiver_state,receiver_city,receiver_district)
                        merge_trade.logistics_company = default_company
                elif shipping_type in (pcfg.POST_SHIPPING_TYPE,pcfg.EMS_SHIPPING_TYPE):
                    post_company = LogisticsCompany.objects.get(code=shipping_type.upper())
                    merge_trade.logistics_company = post_company
                    
            except Exception,exc:
                logger.error(exc.message or 'distribute logistic error',exc_info=True)
                merge_trade.append_reason_code(pcfg.DISTINCT_RULE_CODE)
     
        #退款中
        wait_refunding = merge_trade.has_trade_refunding()
        if wait_refunding:
            merge_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)
        #设置订单待退款属性    
        merge_trade.has_refund = wait_refunding

        has_full_refund = MergeTrade.judge_full_refund(merge_trade.id)
        has_new_refund  = MergeTrade.judge_new_refund(merge_trade.id)
        
        #如果首次付款后入库
        if first_pay_load:  
            
            rule_signal.send(sender='combose_split_rule',trade_id=merge_trade.id)

            #缺货 
            out_stock      =  MergeTrade.judge_out_stock(merge_trade.id)
            
            #设置订单是否有缺货属性    
            merge_trade.has_out_stock = out_stock

            #规则匹配
            is_rule_match  =  MergeTrade.judge_rule_match(merge_trade.id)    
     
            #设置订单匹配属性   
            merge_trade.has_rule_match = is_rule_match
            
            merge_trade.is_force_wlb = getattr(trade,'is_force_wlb',False) or \
                (merge_trade.trade_from&MergeTrade.trade_from.JHS and merge_trade.judge_jhs_wlb())
            #标记物流宝发货订单
            if merge_trade.is_force_wlb:
                merge_trade.append_reason_code(pcfg.TRADE_BY_WLB_CODE)
            
            #订单合并   
            is_merge_success = False #是否合并成功
            is_need_merge    = False #是否有合并的可能
            main_tid = None  #主订单ID
            if not has_full_refund:
                is_need_merge = MergeTrade.judge_need_merge(
                    merge_trade.id,merge_trade.buyer_nick,merge_trade.receiver_name,
                    merge_trade.receiver_mobile or merge_trade.receiver_phone)
                if is_need_merge :
                    merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                    #驱动合单程序
                    is_merge_success,main_tid = drive_merge_trade_action(merge_trade.id)
            
            #更新子订单物流公司信息    
            if is_need_merge and main_tid:
                main_trade = MergeTrade.objects.get(tid=main_tid)
                if not main_trade.logistics_company:
                    main_trade.logistics_company = LogisticsCompany.get_recommend_express(
                            main_trade.receiver_state,main_trade.receiver_city,main_trade.receiver_district)
                    main_trade.save()
                merge_trade.logistics_company = main_trade.logistics_company

            #进入待发货区域，需要进行商品金额规则匹配
            rule_signal.send(sender='payment_rule',trade_id=merge_trade.id)
            
            trade_reason_code = MergeTrade.objects.get(id=merge_trade.id).reason_code 
            #如果合单成功则将新单置为飞行模式                 
            if is_merge_success:
                merge_trade.sys_status = pcfg.ON_THE_FLY_STATUS
            #如果没有选择快递公司
            elif not merge_trade.logistics_company:
                merge_trade.append_reason_code(pcfg.LOGISTIC_ERROR_CODE)
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
            #有问题则进入问题单域
            elif trade_reason_code:
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
            else:
                merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS

        #再次入库
        else:
            #如果有新退款
            if has_new_refund:
                merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)

                merge_type  = MergeBuyerTrade.get_merge_type(trade.id)
                if merge_type == 0:    
                    MergeTrade.objects.filter(tid=trade.id,out_sid='').update(sys_status=pcfg.WAIT_AUDIT_STATUS,has_refund=True)
                elif merge_type == 1:
                    main_tid = MergeBuyerTrade.objects.get(sub_tid=trade.id).main_tid
                    merge_order_remover(main_tid)
                else:
                    merge_order_remover(merge_trade.tid)
                
                #如果拆单后订单系统状态改变，则将订单状态置为问题单
                tmp_trade = MergeTrade.objects.get(id=merge_trade.id)
                if tmp_trade.sys_status == pcfg.WAIT_AUDIT_STATUS:
                    merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
            
    elif trade.status==pcfg.WAIT_BUYER_CONFIRM_GOODS:
        has_new_refund  = MergeTrade.judge_new_refund(merge_trade.id)
        if has_new_refund:
            merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
            
            merge_type  = MergeBuyerTrade.get_merge_type(trade.id)
            #如果有合并的父订单，则设置父订单退款编号
            if merge_type == 1:    
                main_tid = MergeBuyerTrade.objects.get(sub_tid=trade.id).main_tid
                MergeTrade.objects.get(tid=main_tid).append_reason_code(pcfg.NEW_REFUND_CODE)
                
        if merge_trade.sys_status in pcfg.WAIT_DELIVERY_STATUS and not merge_trade.out_sid:
            merge_trade.sys_status = pcfg.INVALID_STATUS
            
    elif trade.status==pcfg.TRADE_CLOSED:
        has_new_refund  = MergeTrade.judge_new_refund(merge_trade.id)
        if has_new_refund :
            merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
            merge_type = MergeBuyerTrade.get_merge_type(trade.id)
            if merge_type == 1:
                mbt = MergeBuyerTrade.objects.get(sub_tid=merge_trade.tid)
                MergeTrade.objects.get(tid=mbt.main_tid).append_reason_code(pcfg.NEW_REFUND_CODE)
                
        if merge_trade.sys_status not in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                                 pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                                 pcfg.FINISHED_STATUS): 
            merge_type  = MergeBuyerTrade.get_merge_type(trade.id)
            if merge_type == 2:    
                merge_order_remover(merge_trade.tid)
        
        if merge_trade.sys_status not in (pcfg.FINISHED_STATUS,pcfg.INVALID_STATUS): 
            merge_trade.append_reason_code(pcfg.INVALID_END_CODE)
            merge_trade.sys_status = pcfg.INVALID_STATUS
    
    #是否对系统内部的订单进行，合单拦截？
    elif trade.status in (pcfg.TRADE_NO_CREATE_PAY,pcfg.WAIT_BUYER_PAY):
        pass
    
    #如果淘宝订单状态已改变，而系统内部状态非最终状态，则将订单作废        
    elif merge_trade.sys_status:
        if merge_trade.sys_status not in (pcfg.FINISHED_STATUS,pcfg.INVALID_STATUS) and not merge_trade.out_sid: 
            merge_trade.append_reason_code(pcfg.INVALID_END_CODE)
            merge_trade.sys_status = pcfg.INVALID_STATUS
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
            is_force_wlb = merge_trade.is_force_wlb,
    )

#平台名称与存储编码映射
TF_CODE_MAP = {
               pcfg.TF_WAP:MergeTrade.trade_from.WAP,
               pcfg.TF_HITAO:MergeTrade.trade_from.HITAO,
               pcfg.TF_TOP:MergeTrade.trade_from.TOP,
               pcfg.TF_TAOBAO:MergeTrade.trade_from.TAOBAO,
               pcfg.TF_JHS:MergeTrade.trade_from.JHS,
               }

def map_trade_from_to_code(trade_from):
    
    from_code = 0
    from_list = trade_from.split(',')
    for f in from_list:
        from_code |= TF_CODE_MAP.get(f.upper(),0)
        
    return from_code
     
def save_orders_trade_to_mergetrade(sender, trade, *args, **kwargs):
    
    try:
        tid  = trade.id
        merge_trade,state = MergeTrade.objects.get_or_create(user=trade.user,tid=tid)
        
        first_pay_load = not merge_trade.sys_status
        if not merge_trade.receiver_name and trade.receiver_name:
            #保存地址
            merge_trade.receiver_name = trade.receiver_name 
            merge_trade.receiver_state   = trade.receiver_state 
            merge_trade.receiver_city = trade.receiver_city 
            merge_trade.receiver_district = trade.receiver_district 
            merge_trade.receiver_address = trade.receiver_address 
            merge_trade.receiver_zip  = trade.receiver_zip 
            merge_trade.receiver_mobile  = trade.receiver_mobile 
            merge_trade.receiver_phone = trade.receiver_phone 
            
            update_model_fields(merge_trade,update_fields= ['receiver_name',
                                                            'receiver_state',
                                                            'receiver_city',
                                                            'receiver_district',
                                                            'receiver_address',
                                                            'receiver_zip',
                                                            'receiver_mobile',
                                                            'receiver_phone'])
      
        #保存商城或C店订单到抽象全局抽象订单表
        for order in trade.trade_orders.all():
            merge_order,state = MergeOrder.objects.get_or_create(
                                oid=order.oid,merge_trade = merge_trade)
            state = state or not merge_order.sys_status
            if (state and order.refund_status in 
                (pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_SUCCESS)
                or order.status in (pcfg.TRADE_CLOSED,pcfg.TRADE_CLOSED_BY_TAOBAO)):
                sys_status = pcfg.INVALID_STATUS
            else:
                sys_status = merge_order.sys_status or pcfg.IN_EFFECT
            
            if state:
                order_fields = ['num_iid','title','price','sku_id','num',
                                'outer_id','outer_sku_id','total_fee','payment',
                                'refund_status','pic_path','seller_nick','buyer_nick',
                                'created','pay_time','consign_time','status']
                
                for k in order_fields:
                    setattr(merge_order,k,getattr(order,k))
                
                merge_order.sku_properties_name = order.properties_values
                merge_order.sys_status = sys_status
            else:
                merge_order.refund_status = order.refund_status
                merge_order.payment = order.payment
                merge_order.pay_time = order.pay_time
                merge_order.consign_time = order.consign_time
                merge_order.status   = order.status
                merge_order.sys_status = sys_status
            merge_order.save()
            
        #保存基本订单信息
        trade_from    = pcfg.FENXIAO_TYPE if trade.type==pcfg.FENXIAO_TYPE else pcfg.TAOBAO_TYPE
        if first_pay_load:
            merge_trade.payment   = trade.payment
            merge_trade.total_fee = trade.total_fee
            merge_trade.discount_fee = trade.discount_fee
            merge_trade.adjust_fee   = trade.adjust_fee
            merge_trade.post_fee     = trade.post_fee
        else:
            merge_trade.payment   = merge_trade.payment or trade.payment
            merge_trade.total_fee   = merge_trade.total_fee or trade.total_fee
            merge_trade.discount_fee   = merge_trade.discount_fee or trade.discount_fee
            merge_trade.adjust_fee   = merge_trade.adjust_fee or trade.adjust_fee
            merge_trade.post_fee   = merge_trade.post_fee or trade.post_fee
        
        update_fields = ['buyer_nick','type','seller_cod_fee','buyer_cod_fee',
                         'cod_fee','cod_status','seller_flag','created','pay_time',
                         'modified','consign_time','send_time','status','is_brand_sale','is_lgtype',
                         'lg_aging','lg_aging_type','buyer_rate','seller_rate','seller_can_rate',
                         'is_part_consign','step_paid_fee','step_trade_status']
        
        for k in update_fields:
            setattr(merge_trade,k,getattr(trade,k))
        
        merge_trade.trade_from    = map_trade_from_to_code(trade.trade_from)
        merge_trade.alipay_no     = trade.buyer_alipay_no
        merge_trade.shipping_type = merge_trade.shipping_type or \
                pcfg.SHIPPING_TYPE_MAP.get(trade.shipping_type,pcfg.EXPRESS_SHIPPING_TYPE)
        
        update_model_fields(merge_trade,update_fields=update_fields
                            +['shipping_type','payment','total_fee','discount_fee','adjust_fee',
                              'post_fee','alipay_no','trade_from'])

        #设置系统内部状态信息
        trade_download_controller(merge_trade,trade,trade_from,first_pay_load) 
  
    except Exception,exc:
        logger.error(exc.message,exc_info=True)

merge_trade_signal.connect(save_orders_trade_to_mergetrade,sender=Trade,dispatch_uid='merge_trade')        


def save_fenxiao_orders_to_mergetrade(sender, trade, *args, **kwargs):
    try:
        tid = trade.id
        merge_trade,state = MergeTrade.objects.get_or_create(user=trade.user,tid=tid)
        
        first_pay_load = not merge_trade.sys_status 
        #如果交易是等待卖家发货，第一次入库，或者没有卖家收货信息，则更新其物流信息
        if not merge_trade.receiver_name and trade.status not in ('',pcfg.TRADE_NO_CREATE_PAY,
                                pcfg.WAIT_BUYER_PAY,pcfg.TRADE_CLOSED,pcfg.TRADE_CLOSED_BY_TAOBAO):
            logistics = Logistics.get_or_create(trade.user.visitor_id,tid)
            location = json.loads(logistics.location or 'null')
            
            merge_trade.receiver_name = logistics.receiver_name 
            merge_trade.receiver_zip  = location.get('zip','') if location else '' 
            merge_trade.receiver_mobile = logistics.receiver_mobile 
            merge_trade.receiver_phone = logistics.receiver_phone 

            merge_trade.receiver_state = location.get('state','') if location else '' 
            merge_trade.receiver_city  = location.get('city','') if location else ''
            merge_trade.receiver_district = location.get('district','') if location else '' 
            merge_trade.receiver_address  = location.get('address','') if location else '' 
            
            update_model_fields(merge_trade,update_fields= ['receiver_name',
                                                            'receiver_state',
                                                            'receiver_city',
                                                            'receiver_district',
                                                            'receiver_address',
                                                            'receiver_zip',
                                                            'receiver_mobile',
                                                            'receiver_phone'])

        #保存分销订单到抽象全局抽象订单表
        for order in trade.sub_purchase_orders.all():
            merge_order,state = MergeOrder.objects.get_or_create(oid=order.fenxiao_id,
                                                                 merge_trade = merge_trade)
            state = state or not merge_order.sys_status
            
            fenxiao_product = FenxiaoProduct.get_or_create(trade.user.visitor_id,order.item_id)
            if order.status == pcfg.TRADE_REFUNDING:
                refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
            elif order.status == pcfg.TRADE_REFUNDED:
                refund_status = pcfg.REFUND_SUCCESS
            else:
                refund_status = pcfg.NO_REFUND
            if state and order.status in (pcfg.TRADE_REFUNDING,
                                          pcfg.TRADE_CLOSED,
                                          pcfg.TRADE_REFUNDED):
                sys_status = pcfg.INVALID_STATUS
            else:
                sys_status = merge_order.sys_status or pcfg.IN_EFFECT     
            if state:    
                merge_order.num_iid = fenxiao_product.item_id
                merge_order.title  = order.title
                merge_order.price  = order.price
                merge_order.sku_id = order.sku_id
                merge_order.num    = order.num
                merge_order.outer_id = order.item_outer_id
                merge_order.outer_sku_id = order.sku_outer_id
                merge_order.total_fee = order.total_fee
                merge_order.payment = order.distributor_payment
                merge_order.sku_properties_name = order.properties_values
                merge_order.refund_status = refund_status
                merge_order.pic_path = fenxiao_product.pictures and fenxiao_product.pictures.split(',')[0] or ''
                merge_order.seller_nick = merge_trade.user.nick
                merge_order.buyer_nick  = merge_trade.buyer_nick
                merge_order.created  = order.created
                merge_order.pay_time = merge_trade.created
                merge_order.consign_time  = merge_trade.consign_time
                merge_order.status   = pcfg.FENXIAO_TAOBAO_STATUS_MAP.get(order.status,order.status)
                merge_order.sys_status    = sys_status
            else:
                merge_order.refund_status = refund_status
                merge_order.payment       = order.distributor_payment
                merge_order.consign_time  = merge_trade.consign_time
                merge_order.status        = order.status
                merge_order.sys_status    = sys_status
            merge_order.save()
        
        trade_from = pcfg.FENXIAO_TYPE
        if first_pay_load:
            merge_trade.payment   = trade.distributor_payment
            merge_trade.total_fee = trade.total_fee
            merge_trade.post_fee  = trade.post_fee
        else:
            merge_trade.payment   = merge_trade.payment or trade.distributor_payment
            merge_trade.total_fee = merge_trade.total_fee or trade.total_fee
            merge_trade.post_fee  = merge_trade.post_fee or trade.post_fee
        
        merge_trade.buyer_nick = trade.distributor_username
        merge_trade.type = pcfg.FENXIAO_TYPE
        merge_trade.shipping_type = merge_trade.shipping_type or\
                pcfg.SHIPPING_TYPE_MAP.get(trade.shipping,pcfg.EXPRESS_SHIPPING_TYPE)
        merge_trade.created = trade.created
        merge_trade.pay_time = trade.created
        merge_trade.modified = trade.modified
        merge_trade.consign_time = trade.consign_time
        merge_trade.seller_flag  = trade.supplier_flag
        merge_trade.priority = 0
        merge_trade.status   = trade.status
        merge_trade.trade_from  = TF_CODE_MAP[pcfg.TF_TAOBAO]
        
        update_fields = ['buyer_nick','type','shipping_type','payment',
                         'total_fee','post_fee','created','trade_from',
                         'pay_time','modified','consign_time',
                         'seller_flag','priority','status']
        
        update_model_fields(merge_trade,update_fields=update_fields)
        #更新系统内部状态
        trade_download_controller(merge_trade,trade,trade_from,first_pay_load)
        
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
    
merge_trade_signal.connect(save_fenxiao_orders_to_mergetrade,sender=PurchaseOrder,dispatch_uid='merge_purchaseorder')


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
    
    post_data  =  models.TextField(blank=True,verbose_name=u'发货清单数据')
    
    order_num  =  models.BigIntegerField(default=0,verbose_name=u'发货单数')
    trade_ids  =  models.TextField(blank=True,verbose_name=u'订单编号')
    
    succ_num   =  models.BigIntegerField(default=0,verbose_name=u'成功单数')
    succ_ids   =  models.TextField(blank=True,verbose_name=u'成功订单数据')
    
    created    =  models.DateTimeField(null=True,db_index=True,auto_now_add=True,verbose_name=u'创建日期')
    finished   =  models.DateTimeField(blank=True,db_index=True,null=True,verbose_name=u'发货完成日期')
    
    receiver   =  models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'接单人')
    rece_date  =  models.DateTimeField(blank=True,null=True,db_index=True,verbose_name=u'接单时间')
    check_date =  models.DateTimeField(blank=True,null=True,db_index=True,verbose_name=u'验收时间')
    
    status     =  models.IntegerField(default=0,db_index=True,choices=REPLAY_TRADE_STATUS,verbose_name=u'状态')
    
    class Meta:
        db_table = 'shop_trades_replayposttrade'
        verbose_name = u'已发货清单'
        verbose_name_plural = u'发货清单列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>'%(self.id,self.operator,self.receiver,dict(REPLAY_TRADE_STATUS).get(self.status,''))    
        
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

        replay_trades = ReplayPostTrade.objects.filter(fid=self.id,status=pcfg.RP_CANCEL_STATUS)    
        for t in replay_trades:
            t.status = pcfg.RP_WAIT_ACCEPT_STATUS
            t.fid    = 0
            t.save()
        
        self.status = pcfg.RP_CANCEL_STATUS
        self.save()
        return True
    
    
