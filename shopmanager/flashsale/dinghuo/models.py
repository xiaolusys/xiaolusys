# -*- coding:utf-8 -*-
import datetime
import re
import sys
import copy
import numpy as np
from django.db import models
from django.db.models import Sum, Count, F, Q
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.db import transaction

from core.utils.modelutils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseModel
from shopback.items.models import ProductSku, Product, ProductSkuStats
from shopback.refunds.models import Refund
from supplychain.supplier.models import SaleSupplier, SaleProduct
import logging

logger = logging.getLogger(__name__)

import logging

logger = logging.getLogger(__name__)


class OrderList(models.Model):
    # 订单状态
    SUBMITTING = u'草稿'  # 提交中
    APPROVAL = u'审核'  # 审核
    WAIT_PAY = u"付款"
    ZUOFEI = u'作废'  # 作废
    COMPLETED = u'验货完成'  # 验货完成
    QUESTION = u'有问题'  # 有问题
    CIPIN = u'5'  # 有次品
    QUESTION_OF_QUANTITY = u'6'  # 到货有问题
    DEALED = u'已处理'  # 已处理
    SAMPLE = u'7'  # 样品
    TO_BE_PAID = u'待收款'
    TO_PAY = u'待付款'
    CLOSED = u'完成'
    NEAR = u'1'  # 江浙沪皖
    SHANGDONG = u'2'  # 山东
    GUANGDONG = u'3'  # 广东
    YUNDA = u'YUNDA'
    STO = u'STO'
    ZTO = u'ZTO'
    EMS = u'EMS'
    ZJS = u'ZJS'
    SF = u'SF'
    YTO = u'YTO'
    HTKY = u'HTKY'
    TTKDEX = u'TTKDEX'
    QFKD = u'QFKD'
    DBKD = u'DBKD'

    ST_DRAFT = 'draft'
    ST_APPROVAL = 'approval'
    ST_BILLING = 'billing'
    ST_FINISHED = 'finished'
    ST_CLOSE = 'close'

    SYS_STATUS_CHOICES = (
        (ST_DRAFT, u'草稿'),
        (ST_APPROVAL, u'已审核'),
        (ST_BILLING, u'结算中'),
        (ST_FINISHED, u'已结算'),
        (ST_CLOSE, u'已取消'),
    )

    CREATED_BY_PERSON = 1
    CREATED_BY_MACHINE = 2

    ORDER_PRODUCT_STATUS = ((SUBMITTING, u'草稿'), (APPROVAL, u'审核'),
                            (ZUOFEI, u'作废'), (QUESTION, u'有次品又缺货'),
                            (CIPIN, u'有次品'), (QUESTION_OF_QUANTITY, u'到货数量问题'),
                            (COMPLETED, u'验货完成'), (DEALED, u'已处理'),
                            (SAMPLE, u'样品'), (TO_PAY, u'待付款'),
                            (TO_BE_PAID, u'待收款'), (CLOSED, u'完成'))
    BUYER_OP_STATUS = ((DEALED, u'已处理'), (TO_BE_PAID, u'待收款'), (TO_PAY, u'待付款'),
                       (CLOSED, u'完成'))

    ORDER_DISTRICT = ((NEAR, u'江浙沪皖'),
                      (SHANGDONG, u'山东'),
                      (GUANGDONG, u'广东福建'),)
    EXPRESS_CONPANYS = ((YUNDA, u'韵达速递'),
                        (STO, u'申通快递'),
                        (ZTO, u'中通快递'),
                        (EMS, u'邮政'),
                        (ZJS, u'宅急送'),
                        (SF, u'顺丰速运'),
                        (YTO, u'圆通'),
                        (HTKY, u'汇通快递'),
                        (TTKDEX, u'天天快递'),
                        (QFKD, u'全峰快递'),
                        (DBKD, u'德邦快递'),)

    PC_COD_TYPE = 11  # 货到付款
    PC_PREPAID_TYPE = 12  # 预付款
    PC_POD_TYPE = 13  # 付款提货
    PC_OTHER_TYPE = 14  # 其它
    PURCHASE_PAYMENT_TYPE = (
        (PC_COD_TYPE, u'货到付款'),
        (PC_PREPAID_TYPE, u'预付款'),
        (PC_POD_TYPE, u'付款提货'),
        (PC_OTHER_TYPE, u'其它'),
    )

    id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(User,
                              null=True,
                              related_name='dinghuo_orderlists',
                              verbose_name=u'负责人')
    buyer_name = models.CharField(default="", max_length=32, verbose_name=u'买手')
    order_amount = models.FloatField(default=0, verbose_name=u'金额')
    bill_method = models.IntegerField(choices=PURCHASE_PAYMENT_TYPE, default=PC_COD_TYPE, verbose_name=u'付款类型')
    supplier_name = models.CharField(default="",
                                     blank=True,
                                     max_length=128,
                                     verbose_name=u'商品链接')
    supplier_shop = models.CharField(default="",
                                     blank=True,
                                     max_length=32,
                                     verbose_name=u'供应商店铺名')
    supplier = models.ForeignKey(SaleSupplier,
                                 null=True,
                                 blank=True,
                                 related_name='dinghuo_orderlist',
                                 verbose_name=u'供应商')

    express_company = models.CharField(choices=EXPRESS_CONPANYS,
                                       blank=True,
                                       max_length=32,
                                       verbose_name=u'快递公司')
    express_no = models.CharField(default="",
                                  blank=True,
                                  max_length=32,
                                  verbose_name=u'快递单号')

    receiver = models.CharField(default="", max_length=32, verbose_name=u'负责人')
    costofems = models.IntegerField(default=0, verbose_name=u'快递费用')
    status = models.CharField(max_length=32,
                              db_index=True,
                              verbose_name=u'订货单状态',
                              choices=ORDER_PRODUCT_STATUS)
    pay_status = models.CharField(max_length=32,
                                  db_index=True,
                                  verbose_name=u'收款状态')
    p_district = models.CharField(max_length=32,
                                  default=NEAR,
                                  verbose_name=u'地区',
                                  choices=ORDER_DISTRICT)  # 从发货地对应仓库
    reach_standard = models.BooleanField(default=False, verbose_name=u"达标")
    created = models.DateField(auto_now_add=True,
                               db_index=True,
                               verbose_name=u'订货日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    completed_time = models.DateTimeField(blank=True, null=True, verbose_name=u'完成时间')
    note = models.TextField(default="", blank=True, verbose_name=u'备注信息')
    created_by = models.SmallIntegerField(
        choices=((CREATED_BY_PERSON, u'手工订货'), (CREATED_BY_MACHINE, u'订单自动订货')),
        default=CREATED_BY_PERSON,
        verbose_name=u'创建方式')

    sys_status = models.CharField(max_length=16,
                                  db_index=True,
                                  default=ST_DRAFT,
                                  verbose_name=u'系统状态',
                                  choices=SYS_STATUS_CHOICES)
    STAGE_DRAFT = 0
    STAGE_CHECKED = 1
    STAGE_PAY = 2
    STAGE_RECEIVE = 3
    STAGE_STATE = 4
    STAGE_COMPLETED = 5
    STAGE_DELETED = 9
    STAGE_CHOICES = ((STAGE_DRAFT, u'草稿'),
                     (STAGE_CHECKED, u'审核'),
                     (STAGE_PAY, u'付款'),
                     (STAGE_RECEIVE, u'收货'),
                     (STAGE_STATE, u'结算'),
                     (STAGE_COMPLETED, u'完成'),
                     (STAGE_DELETED, u'删除'))
    # 改进原状态一点小争议和妥协造成的状态字段冗余 TODO@hy
    stage = models.IntegerField(db_index=True, choices=STAGE_CHOICES, default=0, verbose_name=u'进度')
    lack = models.NullBooleanField(default=None, verbose_name=u'缺货')
    inferior = models.BooleanField(default=False, verbose_name=u'次品')
    press_num = models.IntegerField(default=0, verbose_name=u'催促次数')
    purchase_total_num = models.IntegerField(default=0, verbose_name=u'订购总件数')
    last_pay_date = models.DateField(null=True, blank=True, verbose_name=u'最后下单日期')
    is_postpay = models.BooleanField(default=False, verbose_name=u'后付')
    purchase_order_unikey = models.CharField(max_length=32, unique=True, null=True, verbose_name=u'PurchaseOrderUnikey')

    class Meta:
        db_table = 'suplychain_flashsale_orderlist'
        app_label = 'dinghuo'
        verbose_name = u'订货表'
        verbose_name_plural = u'订货表'
        permissions = [("change_order_list_inline", u"修改后台订货信息"), ]

    def costofems_cash(self):
        return self.costofems / 100.0

    costofems_cash.allow_tags = True
    costofems_cash.short_description = u"快递费用"

    @property
    def amount(self):
        return self.order_amount

    def get_product_list(self):
        if self.supplier_name:
            return self.supplier_name
        else:
            return self.supplier.product_link

    def get_buyer_name(self):
        buyer_name = '未知'
        if self.buyer_id:
            buyer_name = '%s%s' % (self.buyer.last_name,
                                   self.buyer.first_name)
            buyer_name = buyer_name or self.buyer.username
        return buyer_name

    def is_open(self):
        return self.status == OrderList.SUBMITTING

    def is_booked(self):
        return self.status != OrderList.SUBMITTING and \
               self.status != OrderList.COMPLETED and \
               self.status != OrderList.ZUOFEI and \
               self.status != OrderList.CLOSED

    def is_finished(self):
        return self.status == OrderList.COMPLETED or self.status == OrderList.CLOSED

    def is_canceled(self):
        return self.status == OrderList.ZUOFEI

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['chichu_id'] for i in self.order_list.values('chichu_id')]
        return self._sku_ids_

    @property
    def skus(self):
        if not hasattr(self, '_skus_'):
            self._skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(prod_skus__id__in=self.sku_ids).distinct()
        return self._products_

    def products_item_sku(self):
        products = self.products
        for order_detail in self.order_list.order_by('product_id'):
            for product in products:
                if order_detail.product_id == product.id:
                    if not hasattr(product, 'order_details'):
                        product.order_details = []
                    product.order_details.append(order_detail)
                    break
                    continue
        for product in products:
            product.skus = [od.sku for od in product.order_details]
            product.detail_length = len(product.skus)
        return products

    def __unicode__(self):
        return '<%s, %s, %s>' % (str(self.id or ''),
                                 self.last_pay_date and self.last_pay_date.strftime('%Y-%m-%d') or '------------',
                                 self.buyer_name)

    def normal_details(self):
        return self.order_list.all()

    @property
    def total_detail_num(self):
        order_nums = self.normal_details().values_list('buy_quantity', flat=True)
        return order_nums and sum(order_nums) or 0

    @property
    def status_name(self):
        return self.get_sys_status_display()

    def press(self, desc):
        OrderGuarantee(purchase_order=self, desc=desc).save()
        self.press_num = self.guarantees.count()
        self.save(update_fields=['press_num'])

    def set_stat(self):
        if self.stage in [OrderList.STAGE_DRAFT, OrderList.STAGE_CHECKED, OrderList.STAGE_DELETED]:
            self.lack = None
            return
        lack = False
        inferior = False
        arrival_quantity_total = 0
        for detail in self.order_list.all():
            if detail.need_arrival_quantity > 0:
                lack = True
            if detail.inferior_quantity > 0:
                inferior = True
            arrival_quantity_total += detail.arrival_quantity + detail.inferior_quantity
        if arrival_quantity_total == 0:
            lack = None
        change = False
        if self.lack != lack:
            change = True
            self.lack = lack
        elif self.inferior != inferior:
            change = True
            self.inferior = inferior
        return change

    def has_paid(self):
        return self.status > OrderList.STAGE_PAY

    def set_stage_verify(self, is_postpay=False):
        self.stage = OrderList.STAGE_CHECKED
        self.status = OrderList.APPROVAL
        self.purchase_total_num = self.order_list.aggregate(
                total_num=Sum('buy_quantity')).get('total_num') or 0
        if is_postpay:
            self.is_postpay = True
        self.save(update_fields=['stage', 'status', 'is_postpay'])

    def set_stage_receive(self):
        self.stage = OrderList.STAGE_RECEIVE
        self.status = OrderList.QUESTION_OF_QUANTITY
        self.save(update_fields=['stage', 'status'])

    def set_stage_state(self):
        self.stage = OrderList.STAGE_STATE
        self.status = OrderList.TO_BE_PAID
        self.save(update_fields=['stage', 'status'])

    def set_stage_complete(self):
        self.stage = OrderList.STAGE_STATE
        self.status = OrderList.CLOSED
        self.save(update_fields=['stage', 'status'])

    def set_stage_delete(self):
        self.stage = OrderList.STAGE_DELETED
        self.status = OrderList.ZUOFEI
        self.save(update_fields=['stage', 'status'])

    def get_receive_status(self):
        if self.lack is None:
            return u'未到货'
        if self.lack and not self.inferior:
            info = u'缺货'
        elif self.lack and self.inferior:
            info = u'次品又缺货'
        elif self.inferior:
            info = u'有次品'
        else:
            info = u'完成'
        return info

    def update_stage(self):
        if self.stage == OrderList.STAGE_RECEIVE:
            self.set_stat()
            if self.lack is False:
                self.set_stage_state()
        elif self.stage == OrderList.STAGE_STATE:
            if self.lack is False and not self.is_postpay:
                self.set_stage_complete()



def check_with_purchase_order(sender, instance, created, **kwargs):
    if not created:
        return


post_save.connect(
    check_with_purchase_order,
    sender=OrderList,
    dispatch_uid='post_save_check_with_purchase_order')


def order_list_update_stage(sender, instance, created, **kwargs):
    if instance.stage in [OrderList.STAGE_RECEIVE, OrderList.STAGE_STATE]:
        from flashsale.dinghuo.tasks import task_orderlist_update_self
        task_orderlist_update_self.delay(instance)


post_save.connect(
    order_list_update_stage,
    sender=OrderList,
    dispatch_uid='post_save_update_stage')


def update_orderdetail_relationship(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.purchase_order_unikey:
        OrderDetail.objects.filter(purchase_order_unikey=instance.purchase_order_unikey).update(orderlist=instance)


post_save.connect(update_orderdetail_relationship, sender=OrderList,
                  dispatch_uid='post_save_update_orderdetail_relationship')


def update_purchaseorder_status(sender, instance, created, **kwargs):
    from flashsale.dinghuo.models_purchase import PurchaseOrder
    status = None
    if instance.is_open():
        status = PurchaseOrder.OPEN
    elif instance.is_booked():
        status = PurchaseOrder.BOOKED
    elif instance.is_finished():
        status = PurchaseOrder.FINISHED
    elif instance.is_canceled():
        status = PurchaseOrder.CANCELED
    else:
        return

    po = PurchaseOrder.objects.filter(uni_key=instance.purchase_order_unikey).first()
    if po and po.status != status:
        po.status = status
        po.save(update_fields=['status', 'modified'])

        from flashsale.dinghuo.tasks import task_update_purchasedetail_status, \
            task_update_purchasearrangement_initial_book, task_update_purchasearrangement_status

        task_update_purchasedetail_status.delay(po)
        if status == PurchaseOrder.BOOKED:
            task_update_purchasearrangement_initial_book.delay(po)
        else:
            task_update_purchasearrangement_status.delay(po)


post_save.connect(update_purchaseorder_status, sender=OrderList, dispatch_uid='post_save_update_purchaseorder_status')


class OrderDetail(models.Model):
    id = models.AutoField(primary_key=True)
    orderlist = models.ForeignKey(OrderList, null=True,
                                  related_name='order_list',
                                  verbose_name=u'订单编号')
    product_id = models.CharField(db_index=True,
                                  max_length=32,
                                  verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32,
                                db_index=True,
                                verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32,
                                 db_index=True,
                                 verbose_name=u'规格id')
    product_chicun = models.CharField(max_length=100, verbose_name=u'产品尺寸')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'正品数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')
    non_arrival_quantity = models.IntegerField(default=0, verbose_name=u'未到数量')

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True,
                                   verbose_name=u'生成日期')  # index
    updated = models.DateTimeField(auto_now=True,
                                   db_index=True,
                                   verbose_name=u'更新日期')  # index
    arrival_time = models.DateTimeField(blank=True,
                                        null=True,
                                        db_index=True,
                                        verbose_name=u'到货时间')

    purchase_detail_unikey = models.CharField(max_length=32, null=True, unique=True,
                                              verbose_name='PurchaseDetailUniKey')
    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True,
                                             verbose_name='PurchaseOrderUnikey')

    class Meta:
        db_table = 'suplychain_flashsale_orderdetail'
        app_label = 'dinghuo'
        verbose_name = u'订货明细表'
        verbose_name_plural = u'订货明细表'
        permissions = [('change_orderdetail_quantity', u'修改订货明细数量')]

    def __unicode__(self):
        return self.product_id

    @property
    def not_arrival_quantity(self):
        """ 未到数量 """
        return self.buy_quantity - self.arrival_quantity - self.inferior_quantity

    @property
    def need_arrival_quantity(self):
        """ 未到数量 """
        return max(self.buy_quantity - self.arrival_quantity, 0)

    @property
    def sku(self):
        return ProductSku.objects.get(id=self.chichu_id)

    @property
    def product(self):
        return Product.objects.get(id=self.product_id)

    def get_receive_status(self):
        if self.buy_quantity == self.arrival_quantity:
            return u'完成'
        if self.buy_quantity > self.arrival_quantity:
            return u'缺货'
        if self.buy_quantity < self.arrival_quantity:
            return u'超额'


def orderlist_create_forecast_inbound(sender, instance, raw, **kwargs):
    """ 根据status更新sys_status,审核通过后更新预测到货单  """

    if instance.status == OrderList.SUBMITTING:
        instance.sys_status = OrderList.ST_DRAFT
    elif instance.status == OrderList.ZUOFEI:
        instance.sys_status = OrderList.ST_CLOSE
    elif instance.status == OrderList.CLOSED:
        instance.sys_status = OrderList.ST_FINISHED
    else:
        instance.sys_status = OrderList.ST_APPROVAL
    update_model_fields(instance, update_fields=['sys_status'])

    real_orderlist = OrderList.objects.filter(id=instance.id).first()
    if real_orderlist and instance.status == OrderList.APPROVAL:
        # if the orderlist purchase confirm, then create forecast inbound
        from flashsale.forecast.apis import api_create_or_update_forecastinbound_by_orderlist
        try:
            with transaction.atomic():
                api_create_or_update_forecastinbound_by_orderlist(instance)
        except Exception, exc:
            logger.error('update forecast inbound:%s' % exc.message, exc_info=True)


post_save.connect(
    orderlist_create_forecast_inbound,
    sender=OrderList,
    dispatch_uid='pre_save_orderlist_create_forecast_inbound')


def update_productskustats_inbound_quantity(sender, instance, created,
                                            **kwargs):
    # Note: chichu_id is actually the id of related ProductSku record.
    from flashsale.dinghuo.tasks import task_orderdetail_update_productskustats_inbound_quantity
    task_orderdetail_update_productskustats_inbound_quantity.delay(
        instance.chichu_id)


post_save.connect(
    update_productskustats_inbound_quantity,
    sender=OrderDetail,
    dispatch_uid='post_save_update_productskustats_inbound_quantity')


def update_orderlist(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_orderdetail_update_orderlist
    task_orderdetail_update_orderlist.delay(instance)

post_save.connect(update_orderlist, sender=OrderDetail, dispatch_uid='post_save_update_orderlist')


class OrderGuarantee(BaseModel):
    purchase_order = models.ForeignKey(OrderList, related_name='guarantees', verbose_name=u'订货单')
    desc = models.CharField(max_length=100, default='')

class orderdraft(models.Model):
    buyer_name = models.CharField(default="None",
                                  max_length=32,
                                  verbose_name=u'买手')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(default="",
                                      max_length=20,
                                      verbose_name=u'产品尺寸')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    created = models.DateField(auto_now_add=True, verbose_name=u'生成日期')

    class Meta:
        db_table = 'suplychain_flashsale_orderdraft'
        app_label = 'dinghuo'
        verbose_name = u'草稿表'
        verbose_name_plural = u'草稿表'

    def __unicode__(self):
        return self.product_name


class ProductSkuDetail(models.Model):
    product_sku = models.BigIntegerField(unique=True, verbose_name=u'库存商品规格')
    exist_stock_num = models.IntegerField(default=0, verbose_name=u'上架前库存')
    sample_num = models.IntegerField(default=0, verbose_name=u'样品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'flash_sale_product_sku_detail'
        app_label = 'dinghuo'
        verbose_name = u'特卖商品库存'
        verbose_name_plural = u'特卖商品库存列表'

    def __unicode__(self):
        return u'<%s>' % (self.product_sku)


from shopback import signals


def init_stock_func(sender, product_list, *args, **kwargs):
    import datetime
    from django.db.models import Sum
    today = datetime.date.today()

    for pro_bean in product_list:
        sku_qs = pro_bean.prod_skus.all()
        for sku_bean in sku_qs:
            total_num = OrderDetail.objects.filter(
                chichu_id=sku_bean.id,
                orderlist__created__range=
                (today - datetime.timedelta(days=7), today)).exclude(
                orderlist__status=OrderList.ZUOFEI).aggregate(
                total_num=Sum('arrival_quantity')).get('total_num') or 0
            pro_sku_beans = ProductSkuDetail.objects.get_or_create(
                product_sku=sku_bean.id)
            pro_sku_bean = pro_sku_beans[0]
            result_num = sku_bean.quantity - sku_bean.wait_post_num - total_num
            pro_sku_bean.exist_stock_num = result_num if result_num > 0 else 0
            pro_sku_bean.sample_num = 0
            sku_bean.memo = ""
            sku_bean.save()
            pro_sku_bean.save()


signals.signal_product_upshelf.connect(init_stock_func, sender=Product)


class ReturnGoods(models.Model):
    CREATE_RG = 0
    VERIFY_RG = 1
    OBSOLETE_RG = 2
    DELIVER_RG = 3
    REFUND_RG = 31
    SUCCEED_RG = 4
    FAILED_RG = 5
    MEMO_DEFAULT = u'\u6536\u4ef6\u4eba:\r\n\u624b\u673a/\u7535\u8bdd:\r\n\u6536\u4ef6\u5730\u5740:'
    RG_STATUS = ((CREATE_RG, u"新建"), (VERIFY_RG, u"已审核"), (OBSOLETE_RG, u"已作废"),
                 (DELIVER_RG, u"已发货"), (REFUND_RG, u"待验退款"),
                 (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))
    product_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u"退货商品id")
    # supplier_id = models.IntegerField(db_index=True, verbose_name=u"供应商id")
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u"供应商")
    return_num = models.IntegerField(default=0, verbose_name=u"退件总数")
    sum_amount = models.FloatField(default=0.0, verbose_name=u"计划退款总额")
    plan_amount = models.FloatField(default=0.0, verbose_name=u"计划退款总额")
    real_amount = models.FloatField(default=0.0, verbose_name=u"实际退款额")
    # confirm_pic_url = models.FileField(blank=True, verbose_name=u"付款截图")
    confirm_pic_url = models.URLField(blank=True, verbose_name=u"付款截图")
    upload_time = models.DateTimeField(null=True, verbose_name=u"上传截图时间")
    refund_fee = models.FloatField(default=0.0, verbose_name=u"客户退款额")
    confirm_refund = models.BooleanField(default=False, verbose_name=u"退款额确认")
    refund_confirmer_id = models.IntegerField(default=None, null=True, verbose_name=u"退款额确认人")
    transactor_id = models.IntegerField(default=None, null=True, db_index=True, verbose_name=u"处理人id")
    # transactor_id = models.IntegerField(choices=[(i.id, i.username) for i in return_goods_transcations()], default=None,
    #                                     null=True, db_index=True, verbose_name=u"处理人id")
    # transactor = models.ForeignKey(User, choices=ReturnGoods.transactors, null=True, verbose_name=u"处理人id")
    transaction_number = models.CharField(default='', max_length=64, verbose_name=u"交易单号")
    noter = models.CharField(max_length=32, verbose_name=u"录入人")
    consigner = models.CharField(max_length=32, blank=True, verbose_name=u"发货人")

    consign_time = models.DateTimeField(blank=True, null=True, verbose_name=u'发货时间')
    sid = models.CharField(max_length=64, null=True, blank=True, verbose_name=u"发货物流单号")
    logistics_company_id = models.BigIntegerField(null=True, verbose_name='物流公司ID')
    # logistics_company = models.ForeignKey(LogisticsCompany, null=True, blank=True, verbose_name=u'物流公司')
    status = models.IntegerField(default=0, choices=RG_STATUS, db_index=True, verbose_name=u"状态")

    type = models.IntegerField(default=0, choices=((0, u'普通退货'), (1, u'未入库退货')), verbose_name=u'退货类型')
    REFUND_STATUS = ((0, u"未付"), (1, u"已完成"), (2, u"部分支付"), (3, u"已关闭"))
    refund_status = models.IntegerField(default=0, choices=REFUND_STATUS, db_index=True, verbose_name=u"退款状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=512,
                            blank=True,
                            default=MEMO_DEFAULT,
                            verbose_name=u"退货备注")

    class Meta:
        db_table = 'flashsale_dinghuo_returngoods'
        app_label = 'dinghuo'
        verbose_name = u'仓库退货单'
        verbose_name_plural = u'仓库退货单列表'

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['skuid'] for i in self.rg_details.values('skuid')]
        return self._sku_ids_

    @property
    def product_skus(self):
        if not hasattr(self, '_product_skus_'):
            self._product_skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._product_skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(prod_skus__id__in=self.sku_ids).distinct()
        return self._products_

    @property
    def logistics_company(self):
        if not hasattr(self, '_logistics_company_'):
            from shopback.logistics.models import LogisticsCompany
            self._logistics_company_ = LogisticsCompany.objects.get(id=self.logistics_company_id)
        return self._logistics_company_

    @property
    def transactor(self):
        if not hasattr(self, '_transactor_'):
            self._transactor_ = User.objects.get(id=self.transactor_id)
        return self._transactor_

    def products_item_sku(self):
        products = self.products
        for sku in self.product_skus:
            for product in products:
                if sku.product_id == product.id:
                    if not hasattr(product, 'detail_skus'):
                        product.detail_skus = []
                    product.detail_skus.append(sku)
                    break
                    continue
        for product in products:
            product.detail_sku_ids = [sku.id for sku in product.detail_skus]
            product.detail_length = len(product.detail_sku_ids)
        for detail in self.rg_details.all():
            for product in products:
                if detail.skuid in product.detail_sku_ids:
                    if not hasattr(product, 'detail_items'):
                        product.detail_items = []
                    product.detail_items.append(detail)
        return products

    @staticmethod
    def generate(sku_dict, noter):
        """
            产生sku
        :param sku_dict:
        :param noter:
        :return:
        """
        product_sku_dict = dict([(p.id, p) for p in ProductSku.objects.filter(id__in=sku_dict.keys())])
        supplier = {}
        for sku_id in product_sku_dict:
            if sku_dict[sku_id] > 0 and \
                    ReturnGoods.can_return(sku=sku_id):
                sku = product_sku_dict[sku_id]
                # if sku.product.offshelf_time<datetime.datetime.now()- datetime.timedelta(days=12):
                detail = RGDetail(
                    skuid=sku_id,
                    num=sku_dict[sku_id],
                    price=sku.cost,
                )
                supplier_id = sku.product.sale_product_item.sale_supplier_id
                if supplier_id not in supplier:
                    supplier[supplier_id] = []
                supplier[supplier_id].append(detail)
        res = []
        for supplier_id in supplier:
            if ReturnGoods.can_return(supplier_id=supplier_id):
                rg_details = supplier[supplier_id]

                rg = ReturnGoods(supplier_id=supplier_id,
                                 noter=noter,
                                 return_num=sum([d.num for d in rg_details]),
                                 sum_amount=sum([d.num * d.price for d in rg_details])
                                 )
                rg.transactor_id = ReturnGoods.get_user_by_supplier(supplier_id)
                rg.save()
                details = []
                for detail in supplier[supplier_id]:
                    detail.return_goods = rg
                    detail.return_goods_id = rg.id
                    details.append(detail)
                RGDetail.objects.bulk_create(details)
                res.append(rg)
        return res

    @staticmethod
    def generate_by_inbound(inbound, noter):
        if not inbound.wrong and not inbound.out_stock:
            raise Exception(u'此入库单无错货多货无法生成退货单')
        supplier_id = inbound.supplier_id
        rg_details = []
        for detail in inbound.details.filter(Q(out_stock=True) or Q(inferior_quantity__gt=0)):
            rg_detail = RGDetail(
                skuid=detail.sku_id,
                num=detail.out_stock_cnt,
                inferior_num=detail.inferior_quantity,
                price=0
            )
            rg_details.append(rg_detail)
            rg_details.append(rg_detail)
        rg = ReturnGoods(supplier_id=supplier_id,
                         noter=noter,
                         return_num=sum([d.num for d in rg_details]),
                         sum_amount=sum([d.num * d.price for d in rg_details]),
                         type=1
                         )
        rg.save()
        details = []
        for detail in rg_details:
            detail.return_goods = rg
            detail.return_goods_id = rg.id
            details.append(detail)
        RGDetail.objects.bulk_create(details)
        return rg

    @staticmethod
    def can_return(supplier_id=None, sku=None):
        """
            近七天内没有有效退货单
            且    RG_STATUS = ((CREATE_RG, u"新建"), (VERIFY_RG, u"已审核"), (OBSOLETE_RG, u"已作废"),
                 (DELIVER_RG, u"已发货"), (REFUND_RG, u"待验退款"),
                 (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))
            不在不可退货商品列表中
        :param supplier_id:
        :return:
        """
        # if supplier_id:
        #     return not ReturnGoods.objects.filter(created__gt=datetime.datetime.now() - datetime.timedelta(days=7),
        #                                           supplier_id=supplier_id,
        #                                           status__in=[ReturnGoods.CREATE_RG, ReturnGoods.VERIFY_RG,
        #                                                       ReturnGoods.DELIVER_RG, ReturnGoods.REFUND_RG,
        #                                                       ReturnGoods.SUCCEED_RG]).exists()

        if sku:
            not_in_unreturn = not UnReturnSku.objects.filter(sku_id=sku, status=UnReturnSku.EFFECT).exists()
            not_onshelf = datetime.datetime.now() < ProductSku.objects.get(
                id=sku).product.offshelf_time < datetime.datetime.now() + datetime.timedelta(days=7)
            return not_in_unreturn and not_onshelf

        if supplier_id:
            supplier = SaleSupplier.objects.get(id=supplier_id)
            sale_product_ids = [i["id"] for i in supplier.supplier_products.values("id")]
            product_ids = [p["id"] for p in Product.objects.filter(id__in=sale_product_ids).values("id")]
            unreturn_sku_ids = [i["id"] for i in supplier.unreturnsku_set.values("sku_id")]
            return ProductSkuStats.objects.filter(product__id__in=product_ids,
                                                  product__offshelf_time__lt=datetime.datetime.now() - datetime.timedelta(
                                                      days=15),
                                                  sold_num__lt=F('history_quantity') + F('inbound_quantity') + F(
                                                      'return_quantity') \
                                                               - F('rg_quantity')).exclude(
                sku__id__in=unreturn_sku_ids).exists()

    @staticmethod
    def get_user_by_supplier(supplier_id):
        r = OrderList.objects.filter(supplier_id=supplier_id).values('buyer_id').annotate(s=Count('buyer_id'))

        def get_max_from_list(l):
            max_i = 0
            buyer_id = None
            for i in l:
                if i['s'] > max_i:
                    max_i = i['s']
                    buyer_id = i['buyer_id']
            return buyer_id

        return get_max_from_list(r)

    def set_stat(self):
        self.rg_details.filter(num=0).delete()
        rgds = self.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_num = total_num
        self.sum_amount = total_amount
        self.save()

    def has_sent(self):
        return self.status >= ReturnGoods.DELIVER_RG and not self.status == ReturnGoods.FAILED_RG

    def has_refund(self):
        return self.status in [ReturnGoods.REFUND_RG, ReturnGoods.SUCCEED_RG]

    def set_transactor(self, transactor):
        self.transactor_id = User.objects.get(username=transactor).id
        self.save()

    def delivery_by(self, logistics_no, logistics_company_id, consigner):
        self.sid = logistics_no
        self.logistics_company_id = logistics_company_id
        self.consigner = consigner
        self.consign_time = datetime.datetime.now()
        self.status = ReturnGoods.DELIVER_RG
        self.save()
        for d in self.rg_details.all():
            ProductSku.objects.filter(id=d.skuid).update(quantity=F('quantity') - d.num)

    def supply_notify_refund(self, receive_method, amount, note='', pic=None):
        """
            供应商说他已经退款了
        :return:
        """
        from flashsale.finance.models import Bill
        bill = Bill(type=Bill.RECEIVE,
                    status=0,
                    creater=self.transactor,
                    pay_method=receive_method,
                    plan_amount=amount,
                    note=note,
                    supplier_id=self.supplier_id)
        if pic:
            bill.attachment = pic
        bill.save()
        bill.relate_to([self])
        self.status = ReturnGoods.REFUND_RG
        self.save()
        return bill

    def set_confirm_refund_status(self, refund_status=u'已完成'):
        self.refund_status = dict([(r[1], r[0]) for r in ReturnGoods.REFUND_STATUS]).get(refund_status, 0)
        if self.refund_status == 1:
            self.status = ReturnGoods.REFUND_RG
        self.save()

    def set_failed(self):
        self.status = ReturnGoods.FAILED_RG
        rd = self.rg_details.all()
        for item in rd:
            skuid = item.skuid
            num = item.num
            inferior_num = item.inferior_num
            ProductSku.objects.filter(id=skuid).update(quantity=F('quantity') + num,
                                                       sku_inferior_num=F('sku_inferior_num') + inferior_num)
            self.save()
        return

    # def set_fail_closed(self):
    #     self.status = ReturnGoods.FAILED_RG
    #     self.save()

    @staticmethod
    def transactors():
        return User.objects.filter(is_staff=True,
                                   groups__name__in=(u'小鹿买手资料员', u'小鹿采购管理员', u'小鹿采购员', u'管理员', u'小鹿管理员')). \
            distinct().order_by('id')

    def add_sku(self, skuid, num, price=None):
        from shopback.items.models import ProductSku
        sku = ProductSku.objects.get(id=skuid)
        if self.status in [self.CREATE_RG, self.VERIFY_RG]:
            rgd = self.rg_details.filter(skuid=skuid).first()
            if rgd:
                rgd.num += num
                if price:
                    rgd.price = price
                rgd.save()
            else:
                rgd = RGDetail()
                rgd.return_goods = self
                rgd.skuid = skuid
                rgd.num = num
                rgd.price = price or sku.cost
                rgd.save()
        else:
            raise Exception(u'已发货的退货单不可更改')

    @property
    def pay_choices(self):
        from flashsale.finance.models import Bill
        return [{'value': x, 'text': y} for x, y in Bill.PAY_CHOICES]

    @property
    def bill(self):
        from flashsale.finance.models import BillRelation
        bill_relation = BillRelation.objects.filter(type=3, object_id=self.id).order_by('-id').first()
        if not bill_relation:
            return None
        return bill_relation.bill

    def __unicode__(self):
        return u'<%s,%s>' % (self.supplier_id, self.id)

    @property
    def bill_relation_dict(self):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe
        return {
            # 'payinfo': mark_safe(render_to_string('dinghuo/returngoods_payinfo.html', {'memo': self.memo, 'sum_amount': self.sum_amount})),
            'object_id': self.id,
            'payinfo': self.memo,
            'object_url': '/admin/dinghuo/returngoods/%d/' % self.id,
            'amount': self.sum_amount
        }

    def deal(self, confirm_pic_url):
        self.confirm_pic_url = confirm_pic_url
        self.status = self.REFUND_RG
        self.save()

    def confirm(self):
        self.status = self.SUCCEED_RG
        self.save()


def update_product_sku_stat_rg_quantity(sender, instance, created, **kwargs):
    from shopback.items.models_stats import PRODUCT_SKU_STATS_COMMIT_TIME
    if instance.created >= PRODUCT_SKU_STATS_COMMIT_TIME and instance.status in [
        ReturnGoods.REFUND_RG, ReturnGoods.DELIVER_RG,
        ReturnGoods.SUCCEED_RG
    ]:
        from flashsale.dinghuo.tasks import task_update_product_sku_stat_rg_quantity
        for rg in instance.rg_details.all():
            task_update_product_sku_stat_rg_quantity.delay(rg.skuid)


post_save.connect(update_product_sku_stat_rg_quantity,
                  sender=ReturnGoods,
                  dispatch_uid='post_save_update_product_sku_stat_rg_quantity')


class RGDetail(models.Model):
    skuid = models.BigIntegerField(db_index=True, verbose_name=u"退货商品skuid")
    return_goods = models.ForeignKey(ReturnGoods,
                                     related_name='rg_details',
                                     verbose_name=u'退货单信息')
    num = models.IntegerField(default=0, verbose_name=u"正品退货数量")
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品退货数量")
    price = models.FloatField(default=0.0, verbose_name=u"退回价格")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'flashsale_dinghuo_rg_detail'
        app_label = 'dinghuo'
        verbose_name = u'商品库存退货明细表'
        verbose_name_plural = u'商品库存退货明细列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.skuid, self.return_goods)

    def sync_rg_field(self):
        rgds = self.return_goods.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_goods.return_num = total_num
        self.return_goods.sum_amount = total_amount
        self.return_goods.save()

    @property
    def product_sku(self):
        return ProductSku.objects.get(id=self.skuid)

    @staticmethod
    def get_return_inferior_num_total(sku_id):
        from shopback.items.models_stats import PRODUCT_SKU_STATS_COMMIT_TIME
        res = RGDetail.objects.filter(skuid=sku_id, created__gt=PRODUCT_SKU_STATS_COMMIT_TIME,
                                      return_goods__status__in=[ReturnGoods.DELIVER_RG, ReturnGoods.REFUND_RG,
                                                                ReturnGoods.SUCCEED_RG, ]).aggregate(
            n=Sum("inferior_num")).get('n', 0)
        return res or 0


def sync_rgd_return(sender, instance, created, **kwargs):
    instance.return_goods.set_stat()


post_save.connect(sync_rgd_return, sender=RGDetail, dispatch_uid='post_save_sync_rgd_return')


class UnReturnSku(BaseModel):
    EFFECT = 1
    INVALIED = 2
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u"供应商")
    sale_product = models.ForeignKey(SaleProduct, null=True, verbose_name=u"供应商")
    product = models.ForeignKey(Product, null=True, verbose_name=u"商品")
    sku = models.ForeignKey(ProductSku, null=True, verbose_name=u"sku")
    creater = models.ForeignKey(User, verbose_name=u'创建人')
    status = models.IntegerField(choices=((EFFECT, u'有效'), (INVALIED, u'无效')), default=0, verbose_name=u'状态')
    reason = models.IntegerField(choices=((1, u'保护商品'), (2, u'商家不许退货'), (3, u'其它原因')),
                                 default=2, verbose_name=u'不可退货原因')

    class Meta:
        db_table = 'flashsale_dinghuo_unreturn_sku'
        app_label = 'dinghuo'
        verbose_name = u'不可退货商品明细表'
        verbose_name_plural = u'不可退货商品明细列表'


class SaleInventoryStat(models.Model):
    """
    （只统计小鹿特卖商品）统计当天的订货表的新增采购数，未到货总数，到货数，发出件数，总库存数
    """
    CHILD = 1
    FEMALE = 2

    INVENTORY_CATEGORY = ((CHILD, u'童装'), (FEMALE, u'女装'))
    newly_increased = models.IntegerField(default=0, verbose_name=u'新增采购数')
    not_arrive = models.IntegerField(default=0, verbose_name=u'未到货数')
    arrived = models.IntegerField(default=0, verbose_name=u'到货数')
    deliver = models.IntegerField(default=0, verbose_name=u'发出数')
    inventory = models.IntegerField(default=0, verbose_name=u'库存')
    category = models.IntegerField(blank=True,
                                   null=True,
                                   db_index=True,
                                   choices=INVENTORY_CATEGORY,
                                   verbose_name=u'分类')
    stat_date = models.DateField(verbose_name=u'统计日期')

    class Meta:
        db_table = 'flashsale_inventory_stat'
        app_label = 'dinghuo'
        verbose_name = u'特卖入库及库存每日统计'
        verbose_name_plural = u'特卖入库及库存每日统计列表'

    def __unicode__(self):
        return u'<%s>' % self.stat_date


class InBound(models.Model):
    INVALID = 0
    PENDING = 1
    WAIT_CHECK = 2
    COMPLETED = 3
    COMPLETE_RETURN = 4

    SUPPLIER = 1
    REFUND = 2

    STATUS_CHOICES = ((INVALID, u'作废'),
                      (PENDING, u'待分配'),
                      (WAIT_CHECK, u'待质检'),
                      (COMPLETED, u'已入库'),
                      (COMPLETE_RETURN, u'已完结'))
    supplier = models.ForeignKey(SaleSupplier,
                                 null=True,
                                 blank=True,
                                 related_name='inbounds',
                                 verbose_name=u'供应商')
    express_no = models.CharField(max_length=32,
                                  verbose_name=u'快递单号')
    ori_orderlist_id = models.CharField(max_length=32, default='',
                                        verbose_name=u'订货单号')
    sent_from = models.SmallIntegerField(
        default=SUPPLIER,
        choices=((SUPPLIER, u'供应商'), (REFUND, u'退货')),
        verbose_name=u'包裹类型')
    refund = models.ForeignKey(Refund,
                               null=True,
                               blank=True,
                               related_name='inbounds',
                               verbose_name=u'退货单')
    creator = models.ForeignKey(User,
                                related_name='inbounds',
                                verbose_name=u'创建人')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(default=PENDING,
                                      choices=STATUS_CHOICES,
                                      verbose_name=u'进度')
    images = JSONCharMyField(max_length=10240,
                             blank=True,
                             default='[]',
                             verbose_name=u'图片')
    orderlist_ids = JSONCharMyField(max_length=10240,
                                    blank=True,
                                    default='[]',
                                    verbose_name=u'订货单ID',
                                    help_text=u'冗余的订货单关联')
    forecast_inbound_id = models.IntegerField(null=True, db_index=True, verbose_name=u'关联预测单ID')
    checked = models.BooleanField(default=False, verbose_name=u"是否质检")
    check_time = models.DateTimeField(null=True, verbose_name=u"检查时间")
    wrong = models.BooleanField(default=False, verbose_name=u"是否错货")
    out_stock = models.BooleanField(default=False, verbose_name=u"是否多货")

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'

    def __unicode__(self):
        return str(self.id)

    def assign_to_order_detail(self, orderlist_id, orderlist_ids):
        return {}
        orderlist_ids = [x for x in orderlist_ids if x != orderlist_id]
        inbound_skus = dict([(inbound_detail.sku_id,
                              inbound_detail.arrival_quantity)
                             for inbound_detail in self.details.all()])
        order_details_first = OrderDetail.objects.filter(
            orderlist_id=orderlist_id,
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = OrderDetail.objects.filter(
            orderlist_id__in=list(orderlist_ids),
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = list(order_details)
        order_details = list(order_details_first) + order_details
        assign_dict = {}
        for order_detail in order_details:
            if order_detail.not_arrival_quantity < inbound_skus.get(
                    order_detail.chichu_id, 0):
                order_detail.arrival_quantity += order_detail.not_arrival_quantity
                inbound_skus[
                    order_detail.chichu_id] -= order_detail.not_arrival_quantity
                assign_dict[order_detail.id] = order_detail.not_arrival_quantity
                # order_detail.save()
            else:
                order_detail.arrival_quantity += inbound_skus.get(
                    order_detail.chichu_id, 0)
                inbound_skus[order_detail.chichu_id] = 0
                assign_dict[order_detail.id] = inbound_skus.get(
                    order_detail.chichu_id, 0)
        return assign_dict

    def allocate(self, data):
        request_all_sku = {}
        for orderdetail_id in data:
            orderdetail = OrderDetail.objects.get(id=orderdetail_id)
            request_all_sku[int(orderdetail.chichu_id)] = request_all_sku.get(int(orderdetail.chichu_id), 0) + data[
                orderdetail_id]
        sku_data = self.sku_data
        for sku_id in request_all_sku:
            if request_all_sku.get(sku_id, 0) > sku_data[sku_id]:
                raise Exception(u'分配数不能超出总数')
        for orderdetail_id in data:
            orderdetail = OrderDetail.objects.get(id=orderdetail_id)
            OrderDetailInBoundDetail.create(orderdetail, self, data[orderdetail_id])
        self.status = InBound.WAIT_CHECK
        self.set_stat()
        self.save()

    def notify_forecast_save_or_update_inbound(self):
        from flashsale.forecast.apis import api_create_or_update_realinbound_by_inbound
        api_create_or_update_realinbound_by_inbound.delay(self.id)

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['sku_id'] for i in self.details.values('sku_id')]
        return self._sku_ids_

    @property
    def product_ids(self):
        if not hasattr(self, '_product_ids_'):
            self._product_ids_ = [i['product_id'] for i in self.details.values('product_id').distinct()]
        return self._product_ids_

    @property
    def product_skus(self):
        if not hasattr(self, '_product_skus_'):
            self._product_skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._product_skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(id__in=self.product_ids)
        return self._products_

    @property
    def order_detail_ids(self):
        if not hasattr(self, '_order_detail_ids_'):
            query = OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound__id=self.id).values('orderdetail_id')
            self._order_detail_ids_ = [item['orderdetail_id'] for item in query]
        return self._order_detail_ids_

    @property
    def order_details(self):
        if not hasattr(self, '_order_details_'):
            self._order_details_ = OrderDetail.objects.filter(id__in=self.order_detail_ids)
        return self._order_details_

    @property
    def order_list_ids(self):
        if not hasattr(self, '_order_list_ids_'):
            query = OrderDetail.objects.filter(id__in=self.order_detail_ids).values('orderlist_id').distinct()
            self._order_list_ids_ = [item['orderlist_id'] for item in query]
        return self._order_list_ids_

    @property
    def order_lists(self):
        if not hasattr(self, '_order_lists_'):
            self._order_lists_ = OrderList.objects.filter(id__in=self.order_list_ids)
        return self._order_lists_

    @property
    def order_list_items(self):
        cache_orderlist = {}
        cache_product = {}
        res = []
        for od in self.order_details:
            if od.orderlist_id not in cache_orderlist:
                cache_orderlist[od.orderlist_id] = od.orderlist
            ol = cache_orderlist[od.orderlist_id]
            if ol not in res:
                ol.inbound_products = []
                res.append(ol)
            if od.product_id not in cache_product:
                cache_product[od.product_id] = od.product
            product = cache_product[od.product_id]
            if product not in ol.inbound_products:
                product.inbound_orderdetails = [od]
                ol.inbound_products.append(product)
            else:
                product.inbound_orderdetails.append(od)
        for ol in res:
            ol.rows = sum([len(p.inbound_orderdetails) for p in ol.inbound_products])
        return res

    def get_order_list_items_dict(self):
        order_list_items = self.order_list_items
        return order_list_items

    @property
    def sku_data(self):
        return {item['sku_id']: item['arrival_quantity'] + item['inferior_quantity']
                for item in self.details.values('sku_id', 'arrival_quantity', 'inferior_quantity')}

    def all_skus(self):
        orderlist_ids = self.get_may_allocate_order_list_ids()
        query = OrderDetail.objects.filter(orderlist_id__in=orderlist_ids).values('chichu_id').distinct()
        return [int(item['chichu_id']) for item in query]

    def get_set_status_info(self):
        if self.set_stat():
            self.save()
        info = u''
        if self.wrong:
            info += u'有错货'
        if self.out_stock:
            info += u'有多货'
        all_inferior_quantity = self.all_inferior_quantity
        if all_inferior_quantity:
            info += u'有%d件次品' % all_inferior_quantity
        return info

    def get_may_allocate_order_list_ids(self):
        query = OrderDetail.objects.filter(orderlist__supplier_id=self.supplier_id, chichu_id__in=self.sku_ids).exclude(
            orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED,
                                   OrderList.TO_PAY, OrderList.SUBMITTING]).values('orderlist_id').distinct()
        return [item['orderlist_id'] for item in query]

    def may_allocate_order_list_items(inbound):
        orderlist_ids = inbound.get_may_allocate_order_list_ids()
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}
        sku_data = inbound.sku_data

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': orderlist.get_buyer_name(),
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }

        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):
            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)

            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})

            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'arrival_quantity': orderdetail.arrival_quantity,
                'inferior_quantity': orderdetail.inferior_quantity,
                'all_quantity': orderdetail.inferior_quantity + orderdetail.arrival_quantity,
                'orderdetail_id': orderdetail.id,
                'in_inbound': sku_id in sku_data
            }

        saleproduct_ids = set()
        products_dict = {}
        for product in Product.objects.filter(id__in=list(product_ids)):
            products_dict[product.id] = {
                'id': product.id,
                'name': product.name,
                'saleproduct_id': product.sale_product,
                'outer_id': product.outer_id,
                'pic_path': product.pic_path,
                'ware_by': product.ware_by,
                'product_link': product.get_product_link()
            }
            saleproduct_ids.add(product.sale_product)

        skus_dict = {}
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            skus_dict[sku.id] = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'is_inbound': 1
            }

        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link
            }

        orderlists = []
        for orderlist_id in sorted(orderlists_dict.keys()):
            orderlist_dict = orderlists_dict[orderlist_id]
            orderlist_products_dict = orderlist_dict['products']
            orderlist_products = []
            len_of_skus = 0
            for product_id in sorted(orderlist_products_dict.keys()):
                product_dict = copy.copy(products_dict[product_id])
                product_dict.update(saleproducts_dict.get(product_dict['saleproduct_id']) or {})
                orderlist_skus_dict = orderlist_products_dict[product_id]
                for sku_id in sorted(orderlist_skus_dict.keys()):
                    len_of_skus += 1
                    sku_dict = orderlist_skus_dict[sku_id]
                    sku_dict.update(skus_dict[sku_id])
                    product_dict.setdefault('skus', []).append(sku_dict)
                orderlist_products.append(product_dict)
            orderlist_dict['orderlist_id'] = orderlist_id
            orderlist_dict['products'] = orderlist_products
            orderlist_dict['len_of_skus'] = len_of_skus
            orderlists.append(orderlist_dict)
        return orderlists

    def get_allocate_order_details_dict(self):
        # if self.is_allocated():
        #     orderlist_ids = self.order_list_ids
        # else:
        orderlist_ids = self.get_may_allocate_order_list_ids()
        orderlists_dict = {}
        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': orderlist.get_buyer_name(),
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': orderlist.get_status_display(),
                'products': []
            }
            cache_products = {}
            for orderdetail in orderlist.order_list.all().order_by('id'):
                product = orderdetail.product
                sku = orderdetail.sku
                if orderdetail.product_id in cache_products:
                    product_dict = cache_products.get(orderdetail.product_id)
                else:
                    product_dict = {'id': product.id,
                                    'name': product.name,
                                    'saleproduct_id': product.sale_product,
                                    'outer_id': product.outer_id,
                                    'pic_path': product.pic_path,
                                    'ware_by': product.ware_by,
                                    'skus': []
                                    }
                sku_dict = {
                    'orderdetail_id': orderdetail.id,
                    'buy_quantity': orderdetail.buy_quantity,
                    'plan_quantity': orderdetail.need_arrival_quantity,
                    'arrival_quantity': orderdetail.arrival_quantity,
                    'inferior_quantity': orderdetail.inferior_quantity,
                    'all_quantity': orderdetail.inferior_quantity + orderdetail.arrival_quantity,
                    'in_inbound': int(orderdetail.chichu_id) in self.sku_data,
                }
                sku_dict.update({
                    'id': sku.id,
                    'properties_name': sku.properties_name or sku.properties_alias,
                    'barcode': sku.barcode
                })
                if self.is_allocated():
                    relation = self.get_relation(orderdetail)
                    sku_dict.update({
                        'has_relation': bool(relation),
                        'has_out_stock': bool(relation.inbounddetail.out_stock_cnt if relation else 0),
                        'inbound_total': self.sku_data.get(sku.id, 0),
                        'inbound_arrival_quantity': relation.arrival_quantity if relation else 0,
                        'inbound_inferior_quantity': relation.inferior_quantity if relation else 0,
                        'inbound_status_info': relation.inbounddetail.get_allocate_info() if relation else '',
                        'inbound_relation_id': relation.id if relation else ''
                    })
                product_dict['skus'].append(sku_dict)
                product_dict['sku_ids'] = [sku['id'] for sku in product_dict['skus']]
                cache_products[orderdetail.product_id] = product_dict
            for product_id in cache_products:
                orderlists_dict[orderlist.id]['products'].append(cache_products[product_id])
        for key, orderlist_dict in orderlists_dict.iteritems():
            orderlist_dict['len_of_sku'] = sum([len(i['skus']) for i in orderlist_dict['products']])
        return orderlists_dict

    def _build_orderlists(self, orderlist_ids):
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            buyer_name = '未知'
            if orderlist.buyer_id:
                buyer_name = '%s%s' % (orderlist.buyer.last_name,
                                       orderlist.buyer.first_name)
                buyer_name = buyer_name or orderlist.buyer.username

            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': buyer_name,
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }

        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):
            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)

            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})

            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'orderdetail_id': orderdetail.id
            }

        saleproduct_ids = set()
        products_dict = {}
        for product in Product.objects.filter(id__in=list(product_ids)):
            products_dict[product.id] = {
                'id': product.id,
                'name': product.name,
                'saleproduct_id': product.sale_product,
                'outer_id': product.outer_id,
                'pic_path': product.pic_path,
                'ware_by': product.ware_by
            }
            saleproduct_ids.add(product.sale_product)

        skus_dict = {}
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            skus_dict[sku.id] = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'is_inbound': 1
            }

        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link
            }

        orderlists = []
        for orderlist_id in sorted(orderlists_dict.keys()):
            orderlist_dict = orderlists_dict[orderlist_id]
            orderlist_products_dict = orderlist_dict['products']

            orderlist_products = []
            len_of_skus = 0
            for product_id in sorted(orderlist_products_dict.keys()):
                product_dict = copy.copy(products_dict[product_id])
                product_dict.update(saleproducts_dict.get(product_dict[
                                                              'saleproduct_id']) or {})
                orderlist_skus_dict = orderlist_products_dict[product_id]
                for sku_id in sorted(orderlist_skus_dict.keys()):
                    len_of_skus += 1
                    sku_dict = orderlist_skus_dict[sku_id]
                    sku_dict.update(skus_dict[sku_id])
                    product_dict.setdefault('skus', []).append(sku_dict)
                orderlist_products.append(product_dict)
            orderlist_dict['orderlist_id'] = orderlist_id
            orderlist_dict['products'] = orderlist_products
            orderlist_dict['len_of_skus'] = len_of_skus
            orderlists.append(orderlist_dict)
        return orderlists

    def products_item_sku(self):
        products = self.products
        for sku in self.product_skus:
            for product in products:
                if sku.product_id == product.id:
                    if not hasattr(product, 'detail_skus'):
                        product.detail_skus = []
                    product.detail_skus.append(sku)
                    break
                    continue
        for product in products:
            product.detail_sku_ids = [sku.id for sku in product.detail_skus]
            product.detail_length = len(product.detail_sku_ids)
        for detail in self.details.all():
            for product in products:
                if detail.sku_id in product.detail_sku_ids:
                    if not hasattr(product, 'detail_items'):
                        product.detail_items = []
                    product.detail_items.append(detail)
        return products

    def finish_check(self, data):
        """
            完成质检
        :return:
        """
        for inbound_detail_id in data:
            inbound_detail = InBoundDetail.objects.get(id=inbound_detail_id)
            if inbound_detail.checked:
                inbound_detail.set_quantity(data[inbound_detail_id]["arrivalQuantity"],
                                            data[inbound_detail_id]["inferiorQuantity"], update_stock=True)
            else:
                inbound_detail.set_quantity(data[inbound_detail_id]["arrivalQuantity"],
                                            data[inbound_detail_id]["inferiorQuantity"])
                inbound_detail.finish_check2()
        self.status = InBound.COMPLETED
        self.checked = True
        self.check_time = datetime.datetime.now()
        self.set_stat()
        self.save()

    def need_return(self):
        if self.status != InBound.COMPLETE_RETURN:
            return self.wrong or self.out_stock
        else:
            return False

    def generate_return_goods(self, noter):
        if self.need_return():
            ReturnGoods.generate_by_inbound(self, noter)
        self.status = InBound.COMPLETE_RETURN
        self.save()

    def reset_to_verify(self):
        self.status = InBound.WAIT_CHECK
        self.checked = False
        self.save()

    def reset_to_allocate(self):
        self.checked = False
        self.status = InBound.PENDING
        self.save()
        for detail in self.details.filter(checked=True):
            detail.reset_to_unchecked()

    def get_optimized_allocate_dict(inbound):
        EXPRESS_NO_SPLIT_PATTERN = re.compile(r'\s+|,|，')
        express_no = inbound.express_no
        orderlist_id = inbound.ori_orderlist_id
        inbound_skus_dict = inbound.sku_data
        orderlist_ids = inbound.get_may_allocate_order_list_ids()
        boxes = []
        orderlists = []
        orderlist_ids_with_express_no = []
        for orderlist in OrderList.objects.filter(
                id__in=orderlist_ids).order_by('id'):
            orderlists.append(orderlist)
            orderlist_express_nos = [
                x.strip()
                for x in EXPRESS_NO_SPLIT_PATTERN.split(
                    orderlist.express_no.strip())
                ]
            if express_no and orderlist.express_no and express_no.strip(
            ) in orderlist_express_nos:
                orderlist_ids_with_express_no.append(orderlist_id)
            orderlist_skus_dict = {}
            for orderdetail in orderlist.order_list.all():
                orderlist_skus_dict[int(orderdetail.chichu_id)] = max(
                    orderdetail.buy_quantity - orderdetail.arrival_quantity, 0)
            row = []
            for sku_id in sorted(inbound_skus_dict.keys()):
                row.append(orderlist_skus_dict.get(sku_id) or 0)
            boxes.append(row)
        boxes = np.matrix(boxes)
        package = np.matrix([inbound_skus_dict[k]
                             for k in sorted(inbound_skus_dict.keys())])
        orderlist_ids = sorted(orderlist_ids)
        n = len(orderlist_ids)
        z = sys.maxint
        solution = 0
        for i in range(1, 1 << n):
            x = np.matrix([int(j) for j in ('{0:0%db}' % n).format(i)])
            tmp = np.dot(boxes.T, x.T) - package.T
            tmp = np.abs(tmp).sum()
            if z > tmp:
                z = tmp
                solution = i
        matched_orderlist_ids = []
        for i, j in enumerate(('{0:0%db}' % n).format(solution)):
            if int(j) > 0:
                matched_orderlist_ids.append(orderlist_ids[i])
        if orderlist_id and orderlist_id not in matched_orderlist_ids:
            matched_orderlist_ids.append(orderlist_id)
        tail_orderlist_ids = []
        for orderlist in orderlists:
            if orderlist.id in matched_orderlist_ids:
                continue
            if orderlist.id in orderlist_ids_with_express_no:
                matched_orderlist_ids.append(orderlist.id)
            else:
                tail_orderlist_ids.append(orderlist.id)
        orderlists = sorted(
            orderlists,
            key=
            lambda x: (matched_orderlist_ids + tail_orderlist_ids).index(x.id))
        allocate_dict = {}
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_num = inbound_skus_dict.get(sku_id)
                if not inbound_sku_num:
                    continue
                delta = min(
                    max(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        0), inbound_sku_num)
                if delta > 0:
                    allocate_dict[orderdetail.id] = delta
                    inbound_sku_num -= delta
                    if inbound_sku_num <= 0:
                        inbound_skus_dict.pop(sku_id, False)
        return allocate_dict

    def get_relation(self, order_detail):
        return OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound__id=self.id,
                                                       orderdetail__id=order_detail.id).first()

    @property
    def all_quantity(self):
        return self.details.aggregate(n=Sum('arrival_quantity') + Sum('inferior_quantity')).get('n', 0)

    @property
    def all_allocate_quantity(self):
        return self.details.filter(wrong=False).aggregate(n=Sum('arrival_quantity')).get('n', 0)

    @property
    def all_inferior_quantity(self):
        return self.details.filter(wrong=False).aggregate(n=Sum('inferior_quantity')).get('n', 0)

    @property
    def out_stock_cnt(self):
        return sum([d.out_stock_cnt for d in self.details.all()])

    @property
    def error_cnt(self):
        return self.details.filter(wrong=True).aggregate(n=Sum('arrival_quantity')).get('n', 0) or 0

    @property
    def err_detail(self):
        if not hasattr(self, '_err_detail_'):
            self._err_detail_ = self.details.filter(wrong=True).first()
        return self._err_detail_

    def is_allocated(self):
        return self.status > InBound.PENDING

    def is_finished(self):
        return self.status >= InBound.COMPLETED

    def set_stat(self):
        ori_out_stock = self.out_stock
        ori_wrong = self.wrong
        self.out_stock = True in [u["out_stock"] for u in self.details.values("out_stock")]
        self.wrong = self.details.filter(wrong=True).exists()
        if ori_out_stock == self.out_stock and ori_wrong == self.wrong:
            change = False
        else:
            change = True
        return change

    def add_order_detail(self, orderdetail, num):
        oi = OrderDetailInBoundDetail.create(orderdetail, self, num)
        inbounddetail = self.details.filter(sku=orderdetail.sku).first()
        if inbounddetail.checked:
            ProductSku.objects.filter(id=inbounddetail.sku_id).update(quantity=F('quantity') + oi.num)
        return oi

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'


def update_warehouse_receipt_status(sender, instance, created, **kwargs):
    """
    update the warehouse receipt status to opened!
    """
    if created:
        from shopback.warehouse.models import ReceiptGoods
        ReceiptGoods.update_status_by_open(instance.express_no)


post_save.connect(update_warehouse_receipt_status, sender=InBound,
                  dispatch_uid='post_save_update_warehouse_receipt_status')


class InBoundDetail(models.Model):
    NORMAL = 1
    PROBLEM = 2

    OUT_ORDERING = 2
    ERR_ORDERING = 3
    ERR_OUT_ORDERING = 4

    inbound = models.ForeignKey(InBound,
                                related_name='details',
                                verbose_name=u'入库单')
    product = models.ForeignKey(Product,
                                null=True,
                                blank=True,
                                related_name='inbound_details',
                                verbose_name=u'入库商品')
    sku = models.ForeignKey(ProductSku,
                            null=True,
                            blank=True,
                            related_name='inbound_details',
                            verbose_name=u'入库规格')

    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'颜色编码')
    properties_name = models.CharField(max_length=128,
                                       blank=True,
                                       verbose_name=u'规格')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'已到数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')

    checked = models.BooleanField(default=False, verbose_name=u"是否检查")
    check_time = models.DateTimeField(null=True, verbose_name=u"检查时间")
    wrong = models.BooleanField(default=False, verbose_name=u"是否有错")
    out_stock = models.BooleanField(default=False, verbose_name=u"是否多货")

    status = models.SmallIntegerField(
        default=PROBLEM,
        choices=((NORMAL, u'正常'), (PROBLEM, u'有问题')),
        verbose_name=u'状态')
    district = models.CharField(max_length=64, blank=True, verbose_name=u'库位')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'flashsale_dinghuo_inbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓单明细'
        verbose_name_plural = u'入仓单明细列表'

    def check_sync_quantity(inbounddetail):
        return inbounddetail.arrival_quantity == inbounddetail.records.aggregate(
            n=Sum('arrival_quantity')).get('n') and inbounddetail.inferior_quantity == inbounddetail.records.aggregate(
            n=Sum('inferior_quantity')).get('n')

    def sync_order_detail(self):
        for oi in self.records.all():
            oi.update_orderdetail()

    def change_total_quantity(self, num):
        """
            数量变化，不改变次品数
            如果总数大于分配数，则不改变分配数，如果总数小于分配数，则调整分配数使它重新等于总数
        :param num:
        :return:
        """
        self.arrival_quantity += num
        if self.arrival_quantity < 0:
            raise Exception(u"入库的正品数不可能小于0，请保证次品数正确")
        self.save()
        if self.arrival_quantity < self.all_allocate_quantity:
            change_total = self.all_allocate_quantity - self.arrival_quantity
            if self.records.exists():
                self.change_records_arrival_quantity(change_total, self.checked)

    def change_records_arrival_quantity(self, change_total, change_stock=False):
        """
            inbound_detail的arrival_quantity变化自动体现到records上
        :param change_total:
        :param change_stock:
        :return:
        """
        quantity_add = change_total
        for r in self.records.order_by('-id'):
            if r.arrival_quantity >= change_total:
                r.arrival_quantity -= change_total
                r.save()
                break
            else:
                r.arrival_quantity = 0
                r.save()
                change_total -= r.arrival_quantity
        if change_stock:
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - quantity_add)

    @property
    def out_stock_num(self):
        all_allocate_quantity = self.all_allocate_quantity
        self.out_stock = self.arrival_quantity > all_allocate_quantity
        return self.arrival_quantity - all_allocate_quantity

    @property
    def all_allocate_quantity(self):
        total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', 0)
        total = total if total else 0
        return total

    def get_status_info(self):
        info = u''
        if self.out_stock:
            info += u'多货'
        return info

    def get_allocate_info(self):
        if self.out_stock_num > 0:
            return u'多货'
        return u'完全分配'

    def reset_out_stock(self):
        ori_out_stock = self.out_stock
        self.out_stock = self.out_stock_num > 0
        if ori_out_stock != self.out_stock:
            InBoundDetail.objects.filter(id=self.id).update(out_stock=self.out_stock)

    def reset_to_unchecked(self):
        if self.checked:
            self.checked = False
            self.save()
            arrival_total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', 0)
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - arrival_total)

    def finish_change_inferior(self, arrival_quantity, inferior_quantity):
        """
            完成质检同时更改次品数
        :param arrival_quantity:
        :param inferior_quantity:
        :return:
        """
        self.set_quantity(arrival_quantity, inferior_quantity)
        self.finish_check2()

    def finish_check(self):
        """
            完成质检
        :return:
        """
        if self.wrong:
            raise Exception(u"错货无法通过质检")
        if not self.status == InBoundDetail.NORMAL:
            self.status = InBoundDetail.NORMAL
        if not self.checked:
            self.checked = True
            self.check_time = datetime.datetime.now()
            self.status = InBoundDetail.NORMAL
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') + self.all_allocate_quantity)
        self.save()

    def finish_check2(self):
        if self.checked:
            return
        self.checked = True
        self.check_time = datetime.datetime.now()
        self.status = InBoundDetail.NORMAL
        ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') + self.all_allocate_quantity)
        self.save()

    def set_quantity(self, arrival_quantity, inferior_quantity, update_stock=False):
        """
            设置库存
        :param arrival_quantity:
        :param inferior_quantity:
        :param update_stock:
        :return:
        """
        if self.arrival_quantity == arrival_quantity and self.inferior_quantity == inferior_quantity:
            return
        if arrival_quantity + inferior_quantity != self.arrival_quantity + self.inferior_quantity:
            raise Exception(u'改变次品时总数量不能发生变化')
        self.inferior_quantity = inferior_quantity
        self.arrival_quantity = arrival_quantity
        if self.records.exists() and self.arrival_quantity < self.all_allocate_quantity:
            # 已经分配到订货单的必须同步修正订货单
            change = self.all_allocate_quantity - self.arrival_quantity
            self.set_records_quantity(change, update_stock)
        self.save()

    def set_records_quantity(self, change_total, update_stock):
        """
            inbound_detail的arrival_quantity的减少自动体现到records上
        :param change_total:
        :param change_stock:
        :return:
        """
        quantity_change = change_total
        for r in self.records.order_by('-id'):
            if r.arrival_quantity >= change_total:
                r.arrival_quantity -= change_total
                r.save()
                break
            else:
                r.arrival_quantity = 0
                r.save()
                change_total -= r.arrival_quantity
        if update_stock:
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - quantity_change)

    @property
    def out_stock_cnt(self):
        if self.wrong:
            return 0
        total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', None)
        total = 0 if total is None else total
        return self.arrival_quantity - total


def update_stock(sender, instance, created, **kwargs):
    if instance.checked:
        instance.sync_order_detail()
        from shopback.items.tasks import task_update_productskustats_inferior_num
        task_update_productskustats_inferior_num.delay(instance.sku_id)


post_save.connect(update_stock,
                  sender=InBoundDetail,
                  dispatch_uid='post_save_update_stock')


class OrderDetailInBoundDetail(models.Model):
    INVALID = 0
    NORMAL = 1
    orderdetail = models.ForeignKey(OrderDetail, related_name='records', verbose_name=u'订货明细')
    inbounddetail = models.ForeignKey(InBoundDetail, related_name='records', verbose_name=u'入仓明细')
    arrival_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'正品数')
    inferior_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'次品数')
    status = models.SmallIntegerField(
        default=NORMAL,
        choices=((NORMAL, u'正常'), (INVALID, u'无效')),
        verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'dinghuo_orderdetailinbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓订货明细对照'
        verbose_name_plural = u'入仓订货明细对照列表'

    @staticmethod
    def create(orderdetail, inbound, arrival_quantity, inferior_quantity=0):
        inbounddetail = inbound.details.get(sku_id=orderdetail.chichu_id)
        oi = OrderDetailInBoundDetail(orderdetail=orderdetail, inbounddetail=inbounddetail,
                                      arrival_quantity=arrival_quantity, inferior_quantity=inferior_quantity)
        oi.save()
        return oi

    def change_arrival_quantity(self, num):
        if self.inbounddetail.out_stock_cnt < num:
            raise Exception(u"入库数不足进行分配")
        if self.orderdetail.need_arrival_quantity < num:
            raise Exception(u"分配数超出订货待入库数")
        self.arrival_quantity += num
        if self.arrival_quantity < 0:
            raise Exception(u"入库数不能小于0")
        self.save()
        if self.inbounddetail.checked:
            ProductSku.objects.filter(id=self.inbounddetail.sku_id).update(quantity=F('quantity') + num)
        return True

    def update_orderdetail(self):
        orderdetail = self.orderdetail
        orderdetail.arrival_quantity = orderdetail.records.filter(
            inbounddetail__checked=True).aggregate(
            n=Sum('arrival_quantity')).get('n') or 0
        orderdetail.inferior_quantity = orderdetail.records.filter(
            inbounddetail__checked=True).aggregate(
            n=Sum('inferior_quantity')).get('n') or 0
        orderdetail.non_arrival_quantity = orderdetail.buy_quantity - orderdetail.arrival_quantity \
                                           - orderdetail.inferior_quantity
        orderdetail.arrival_time = orderdetail.records.order_by('-created').first().created
        orderdetail.save()


def update_inbound_record(sender, instance, created, **kwargs):
    instance.inbounddetail.reset_out_stock()


post_save.connect(update_inbound_record,
                  sender=OrderDetailInBoundDetail,
                  dispatch_uid='post_save_orderdetail_inbounddetail_update_inbound_record')


def update_orderdetail_record(sender, instance, created, **kwargs):
    instance.update_orderdetail()


post_save.connect(update_orderdetail_record,
                  sender=OrderDetailInBoundDetail,
                  dispatch_uid='post_save_orderdetail_inbounddetail_update_orderdetail_record')
