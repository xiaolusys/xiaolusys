# coding: utf-8
import time

from django.db import models
from django.db.models import Q, Sum

from shopback import paramconfig as pcfg
from shopback.logistics.models import Logistics, LogisticsCompany
from shopback.users.models import User
from shopback.orders.models import STEP_TRADE_STATUS
from shopback.refunds.models import REFUND_STATUS

from .models import (SYS_TRADE_STATUS, TAOBAO_TRADE_STATUS, TRADE_TYPE,
                     COD_STATUS, SHIPPING_TYPE_CHOICE, PRIORITY_TYPE,
                     SYS_ORDER_STATUS, TAOBAO_ORDER_STATUS, GIFT_TYPE)
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES


def default_dirtytrade_tid():
    return 'DD%d' % int(time.time() * 10 ** 5)


class DirtyMergeTrade(models.Model):
    TAOBAO_TYPE = pcfg.TAOBAO_TYPE
    FENXIAO_TYPE = pcfg.FENXIAO_TYPE
    SALE_TYPE = pcfg.SALE_TYPE
    JD_TYPE = pcfg.JD_TYPE
    YHD_TYPE = pcfg.YHD_TYPE
    DD_TYPE = pcfg.DD_TYPE
    SN_TYPE = pcfg.SN_TYPE
    WX_TYPE = pcfg.WX_TYPE
    AMZ_TYPE = pcfg.AMZ_TYPE
    DIRECT_TYPE = pcfg.DIRECT_TYPE
    REISSUE_TYPE = pcfg.REISSUE_TYPE
    EXCHANGE_TYPE = pcfg.EXCHANGE_TYPE

    EMPTY_STATUS = pcfg.EMPTY_STATUS
    WAIT_AUDIT_STATUS = pcfg.WAIT_AUDIT_STATUS
    WAIT_PREPARE_SEND_STATUS = pcfg.WAIT_PREPARE_SEND_STATUS
    WAIT_CHECK_BARCODE_STATUS = pcfg.WAIT_CHECK_BARCODE_STATUS
    WAIT_SCAN_WEIGHT_STATUS = pcfg.WAIT_SCAN_WEIGHT_STATUS
    FINISHED_STATUS = pcfg.FINISHED_STATUS
    INVALID_STATUS = pcfg.INVALID_STATUS
    ON_THE_FLY_STATUS = pcfg.ON_THE_FLY_STATUS
    REGULAR_REMAIN_STATUS = pcfg.REGULAR_REMAIN_STATUS

    TRADE_NO_CREATE_PAY = pcfg.TRADE_NO_CREATE_PAY
    WAIT_SELLER_SEND_GOODS = pcfg.WAIT_SELLER_SEND_GOODS
    WAIT_BUYER_CONFIRM_GOODS = pcfg.WAIT_BUYER_CONFIRM_GOODS
    TRADE_BUYER_SIGNED = pcfg.TRADE_BUYER_SIGNED
    TRADE_FINISHED = pcfg.TRADE_FINISHED
    TRADE_CLOSED = pcfg.TRADE_CLOSED
    TRADE_CLOSED_BY_TAOBAO = pcfg.TRADE_CLOSED_BY_TAOBAO

    TRADE_REFUNDED = pcfg.TRADE_REFUNDED
    TRADE_REFUNDING = pcfg.TRADE_REFUNDING

    WAIT_WEIGHT_STATUS = pcfg.WAIT_WEIGHT_STATUS
    SYS_TRADE_STATUS = SYS_TRADE_STATUS
    TAOBAO_TRADE_STATUS = TAOBAO_TRADE_STATUS
    TRADE_TYPE = TRADE_TYPE
    COD_STATUS = COD_STATUS
    SHIPPING_TYPE_CHOICE = SHIPPING_TYPE_CHOICE
    PRIORITY_TYPE = PRIORITY_TYPE

    WARE_NONE = 0
    WARE_SH = 1
    WARE_GZ = 2
    WARE_CHOICES = WARE_CHOICES

    tid = models.CharField(max_length=32,
                           default=default_dirtytrade_tid,
                           verbose_name=u'原单ID')
    user = models.ForeignKey(User,
                             related_name='dirty_merge_trades',
                             verbose_name=u'所属店铺', null=True, blank=True)
    buyer_nick = models.CharField(max_length=64,
                                  db_index=True,
                                  blank=True,
                                  verbose_name=u'买家昵称')

    type = models.CharField(max_length=32,
                            choices=TRADE_TYPE,
                            db_index=True,
                            blank=True,
                            verbose_name=u'订单类型')
    shipping_type = models.CharField(max_length=12,
                                     blank=True,
                                     choices=SHIPPING_TYPE_CHOICE,
                                     verbose_name=u'物流方式')

    order_num = models.IntegerField(default=0, verbose_name=u'单数')
    prod_num = models.IntegerField(default=0, verbose_name=u'品类数')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')
    post_fee = models.FloatField(default=0.0, verbose_name=u'物流费用')
    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')

    is_cod = models.BooleanField(default=False, verbose_name=u'货到付款')
    seller_cod_fee = models.FloatField(default=0.0, verbose_name=u'COD卖家费用')
    buyer_cod_fee = models.FloatField(default=0.0, verbose_name=u'COD买家费用')
    cod_fee = models.FloatField(default=0.0, verbose_name=u'COD费用')
    cod_status = models.CharField(max_length=32,
                                  blank=True,
                                  choices=COD_STATUS,
                                  verbose_name=u'COD状态')

    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    post_cost = models.FloatField(default=0.0, verbose_name=u'物流成本')

    buyer_message = models.TextField(max_length=1000,
                                     blank=True,
                                     verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000,
                                   blank=True,
                                   verbose_name=u'卖家备注')
    sys_memo = models.TextField(max_length=1000,
                                blank=True,
                                verbose_name=u'系统备注')
    seller_flag = models.IntegerField(null=True, verbose_name=u'淘宝旗帜')

    created = models.DateTimeField(null=True, blank=True, verbose_name=u'生成日期')
    pay_time = models.DateTimeField(db_index=True,
                                    null=True,
                                    blank=True,
                                    verbose_name=u'付款日期')
    modified = models.DateTimeField(null=True, blank=True, verbose_name=u'修改日期')
    consign_time = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name=u'发货日期')
    send_time = models.DateTimeField(null=True,
                                     blank=True,
                                     verbose_name=u'预售日期')
    weight_time = models.DateTimeField(db_index=True,
                                       null=True,
                                       blank=True,
                                       verbose_name=u'称重日期')
    charge_time = models.DateTimeField(null=True,
                                       blank=True,
                                       verbose_name=u'揽件日期')
    remind_time = models.DateTimeField(null=True,
                                       blank=True,
                                       verbose_name=u'提醒日期')

    is_brand_sale = models.BooleanField(default=False, verbose_name=u'品牌特卖')
    is_force_wlb = models.BooleanField(default=False, verbose_name=u'物流宝')
    trade_from = models.IntegerField(verbose_name=u'交易来源')

    is_lgtype = models.BooleanField(default=False, verbose_name=u'速递')
    lg_aging = models.DateTimeField(null=True,
                                    blank=True,
                                    verbose_name=u'速递送达时间')
    lg_aging_type = models.CharField(max_length=20,
                                     blank=True,
                                     verbose_name=u'速递类型')

    buyer_rate = models.BooleanField(default=False, verbose_name=u'买家已评')
    seller_rate = models.BooleanField(default=False, verbose_name=u'卖家已评')
    seller_can_rate = models.BooleanField(default=False, verbose_name=u'卖家可评')
    is_part_consign = models.BooleanField(default=False, verbose_name=u'分单发货')

    out_sid = models.CharField(max_length=64,
                               db_index=True,
                               blank=True,
                               verbose_name=u'物流编号')
    logistics_company = models.ForeignKey(LogisticsCompany,
                                          null=True,
                                          blank=True,
                                          verbose_name=u'物流公司')
    receiver_name = models.CharField(max_length=25,
                                     blank=True,
                                     verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16,
                                      blank=True,
                                      verbose_name=u'省')
    receiver_city = models.CharField(max_length=16,
                                     blank=True,
                                     verbose_name=u'市')
    receiver_district = models.CharField(max_length=16,
                                         blank=True,
                                         verbose_name=u'区')

    receiver_address = models.CharField(max_length=128,
                                        blank=True,
                                        verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10,
                                    blank=True,
                                    verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24,
                                       db_index=True,
                                       blank=True,
                                       verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20,
                                      db_index=True,
                                      blank=True,
                                      verbose_name=u'电话')

    step_paid_fee = models.CharField(max_length=10,
                                     blank=True,
                                     verbose_name=u'分阶付款金额')
    step_trade_status = models.CharField(max_length=32,
                                         choices=STEP_TRADE_STATUS,
                                         blank=True,
                                         verbose_name=u'分阶付款状态')

    reason_code = models.CharField(max_length=100,
                                   blank=True,
                                   verbose_name=u'问题编号')  # 1,2,3 问题单原因编码集合
    status = models.CharField(max_length=32,
                              choices=TAOBAO_TRADE_STATUS,
                              blank=True,
                              verbose_name=u'订单状态')

    is_picking_print = models.BooleanField(default=False, verbose_name=u'发货单')
    is_express_print = models.BooleanField(default=False, verbose_name=u'物流单')
    is_send_sms = models.BooleanField(default=False, verbose_name=u'发货通知')
    has_refund = models.BooleanField(default=False, verbose_name=u'待退款')
    has_out_stock = models.BooleanField(default=False, verbose_name=u'缺货')
    has_rule_match = models.BooleanField(default=False, verbose_name=u'有匹配')
    has_memo = models.BooleanField(default=False, verbose_name=u'有留言')
    has_merge = models.BooleanField(default=False, verbose_name=u'有合单')
    has_sys_err = models.BooleanField(default=False, verbose_name=u'系统错误')
    refund_num = models.IntegerField(null=True,
                                     default=0,
                                     verbose_name=u'退款单数')  # 退款单数

    is_qrcode = models.BooleanField(default=False, verbose_name=u'热敏订单')
    qrcode_msg = models.CharField(max_length=32,
                                  blank=True,
                                  verbose_name=u'打印信息')

    can_review = models.BooleanField(default=False, verbose_name=u'复审')
    priority = models.IntegerField(default=0,
                                   choices=PRIORITY_TYPE,
                                   verbose_name=u'优先级')
    operator = models.CharField(max_length=32, blank=True, verbose_name=u'打单员')
    scanner = models.CharField(max_length=64, blank=True, verbose_name=u'扫描员')
    weighter = models.CharField(max_length=64, blank=True, verbose_name=u'称重员')
    is_locked = models.BooleanField(default=False, verbose_name=u'锁定')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')
    sys_status = models.CharField(max_length=32,
                                  db_index=True,
                                  choices=SYS_TRADE_STATUS,
                                  blank=True,
                                  default='',
                                  verbose_name=u'系统状态')
    ware_by = models.IntegerField(default=WARE_SH,
                                  choices=WARE_CHOICES,
                                  db_index=True,
                                  verbose_name=u'所属仓库')
    reserveo = models.CharField(max_length=64, blank=True, verbose_name=u'自定义1')
    reservet = models.CharField(max_length=64, blank=True, verbose_name=u'自定义2')
    reserveh = models.CharField(max_length=64, blank=True, verbose_name=u'自定义3')

    class Meta:
        db_table = 'shop_trades_dirtymergetrade'
        app_label = 'trades'
        verbose_name = u'脏订单'
        verbose_name_plural = u'脏订单列表'


def default_dirtyorder_oid():
    return 'DO%d' % int(time.time() * 10 ** 5)


class DirtyMergeOrder(models.Model):
    NO_REFUND = pcfg.NO_REFUND
    REFUND_WAIT_SELLER_AGREE = pcfg.REFUND_WAIT_SELLER_AGREE
    REFUND_WAIT_RETURN_GOODS = pcfg.REFUND_WAIT_RETURN_GOODS
    REFUND_CONFIRM_GOODS = pcfg.REFUND_CONFIRM_GOODS
    REFUND_REFUSE_BUYER = pcfg.REFUND_REFUSE_BUYER
    REFUND_CLOSED = pcfg.REFUND_CLOSED
    REFUND_SUCCESS = pcfg.REFUND_SUCCESS

    REAL_ORDER_GIT_TYPE = pcfg.REAL_ORDER_GIT_TYPE
    CS_PERMI_GIT_TYPE = pcfg.CS_PERMI_GIT_TYPE
    OVER_PAYMENT_GIT_TYPE = pcfg.OVER_PAYMENT_GIT_TYPE
    COMBOSE_SPLIT_GIT_TYPE = pcfg.COMBOSE_SPLIT_GIT_TYPE
    RETURN_GOODS_GIT_TYPE = pcfg.RETURN_GOODS_GIT_TYPE
    CHANGE_GOODS_GIT_TYPE = pcfg.CHANGE_GOODS_GIT_TYPE
    ITEM_GIFT_TYPE = pcfg.ITEM_GIFT_TYPE

    SYS_ORDER_STATUS = SYS_ORDER_STATUS
    TAOBAO_ORDER_STATUS = TAOBAO_ORDER_STATUS
    GIFT_TYPE = GIFT_TYPE

    NORMAL = pcfg.IN_EFFECT
    DELETE = pcfg.INVALID_STATUS
    SYS_ORDER_STATUS = ((NORMAL, u'有效'), (DELETE, u'无效'),)

    oid = models.CharField(max_length=32,
                           default=default_dirtyorder_oid,
                           verbose_name=u'原单ID')
    merge_trade = models.ForeignKey(DirtyMergeTrade,
                                    related_name='merge_orders',
                                    verbose_name=u'所属订单', blank=True, null=True)

    cid = models.BigIntegerField(null=True, verbose_name=u'商品分类')
    num_iid = models.CharField(max_length=64,
                               blank=True,
                               verbose_name=u'线上商品编号')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')

    sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=20,
                                    blank=True,
                                    verbose_name=u'规格编码')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')

    sku_properties_name = models.CharField(max_length=256,
                                           blank=True,
                                           verbose_name=u'购买规格')

    refund_id = models.BigIntegerField(null=True,
                                       blank=True,
                                       verbose_name=u'退款号')
    refund_status = models.CharField(max_length=40,
                                     choices=REFUND_STATUS,
                                     blank=True,
                                     verbose_name=u'退款状态')

    pic_path = models.CharField(max_length=512,
                                blank=True,
                                verbose_name=u'商品图片')

    seller_nick = models.CharField(max_length=32,
                                   blank=True,
                                   verbose_name=u'卖家昵称')
    buyer_nick = models.CharField(max_length=32,
                                  blank=True,
                                  verbose_name=u'买家昵称')

    created = models.DateTimeField(null=True, blank=True, verbose_name=u'创建日期')
    pay_time = models.DateTimeField(db_index=True,
                                    null=True,
                                    blank=True,
                                    verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name=u'发货日期')

    out_stock = models.BooleanField(default=False, verbose_name=u'缺货')
    is_merge = models.BooleanField(default=False, verbose_name=u'合并')
    is_rule_match = models.BooleanField(default=False, verbose_name=u'匹配')
    is_reverse_order = models.BooleanField(default=False, verbose_name=u'追改')
    gift_type = models.IntegerField(choices=GIFT_TYPE,
                                    default=0,
                                    verbose_name=u'类型')

    status = models.CharField(max_length=32,
                              choices=TAOBAO_ORDER_STATUS,
                              blank=True,
                              verbose_name=u'订单状态')
    sys_status = models.CharField(max_length=32,
                                  choices=SYS_ORDER_STATUS,
                                  blank=True,
                                  default='',
                                  verbose_name=u'系统状态')

    class Meta:
        db_table = 'shop_trades_dirtymergeorder'
        app_label = 'trades'
        verbose_name = u'脏订单明细'
        verbose_name_plural = u'脏订单明细列表'
