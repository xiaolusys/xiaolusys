# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from collections import OrderedDict
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.db import transaction
from core.utils.modelutils import update_model_fields
from core.models import BaseModel
from shopback.items.models import ProductSku, Product
from shopback.warehouse.constants import WARE_CHOICES, WARE_NONE, WARE_GZ
from supplychain.supplier.models import SaleSupplier
from shopback.trades.models import SkuStock
import logging

logger = logging.getLogger(__name__)


def gen_purchase_order_group_key(order_ids):
    sorted_ids = [int(s) for s in order_ids]
    sorted_ids.sort()
    return '-%s-' % ('-'.join([str(s) for s in sorted_ids]))


class OrderList(models.Model):
    # 订单状态
    SUBMITTING = u'草稿'  # 提交中
    APPROVAL = u'审核'  # 审核
    WAIT_PAY = u"付款"
    BE_PAID = u'已付款'
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
        (ST_FINISHED, u'已完成'),
        (ST_CLOSE, u'已取消'),
    )

    CREATED_BY_PERSON = 1  # 手工订购
    CREATED_BY_MACHINE = 2  # 自动订货
    CREATED_BY_REPURCHASE = 3  # 补货

    ORDER_PRODUCT_STATUS = ((SUBMITTING, u'草稿'), (APPROVAL, u'审核'), (BE_PAID, u'已付款'),
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
                        (DBKD, u'德邦快递'),
                        )

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
    is_postpay = models.BooleanField(default=False, verbose_name=u'后付')
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
    # supplier_executor_phone =  models.CharField(choices=EXPRESS_CONPANYS, blank=True, max_length=32, verbose_name=u'快递公司')
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
    p_district = models.CharField(null=True,
                                  max_length=32,
                                  default=NEAR,
                                  verbose_name=u'地区',
                                  choices=ORDER_DISTRICT)  # 删除
    reach_standard = models.BooleanField(default=False, verbose_name=u"达标")
    created = models.DateField(auto_now_add=True,
                               db_index=True,
                               verbose_name=u'订货日期')
    checked_time = models.DateTimeField(default=None, null=True, verbose_name=u'检出时间')
    pay_time = models.DateTimeField(default=None, null=True, verbose_name=u'开始支付时间')
    paid_time = models.DateTimeField(default=None, null=True, verbose_name=u'支付完成时间')
    receive_time = models.DateTimeField(default=None, null=True, verbose_name=u'开始收货时间')
    received_time = models.DateTimeField(default=None, null=True, verbose_name=u'开始结算时间')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    completed_time = models.DateTimeField(blank=True, null=True, verbose_name=u'完成时间')
    note = models.TextField(default="", blank=True, verbose_name=u'备注信息')
    created_by = models.SmallIntegerField(
        choices=((CREATED_BY_PERSON, u'手工订货'), (CREATED_BY_MACHINE, u'订单自动订货'), (CREATED_BY_REPURCHASE, u'补货')),
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

    STAGING_STAGES = [STAGE_CHECKED, STAGE_PAY, STAGE_RECEIVE]  # 待处理状态
    # 改进原状态一点小争议和妥协造成的状态字段冗余 TODO@hy
    stage = models.IntegerField(db_index=True, choices=STAGE_CHOICES, default=0, verbose_name=u'进度')
    # 冗余字段 避免过多查询
    lack = models.NullBooleanField(default=None, verbose_name=u'缺货')
    inferior = models.BooleanField(default=False, verbose_name=u'次品')
    press_num = models.IntegerField(default=0, db_index=True, verbose_name=u'催促次数')
    ARRIVAL_NOT = 0
    ARRIVAL_NEED_PROCESS = 1
    ARRIVAL_PRESSED = 2
    ARRIVAL_FINISHED = 3
    ARRIVAL_CHOICES = ((ARRIVAL_NOT, u'未到'), (ARRIVAL_NEED_PROCESS, u'需处理'),
                       (ARRIVAL_PRESSED, u'已催货'), (ARRIVAL_FINISHED, u'已完成'))
    arrival_process = models.IntegerField(choices=ARRIVAL_CHOICES, default=ARRIVAL_NOT, verbose_name=u'到货处理')
    purchase_total_num = models.IntegerField(default=0, verbose_name=u'订购总件数')
    last_pay_date = models.DateField(null=True, blank=True, verbose_name=u'最后下单日期')

    ware_by = models.IntegerField(choices=WARE_CHOICES, default=WARE_NONE, verbose_name=u'收货仓')
    third_package = models.BooleanField(default=False, verbose_name=u'第三方发货')
    purchase_order_unikey = models.CharField(max_length=32, unique=True, null=True, verbose_name=u'订货单生成标识')
    order_group_key = models.CharField(max_length=128, db_index=True, blank=True, verbose_name=u'订货单分组键')

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
        return self.stage == OrderList.STAGE_DRAFT

    def is_booked(self):
        return self.stage not in [OrderList.STAGE_DRAFT, OrderList.STAGE_COMPLETED, OrderList.STAGE_DELETED,
                                  OrderList.STAGE_STATE]

    def can_receive(self):
        return self.stage in [OrderList.STAGE_RECEIVE, OrderList.STAGE_STATE, OrderList.STAGE_COMPLETED]

    def is_finished(self):
        return self.stage in [OrderList.STAGE_STATE, OrderList.STAGE_COMPLETED]

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

    def add_note(self, msg, save=True):
        now = datetime.datetime.now()
        self.note += '\n-->%s: %s' % (now.strftime('%m月%d %H:%M'), msg)
        if save:
            self.save()

    @property
    def normal_details(self):
        return self.order_list.all()

    @property
    def total_detail_num(self):
        return self.purchase_total_num

    @property
    def total_arrival_quantity(self):
        n = self.order_list.aggregate(n=Sum('arrival_quantity')).get('n', 0)
        return n or 0

    @property
    def status_name(self):
        return self.get_sys_status_display()

    @property
    def lack_num(self):
        return sum([detail.need_arrival_quantity for detail in self.order_list.all()])

    def lack_detail(self):
        res = []
        for d in self.order_list.all():
            if d.need_arrival_quantity > 0:
                res.append(d)
        return res

    @property
    def related_inbounds(self):
        if not hasattr(self, '_related_inbounds_'):
            from flashsale.dinghuo.models.inbound import InBound
            self._related_inbounds_ = InBound.objects.filter(id__in=self.get_inbound_ids())
        return self._related_inbounds_

    @property
    def related_out_stock_inbound_details(self):
        if not hasattr(self, '_related_out_stock_inbound_details_'):
            from flashsale.dinghuo.models.inbound import InBoundDetail
            self._related_out_stock_inbound_details_ = InBoundDetail.objects.filter(
                inbound_id__in=self.get_inbound_ids(), out_stock=True)
        return self._related_out_stock_inbound_details_

    @property
    def related_inferior_inbound_details(self):
        if not hasattr(self, '_related_inferior_inbound_details_'):
            from flashsale.dinghuo.models.inbound import InBoundDetail
            self._related_inferior_inbound_details_ = InBoundDetail.objects.filter(
                inbound_id__in=self.get_inbound_ids(), inferior_quantity__gt=0)
        return self._related_inferior_inbound_details_

    @property
    def purchase_order(self):
        from flashsale.dinghuo.models_purchase import PurchaseOrder
        return PurchaseOrder.objects.get(uni_key=self.purchase_order_unikey)

    @property
    def package_sku_items(self):
        """

        """
        from shopback.trades.models import PackageSkuItem
        if self.stage == OrderList.STAGE_DRAFT:
            sku_ids = list(self.purchase_order.arrangements.values_list('sku_id', flat=True))
            psis = PackageSkuItem.objects.filter(
                sku_id__in=sku_ids,
                assign_status__in=[PackageSkuItem.NOT_ASSIGNED],
                purchase_order_unikey=''
            )
        elif self.stage != OrderList.STAGE_DELETED:
            psis = PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey)
        else:
            psis = []
        return psis

    @staticmethod
    def filter_by_supplier(supplier_id, stages=[1, 2, 3]):
        return OrderList.objects.filter(stage__in=stages, supplier_id=supplier_id)

    def verify_order(self):
        """
        审核订货单
        """
        from shopback.warehouse import WARE_THIRD
        from flashsale.finance.models import Bill

        psis = self.package_sku_items

        psis_total = psis.aggregate(total=Sum('num')).get('total') or 0
        ods_res = OrderDetail.objects.filter(purchase_order_unikey=self.purchase_order_unikey) \
                             .aggregate(total=Sum('buy_quantity'))

        ods_total = ods_res['total'] or 0

        if psis_total == 0:
            raise Exception(u'至少要有一个待订货skuitem')

        if psis_total != ods_total:
            raise Exception(u'数量不对，审核失败')

        if self.supplier.ware_by == WARE_THIRD and self.stage < OrderList.STAGE_CHECKED:
            psi_oids = [p.oid for p in psis]
            self.begin_third_package(psi_oids)
            Bill.create([self], Bill.PAY, Bill.STATUS_DELAY, Bill.TRANSFER_PAY, 0, 0, self.supplier,
                        user_id=919899, receive_account='', receive_name='',
                        pay_taobao_link='', transcation_no='')
            return u'订货单已成功进入结算!'
        # elif self.stage < OrderList.STAGE_CHECKED:
        #     self.set_stage_verify()
        #     print u'已成功审核!'

    def begin_third_package(self, psi_oids=[]):
        self.third_package = True
        self.bill_method = OrderList.PC_COD_TYPE
        self.is_postpay = True
        self.purchase_order.book()
        self.ware_by = self.supplier.ware_by
        _now = datetime.datetime.now()
        self.add_note(u'-->%s:审核第三方发货订货单' % _now.strftime('%m月%d %H:%M'), save=False)
        self.set_stage_state()

    def get_related_inbounds_out_stock_cnt(self):
        return sum([d.out_stock_num for d in self.related_out_stock_inbound_details])

    def get_inbound_ids(self):
        from flashsale.dinghuo.models.inbound import InBoundDetail
        detail_ids = [i['id'] for i in self.order_list.values('id')]
        q = InBoundDetail.objects.filter(records__orderdetail_id__in=detail_ids).values('inbound_id').distinct()
        return [i['inbound_id'] for i in q]

    def get_inbounds(self):
        from flashsale.dinghuo.models.inbound import InBound
        return InBound.objects.filter(id__in=self.get_inbound_ids())

    def press(self, desc):
        OrderGuarantee(purchase_order=self, desc=desc).save()
        self.press_num = self.guarantees.count()
        self.arrival_process = OrderList.ARRIVAL_PRESSED
        self.save(update_fields=['press_num', 'arrival_process'])

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
        arrival_process = None
        if lack is False:
            arrival_process = OrderList.ARRIVAL_FINISHED
        elif lack is None:
            arrival_process = OrderList.ARRIVAL_NOT
        elif lack is True and self.arrival_process in [OrderList.ARRIVAL_NOT, OrderList.ARRIVAL_FINISHED]:
            arrival_process = OrderList.ARRIVAL_NEED_PROCESS
        change = False
        if self.lack != lack:
            change = True
            self.lack = lack
        if self.inferior != inferior:
            change = True
            self.inferior = inferior
        if arrival_process and self.arrival_process != arrival_process:
            change = True
            self.arrival_process = arrival_process
        return change

    def set_arrival_process_status(self):
        if self.set_stat():
            self.save()

    def set_express_no(self, express_no, express_company):
        self.express_no = express_no
        self.express_company = express_company
        self.save()
        from flashsale.forecast.models import ForecastInbound
        inbounds = ForecastInbound.objects.filter(relate_order_set__id=self.id, status__in=[ForecastInbound.ST_DRAFT,
                                                                                 ForecastInbound.ST_APPROVED])
        if inbounds.count() == 1:
            inbounds.update(express_code=self.express_company, express_no=self.express_no)
        else:
            inbounds.filter(express_no='').update(express_code=self.express_company, express_no=self.express_no)

    def has_paid(self):
        return self.status > OrderList.STAGE_PAY

    def set_stage_verify(self, is_postpay=False):
        self.stage = OrderList.STAGE_CHECKED
        self.status = OrderList.APPROVAL
        self.purchase_total_num = self.order_list.aggregate(
            total_num=Sum('buy_quantity')).get('total_num') or 0
        self.checked_time = datetime.datetime.now()
        self.ware_by = self.supplier.ware_by
        if is_postpay:
            self.is_postpay = True
        _now = datetime.datetime.now()
        self.add_note(u'-->%s:审核订货单' % _now.strftime('%m月%d %H:%M'), save=False)
        self.save(update_fields=['stage', 'status', 'is_postpay', 'checked_time', 'ware_by', 'note'])
        try:
            from flashsale.forecast.models.forecast import ForecastInbound
            ForecastInbound.reset_forecast(self.id)
        except Exception, e0:
            logger.error("begin forecast error ol: %s, info:%s" % (self.id, e0.message))

    def set_stage_pay(self, pay_way=13):
        # 付款提货 进入付款状态
        self.bill_method = pay_way
        self.is_postpay = pay_way == 11
        self.stage = OrderList.STAGE_PAY
        self.pay_time = datetime.datetime.now()
        self.save()

    def set_stage_receive(self, pay_way=11):
        """
            直接设置收货仅限于到货付款的情况
        """
        self.bill_method = pay_way
        self.stage = OrderList.STAGE_RECEIVE
        self.status = OrderList.QUESTION_OF_QUANTITY
        if not self.receive_time:
            self.receive_time = datetime.datetime.now()
        self.is_postpay = pay_way == OrderList.PC_COD_TYPE
        self.save()

    def set_stage_state(self):
        self.stage = OrderList.STAGE_STATE
        self.status = OrderList.TO_BE_PAID
        self.received_time = datetime.datetime.now()
        self.arrival_process = OrderList.ARRIVAL_FINISHED
        self.save()
        from flashsale.forecast.models import ForecastInbound
        ForecastInbound.reset_forecast(self.id, status=ForecastInbound.ST_ARRIVED)

    def set_stage_complete(self):
        self.stage = OrderList.STAGE_COMPLETED
        self.status = OrderList.CLOSED
        self.completed_time = datetime.datetime.now()
        self.save()

    def set_stage_delete(self):
        self.stage = OrderList.STAGE_DELETED
        self.status = OrderList.ZUOFEI
        self.save()

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

    def get_bill(self):
        """
            暂不支持订货单多账单
        """
        from flashsale.finance.models import BillRelation
        br = BillRelation.objects.filter(object_id=self.id, type=BillRelation.TYPE_DINGHUO_PAY).first()
        if br:
            return br.bill

    bill = property(get_bill)

    def get_return_bill(self):
        from flashsale.finance.models import BillRelation
        if self.bill_method != OrderList.PC_POD_TYPE:
            return None
        br = BillRelation.objects.filter(object_id=self.id, type=BillRelation.TYPE_DINGHUO_RECEIVE).first()
        if br:
            return br.bill

    return_bill = property(get_return_bill)

    def get_bills(self):
        from flashsale.finance.models import BillRelation
        br = BillRelation.objects.filter(object_id=self.id, type__in=[1, 2])
        bill = [i.bill for i in br]
        if bill:
            return bill

    def update_stage(self):
        if self.stage == OrderList.STAGE_PAY:
            if self.bill.is_finished():
                self.set_stage_receive(self.bill_method)
        elif self.stage == OrderList.STAGE_RECEIVE:
            change = self.set_stat()
            if self.lack is False:
                self.set_stage_state()
            elif change:
                self.save()
        elif self.stage == OrderList.STAGE_STATE:
            change = self.set_stat()
            bill = self.get_bills()
            if self.lack is False and not self.is_postpay:
                self.set_stage_complete()
            elif bill and all([i.is_finished() for i in bill]):
                self.set_stage_complete()
            elif change:
                self.save()

    def check_by_package_skuitem(self):
        from shopback.trades.models import PackageSkuItem
        sku_ids = list(self.purchase_order.arrangements.values_list('sku_id', flat=True))
        psis = PackageSkuItem.objects.filter(sku_id__in=sku_ids, assign_status=PackageSkuItem.NOT_ASSIGNED,
                                             purchase_order_unikey='')
        sku_nums = {i['sku_id']: i['total'] for i in psis.values('sku_id').annotate(total=Sum('num'))}
        err_skus = []
        for sku_id in sku_nums:
            od = self.order_list.filter(chichu_id=str(sku_id)).first()
            order_num = od.buy_quantity if od else 0
            print sku_id, order_num, sku_nums[sku_id]
            if order_num != sku_nums[sku_id]:
                err_skus.append(sku_id)
        extra_ods = self.order_list.filter(buy_quantity__gt=0).exclude(chichu_id__in=[str(k) for k in sku_nums])
        err_skus.extend([int(od.chichu_id) for od in extra_ods])
        return err_skus

    def set_by_package_sku_item(self):
        from shopback.trades.models import PackageSkuItem
        psis = PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey, assign_status=2)
        sku_nums = {str(i['sku_id']): i['total'] for i in psis.values('sku_id').annotate(total=Sum('num'))}
        for od in self.order_list.all():
            od.arrival_quantity = sku_nums.get(str(od.chichu_id), 0)
            if not od.arrival_time:
                od.arrival_time = datetime.datetime.now()
            od.save()

    def reduce_sku_num(self, sku_id, num=1):
        od = self.order_list.filter(chichu_id=str(sku_id)).first()
        if num <= od.arrival_quantity:
            od.arrival_quantity = od.arrival_quantity - num
            od.save()
            self.add_note(u'SKU' + (sku_id) + u'缺了' + num + u'个，已将其扣除')
        else:
            raise Exception(u'调整数不可能大于已入库数')

    @classmethod
    def gen_group_key(cls, orderids):
        return gen_purchase_order_group_key(orderids)

    def to_excel_data(self, format):
        from shopback.trades.models import PackageSkuItem
        need_send = PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey)
        items = []
        if not format:
            columns = [u'订单号', u'产品条码', u'订单状态', u'买家id', u'子订单编号', u'供应商编码', u'买家昵称', u'商品名称', u'产品规格', u'商品单价',
                       u'商品数量',
                       u'商品总价', u'运费', u'购买优惠信息', u'总金额', u'买家购买附言', u'收货人姓名', u'收货地址', u'邮编',
                       u'收货人手机', u'收货人电话', u'买家选择运送方式', u'卖家备忘内容', u'订单创建时间', u'付款时间', u'物流公司', u'物流单号', u'发货附言',
                       u'发票抬头', u'电子邮件', u'商品链接']
            for p in need_send:
                o = p.package_order
                saleproduct = p.product_sku.product.get_sale_product()
                items.append(
                    [str(o.pid) if o else '', '', p.get_assign_status_display(), str(p.sale_trade.buyer_id), str(p.id),
                     saleproduct.supplier_sku if saleproduct else '', str(p.sale_trade.buyer_nick),
                     str(p.product_sku.product.name), str(p.product_sku.properties_name),
                     str(p.product_sku.cost), str(p.num), str(p.product_sku.cost * p.num), '0', '0', '0', '', str(p.sale_trade.receiver_name),
                     str(p.sale_trade.receiver_address_detail), '', p.sale_trade.receiver_mobile, '', '', '', '',
                     p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'),
                     p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                     p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '', u'小鹿美美，时尚健康美丽',
                     '', '', saleproduct.product_link if saleproduct else ''])
        elif format == 'with_card':
            columns = [u'订单号', u'产品条码', u'订单状态', u'买家id', u'子订单编号', u'供应商编码', u'买家昵称', u'商品名称', u'产品规格', u'商品单价',
                       u'商品数量',
                       u'商品总价', u'运费', u'购买优惠信息', u'总金额', u'买家购买附言', u'收货人姓名', '身份证号码', u'省', u'市', u'区/县', u'收货详细地址',u'邮编',
                       u'收货人手机', u'收货人电话', u'买家选择运送方式', u'卖家备忘内容', u'订单创建时间', u'付款时间', u'物流公司', u'物流单号', u'发货附言',
                       u'发票抬头', u'电子邮件', u'商品链接']
            for p in need_send:
                o = p.package_order
                saleproduct = p.product_sku.product.get_sale_product()
                items.append(
                    [str(o.pid) if o else '', '', p.get_assign_status_display(), str(p.sale_trade.buyer_id), str(p.id),
                     saleproduct.supplier_sku if saleproduct else '', str(p.sale_trade.buyer_nick),
                     str(p.product_sku.product.name), str(p.product_sku.properties_name),
                     str(p.product_sku.cost), str(p.num), '0', '0', '0', '0', '', str(p.sale_trade.receiver_name),
                     str(o.user_address.identification_no) if o and o.user_address else '',
                     str(o.receiver_state), str(o.receiver_city), str(o.receiver_district),
                              str(o.receiver_address), '', p.sale_trade.receiver_mobile, '', '', '', '',
                     p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'),
                     p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                     p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '', u'小鹿美美，时尚健康美丽',
                     '', '', saleproduct.product_link if saleproduct else ''])
        elif format == 'third_package1':
            columns = [u'订单号', u'产品条码', u'订单状态', u'买家id', u'子订单编号', u'供应商编码', u'买家昵称', u'商品名称', u'产品规格', u'商品单价',
                       u'商品数量',
                       u'商品总价', u'运费', u'购买优惠信息', u'总金额', u'买家购买附言', u'收货人姓名', u'省', u'市', u'区/县', u'收货详细地址', u'邮编',
                       u'收货人手机', u'收货人电话', u'买家选择运送方式', u'卖家备忘内容', u'订单创建时间', u'付款时间', u'物流公司', u'物流单号', u'发货附言',
                       u'发票抬头', u'电子邮件', u'商品链接']
            if not self.third_package:
                raise Exception(u'此订货单不是第三方发货订货单')
            if PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey,
                                             assign_status=0).exists():
                raise Exception(u'此订货单下存在未分配的包裹')
            for p in need_send.exclude(package_order_pid=None):
                o = p.package_order
                saleproduct = p.product_sku.product.get_sale_product()
                items.append([str(o.pid), '', o.sys_status, str(o.buyer_id), str(p.id),
                              saleproduct.supplier_sku if saleproduct else '', str(o.buyer_nick),
                              str(p.product_sku.product.name), str(p.product_sku.properties_name),
                              str(p.product_sku.product.cost), str(p.num), '0', '0', '0', '0', '', str(o.receiver_name),
                              str(o.receiver_state), str(o.receiver_city), str(o.receiver_district),
                              str(o.receiver_address), '', o.receiver_mobile, '', '', '',
                              p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'),
                              p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                              p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '',
                              u'小鹿美美，时尚健康美丽', '', '', saleproduct.product_link if saleproduct else ''])
        elif format == 'third_package_wangli':
            from .data_mengnuo_wangli import MENGNUO_DATA
            columns = [u'订单号', u'<必填>下单时间', u'付款时间', u'交易类型', u'备注', u'买家留言', u'总金额',
                       u'运费', u'<必填>实付总额', u'<必填>收货人姓名', u'手机', u'固话', u'<必填>地址', u'邮编',
                       u'电子邮箱', u'<必填>商品编码', u'<必填>商品名称', u'规格名称', u'<必填>数量',
                       u'<必填>单价', u'<必填>实付']
            if not self.third_package:
               raise Exception(u'此订货单不是第三方发货订货单')
            if PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey,
                                             assign_status=0).exists():
                raise Exception(u'此订货单下存在未分配的包裹')
            for p in need_send.exclude(package_order_pid=None):
                o = p.package_order
                items.append([str(p.id), p.book_time.strftime('%Y-%m-%d %H:%M:%S'), p.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
                              u'货到付款', u'小鹿美美，时尚健康美丽', '', str(p.num * p.product_sku.cost),
                              '0', str(p.num * p.product_sku.cost), str(o.receiver_name), o.receiver_mobile, '', str(o.receiver_address_detail_wb), '',
                              '', MENGNUO_DATA.get(int(p.sku_id), ''), p.product_sku.product.name,
                              str(p.product_sku.color_size), str(p.num), str(p.product_sku.cost), str(p.num * p.product_sku.cost)])
        elif format == 'third_package':
            columns = [u'订单号', u'产品条码', u'订单状态', u'买家id', u'子订单编号', u'供应商编码', u'买家昵称', u'商品名称', u'产品规格', u'商品单价',
                       u'商品数量',
                       u'商品总价', u'运费', u'购买优惠信息', u'总金额', u'买家购买附言', u'收货人姓名', u'收货地址', u'邮编',
                       u'收货人手机', u'收货人电话', u'买家选择运送方式', u'卖家备忘内容', u'订单创建时间', u'付款时间', u'物流公司', u'物流单号', u'发货附言',
                       u'发票抬头', u'电子邮件', u'商品链接']
            if not self.third_package:
                raise Exception(u'此订货单不是第三方发货订货单')
            if PackageSkuItem.objects.filter(purchase_order_unikey=self.purchase_order_unikey,
                                             assign_status=0).exists():
                raise Exception(u'此订货单下存在未分配的包裹')
            for p in need_send.exclude(package_order_pid=None):
                o = p.package_order
                saleproduct = p.product_sku.product.get_sale_product()
                items.append([str(o.pid), '', o.sys_status, str(o.buyer_id), str(p.id),
                              saleproduct.supplier_sku if saleproduct else '', str(o.buyer_nick),
                              str(p.product_sku.product.name), str(p.product_sku.properties_name),
                              str(p.product_sku.cost), str(p.num), str(p.num * p.product_sku.cost), '0', '0', '0', '', str(o.receiver_name),
                              str(o.receiver_address_detail), '', o.receiver_mobile, '', '', '',
                              p.sale_trade.created.strftime('%Y-%m-%D %H:%M:%S'),
                              p.sale_trade.pay_time.strftime('%Y-%m-%D %H:%M:%S'),
                              p.sale_trade.logistics_company.name if p.sale_trade.logistics_company else '', '',
                              u'小鹿美美，时尚健康美丽', '', '', saleproduct.product_link if saleproduct else ''])
        return columns, items

    @staticmethod
    def create_or_update(purchase_order_unikey, od=None):
        ol = OrderList.objects.filter(purchase_order_unikey=purchase_order_unikey).first()
        if not ol:
            supplier_id = purchase_order_unikey.split('-')[0]
            supplier = SaleSupplier.get_by_id(supplier_id)
            p_district = OrderList.NEAR
            if supplier.ware_by == WARE_GZ:
                p_district = OrderList.GUANGDONG
            now = datetime.datetime.now()
            ol = OrderList(purchase_order_unikey=purchase_order_unikey, order_amount=od.total_price,
                           supplier_id=supplier.id, p_district=p_district, created_by=OrderList.CREATED_BY_MACHINE,
                           status=OrderList.SUBMITTING, note=u'-->%s:动态生成订货单' % now.strftime('%m月%d %H:%M'))

            prev_orderlist = OrderList.objects.filter(supplier_id=supplier.id,
                                                      created_by=OrderList.CREATED_BY_MACHINE).exclude(
                status=OrderList.ZUOFEI).order_by('-created').first()
            if prev_orderlist and prev_orderlist.buyer_id:
                ol.buyer_id = prev_orderlist.buyer_id

            ol.save()
        else:
            od_sum = OrderDetail.objects.filter(purchase_order_unikey=purchase_order_unikey).aggregate(
                total=Sum('total_price'))
            purchase_total_num = OrderDetail.objects.filter(purchase_order_unikey=purchase_order_unikey).aggregate(
                total=Sum('buy_quantity')).get('total') or 0
            total = od_sum['total'] or 0
            if ol.order_amount != total or ol.purchase_total_num != purchase_total_num:
                if ol.is_open():
                    ol.order_amount = total
                    ol.purchase_total_num = purchase_total_num
                    ol.save(update_fields=['order_amount', 'updated', 'purchase_total_num'])
                else:
                    logger.warn("tying to modify booked order_list| ol.id: %s, od: %s" % (ol.id,))
            else:
                ol.save(update_fields=['updated'])


def check_with_purchase_order(sender, instance, created, **kwargs):
    logger.info('post_save check_with_purchase_order: %s' % instance)
    if not instance.order_group_key:
        instance.order_group_key = '-%s-' % instance.id
        instance.save(update_fields=['order_group_key'])


post_save.connect(
    check_with_purchase_order,
    sender=OrderList,
    dispatch_uid='post_save_check_with_purchase_order')


def order_list_update_stage(sender, instance, created, **kwargs):
    logger.info('post_save order_list_update_stage: %s' % instance)
    if instance.stage in [OrderList.STAGE_PAY, OrderList.STAGE_RECEIVE, OrderList.STAGE_STATE]:
        from flashsale.dinghuo.tasks import task_orderlist_update_self
        task_orderlist_update_self.delay(instance)


post_save.connect(
    order_list_update_stage,
    sender=OrderList,
    dispatch_uid='post_save_update_stage')


def update_orderdetail_relationship(sender, instance, created, **kwargs):
    logger.info('post_save update_orderdetail_relationship: %s' % instance)
    if not created:
        return

    if instance.purchase_order_unikey:
        OrderDetail.objects.filter(purchase_order_unikey=instance.purchase_order_unikey).update(orderlist=instance)


post_save.connect(update_orderdetail_relationship, sender=OrderList,
                  dispatch_uid='post_save_update_orderdetail_relationship')


def update_purchaseorder_status(sender, instance, created, **kwargs):
    if instance.third_package:
        return
    logger.info('post_save update_purchaseorder_status: %s' % instance)
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
        if status in [PurchaseOrder.BOOKED, PurchaseOrder.FINISHED]:
            task_update_purchasearrangement_initial_book.delay(po)
        elif status == PurchaseOrder.BOOKED:
            task_update_purchasearrangement_initial_book.delay(po)
        else:
            task_update_purchasearrangement_status.delay(po)


post_save.connect(update_purchaseorder_status, sender=OrderList, dispatch_uid='post_save_update_purchaseorder_status')


# def orderlist_create_forecast_inbound(sender, instance, raw, **kwargs):
#     """ 根据status更新sys_status,审核通过后更新预测到货单  """
#     logger.info('post_save orderlist_create_forecast_inbound: %s' % instance)
#     # if instance.stage == OrderList.STAGE_DRAFT:
#     #     instance.sys_status = OrderList.ST_DRAFT
#     # elif instance.stage == OrderList.STAGE_DELETED:
#     #     instance.sys_status = OrderList.ST_CLOSE
#     # elif instance.stage == OrderList.STAGE_COMPLETED:
#     #     instance.sys_status = OrderList.ST_FINISHED
#     # elif instance.stage == OrderList.STAGE_STATE:
#     #     instance.sys_status = OrderList.ST_BILLING
#     # else:
#     #     instance.sys_status = OrderList.ST_APPROVAL
#     # update_model_fields(instance, update_fields=['sys_status'])
#
#     if instance.stage != OrderList.STAGE_DRAFT and instance.supplier:
#         logger.info('orderlist update forecastinbound: %s' % instance)
#         # if the orderlist purchase confirm, then create forecast inbound
#         from flashsale.forecast.apis import api_create_or_update_forecastinbound_by_orderlist
#         try:
#             with transaction.atomic():
#                 api_create_or_update_forecastinbound_by_orderlist(instance)
#         except Exception, exc:
#             logger.error('update forecast inbound:%s' % exc.message, exc_info=True)
#
#     # refresh forecast stats
#     from flashsale.forecast.models import ForecastInbound
#     from flashsale.forecast import tasks
#     forecast_inbounds = ForecastInbound.objects.filter(relate_order_set__in=[instance.id])
#     for forecast in forecast_inbounds:
#         tasks.task_forecast_update_stats_data.delay(forecast.id)
#
#
# post_save.connect(
#     orderlist_create_forecast_inbound,
#     sender=OrderList,
#     dispatch_uid='pre_save_orderlist_create_forecast_inbound')


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
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入单价')
    total_price = models.FloatField(default=0, verbose_name=u'此项总价')
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
    STATUS_CHOICES = ((1, u'已入库'), (0, u'未处理'), (2, u'已作废'))
    status = models.IntegerField(default=0, verbose_name=u'是否已经计入库存')

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
    def sku_id(self):
        return int(self.chichu_id)

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

    def change_value(self, buy_num):
        if buy_num == self.buy_quantity:
            return
        if self.status in [0, 2]:
            self.buy_quantity = buy_num
            self.save()
        elif self.status == 1:
            ori_buy_quantity = self.buy_quantity
            self.buy_quantity = buy_num
            self.save()
            change_num = buy_num - ori_buy_quantity
            self.add_into_stock(self.chichu_id, change_num)

    def add_into_stock(self, num=None):
        if num is None:
            num = self.buy_quantity
        SkuStock.add_inbound_quantity(self.chichu_id, num)

    def reset_sku_stock(self):
        sku_id = self.chichu_id
        sum_res = OrderDetail.objects.filter(chichu_id=sku_id,
                                         arrival_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME) \
            .aggregate(total=Sum('arrival_quantity'))
        total = sum_res["total"] or 0
        stat = SkuStock.get_by_sku(sku_id)
        if stat.inbound_quantity < total:
            stat.inbound_quantity = total
            stat.save(update_fields=['inbound_quantity', 'modified'])
            stat.assign(orderlist=self.orderlist)
        elif stat.inbound_quantity > total:
            stat.inbound_quantity = total
            stat.save(update_fields=['inbound_quantity', 'modified'])
            stat.relase_assign(orderlist=self.orderlist)

def update_productskustats_inbound_quantity(sender, instance, created,
                                            **kwargs):
    # instance.reset_sku_stock()
    # Note: chichu_id is actually the id of related ProductSku record.
    from shopback.items.tasks_stats import task_orderdetail_update_productskustats_inbound_quantity
    task_orderdetail_update_productskustats_inbound_quantity(instance)


post_save.connect(
    update_productskustats_inbound_quantity,
    sender=OrderDetail,
    dispatch_uid='post_save_update_productskustats_inbound_quantity')


def update_orderlist(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_orderdetail_update_orderlist
    task_orderdetail_update_orderlist.delay(instance)

#post_save.connect(update_orderlist, sender=OrderDetail, dispatch_uid='post_save_update_orderlist')


class OrderGuarantee(BaseModel):
    purchase_order = models.ForeignKey(OrderList, related_name='guarantees', verbose_name=u'订货单')
    desc = models.CharField(max_length=100, default='')


class OrderDraft(models.Model):
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
