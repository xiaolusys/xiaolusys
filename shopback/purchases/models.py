# -*- coding:utf8 -*-
from __future__ import unicode_literals

import os
import datetime
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.models import Q, Sum, F
from django.conf import settings
from django.db import IntegrityError, transaction
from shopback import paramconfig as pcfg
from shopback.archives.models import Supplier, PurchaseType, Deposite
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product, ProductSku
from shopback.monitor.models import SystemConfig
from common.utils import format_date, update_model_fields

FINANCIAL_FIXED = 4

PURCHASE_STATUS = (
    (pcfg.PURCHASE_DRAFT, '草稿'),
    (pcfg.PURCHASE_APPROVAL, '审核'),
    (pcfg.PURCHASE_FINISH, '完成'),
    (pcfg.PURCHASE_INVALID, '作废')
)

PURCHASE_ARRIVAL_STATUS = (
    (pcfg.PD_UNARRIVAL, '未到货'),
    (pcfg.PD_PARTARRIVAL, '部分到货'),
    (pcfg.PD_FULLARRIVAL, '全部到货')
)

PURCHASE_STORAGE_STATUS = (
    (pcfg.PURCHASE_DRAFT, '草稿'),
    (pcfg.PURCHASE_APPROVAL, '审核'),
    (pcfg.PURCHASE_FINISH, '完成'),
    (pcfg.PURCHASE_INVALID, '作废')
)

PURCHASE_PAYMENT_TYPE = (
    (pcfg.PC_COD_TYPE, '货到付款'),
    (pcfg.PC_PREPAID_TYPE, '预付款'),
    (pcfg.PC_POD_TYPE, '付款提货'),
    (pcfg.PC_OTHER_TYPE, '其它')
)

PRODUCT_STATUS = (
    (pcfg.NORMAL, '有效'),
    (pcfg.DELETE, '作废')
)

PAYMENT_STATUS = (
    (pcfg.PP_WAIT_APPLY, '未申请'),
    (pcfg.PP_WAIT_PAYMENT, '待付款'),
    (pcfg.PP_HAS_PAYMENT, '已付款'),
    (pcfg.PP_INVALID, '已作废')
)

def getProductWaitReceiveNum(pId, skuId=None):
    purchaseItems = PurchaseItem.objects.filter(product_id=pId,
                                                purchase__status=pcfg.PURCHASE_APPROVAL, status=pcfg.NORMAL)

    if skuId:
        purchaseItems = purchaseItems.filter(sku_id=skuId)

    purchase_dict = purchaseItems.aggregate(total_purchase_num=Sum('purchase_num'),
                                            total_storage_num=Sum('storage_num'))
    if (purchase_dict['total_purchase_num'] is None or
                purchase_dict['total_storage_num'] is None):
        return 0
    return purchase_dict['total_purchase_num'] - purchase_dict['total_storage_num']


class Purchase(models.Model):
    """ 采购合同 """

    origin_no = models.CharField(max_length=32, unique=True, verbose_name='原合同号')

    supplier = models.ForeignKey(Supplier, null=True, blank=True, related_name='purchases', verbose_name='供应商')
    deposite = models.ForeignKey(Deposite, null=True, blank=True, related_name='purchases', verbose_name='仓库')
    purchase_type = models.ForeignKey(PurchaseType, null=True, blank=True, related_name='purchases',
                                      verbose_name='采购类型')

    forecast_date = models.DateField(null=True, blank=True, verbose_name='预测到货日期')
    post_date = models.DateField(null=True, blank=True, verbose_name='发货日期')
    service_date = models.DateField(null=True, blank=True, verbose_name='业务日期')

    creator = models.CharField(max_length=64, null=True, blank=True, verbose_name='创建人')

    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='修改日期')

    purchase_num = models.IntegerField(null=True, default=0, verbose_name='采购数量')
    storage_num = models.IntegerField(null=True, default=0, verbose_name='已入库数')

    total_fee = models.FloatField(default=0.0, verbose_name='总费用')
    prepay = models.FloatField(default=0.0, verbose_name='预付款')
    payment = models.FloatField(default=0.0, verbose_name='已付款')

    receiver_name = models.CharField(max_length=32, blank=True, verbose_name='收货人')

    status = models.CharField(max_length=32, db_index=True, choices=PURCHASE_STATUS,
                              default=pcfg.PURCHASE_DRAFT, verbose_name='订单状态')

    arrival_status = models.CharField(max_length=20, db_index=True, choices=PURCHASE_ARRIVAL_STATUS,
                                      default=pcfg.PD_UNARRIVAL, verbose_name='到货状态')

    extra_name = models.CharField(max_length=256, blank=True, verbose_name='标题')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    prepay_cent = models.FloatField(default=0.0, verbose_name='预付比例')

    attach_files = models.FileField(blank=True, upload_to='file/purchase/')

    class Meta:
        db_table = 'shop_purchases_purchase'
        app_label = 'purchases'
        verbose_name = u'采购单'
        verbose_name_plural = u'采购单列表'
        permissions = [
            ("can_purchase_check", u"审批采购合同"),
            ("can_purchase_confirm", u"确认采购完成"),
        ]

    def __unicode__(self):
        return '<%s,%s,%s>' % (str(self.id or ''), self.origin_no, self.extra_name)

    @property
    def effect_purchase_items(self):
        return self.purchase_items.filter(status=pcfg.NORMAL)

    @property
    def unfinish_purchase_items(self):
        return self.effect_purchase_items.filter(arrival_status__in=(pcfg.PD_UNARRIVAL, pcfg.PD_PARTARRIVAL))

    @property
    def uncompletepay_item(self):
        uncpay_items = []
        for item in self.effect_purchase_items:
            afford_payment = item.price * item.storage_num
            if round(item.payment, 1) < round(afford_payment, 1):
                uncpay_items.append(item)
        return uncpay_items

    @property
    def total_unpay_fee(self):
        unpay_fee = 0
        for item in self.effect_purchase_items:
            unpay_fee += item.unpay_fee

        if unpay_fee < 0:
            return 0
        return round(unpay_fee, FINANCIAL_FIXED)

    @property
    def prepay_complete(self):
        """ 如果预付款超过设定预付比例的50%，则认为预付已完成 """
        return round(self.prepay) >= round(self.total_fee * self.prepay_cent) * 0.5

    def setInvalid(self):

        self.origin_no = '%s_DELETE' % self.origin_no
        self.status = pcfg.PURCHASE_INVALID
        self.save()

    def gen_csv_tuple(self):

        pcsv = []
        pcsv.append((u'采购编号', str(self.id), u'采购标题', self.extra_name, u'供应商',
                     self.supplier and self.supplier.supplier_name or ''))
        pcsv.append((u'采购日期', self.service_date and format_date(self.service_date) or '',
                     u'预测到货日期', self.forecast_date and format_date(self.forecast_date)) or '')
        pcsv.append((u'总费用', str(self.total_fee), u'实付', str(self.payment)))
        pcsv.append(('', ''))

        pcsv.append((u'商品编码', u'商品名称', u'规格编码', u'规格名称', u'采购价', u'采购数量'))
        for item in self.effect_purchase_items.order_by('outer_id'):
            pcsv.append((item.outer_id,
                         item.name,
                         item.outer_sku_id,
                         item.properties_name,
                         str(item.price),
                         str(item.purchase_num)))

        return pcsv

    @property
    def json(self):
        """ 获取采购单JSON信息 """

        purchase_items = []
        for item in self.effect_purchase_items:
            purchase_items.append(item.json)

        return {
            'id': self.id,
            'origin_no': self.origin_no,
            'supplier_id': self.supplier and self.supplier.id or '',
            'deposite_id': self.deposite and self.deposite.id or '',
            'purchase_type_id': self.purchase_type and self.purchase_type.id or '',
            'forecast_date': self.forecast_date,
            'post_date': self.post_date,
            'service_date': self.service_date,
            'total_fee': self.total_fee,
            'payment': self.payment,
            'extra_name': self.extra_name,
            'receiver_name': self.receiver_name,
            'extra_info': self.extra_info,
            'prepay_cent': self.prepay_cent,
            'attach_files': self.attach_files,
            'status': dict(PURCHASE_STATUS).get(self.status, ''),
            'purchase_items': purchase_items
        }

    def get_ship_storages(self):
        """ 获取关联入库信息 """
        storage_map = {}
        relate_ship = PurchaseStorageRelationship.objects.filter(purchase_id=self.id)
        for ship in relate_ship:

            storage_id = ship.storage_id
            storage_item_id = ship.storage_item_id

            storage = PurchaseStorage.objects.get(id=storage_id)
            storage_item = PurchaseStorageItem.objects.get(id=storage_item_id)

            if storage_map.has_key(storage_id):
                storage_map[storage_id]['storage_items'].append({
                    'id': storage_item.id,
                    'outer_id': storage_item.outer_id,
                    'name': storage_item.name,
                    'outer_sku_id': storage_item.outer_sku_id,
                    'properties_name': storage_item.properties_name,
                    'storage_num': storage_item.storage_num,
                    'payment': ship.payment,
                    'ship_num': ship.storage_num,
                    'status': dict(PRODUCT_STATUS).get(storage_item.status)})

            else:
                storage_map[storage_id] = {
                    'id': storage.id,
                    'origin_no': storage.origin_no,
                    'extra_name': storage.extra_name,
                    'supplier_name': storage.supplier and storage.supplier.supplier_name or '',
                    'logistic_company': storage.logistic_company,
                    'out_sid': storage.out_sid,
                    'status': dict(PURCHASE_STORAGE_STATUS).get(storage.status),
                    'storage_items': [{'id': storage_item.id,
                                       'outer_id': storage_item.outer_id,
                                       'name': storage_item.name,
                                       'outer_sku_id': storage_item.outer_sku_id,
                                       'properties_name': storage_item.properties_name,
                                       'storage_num': storage_item.storage_num,
                                       'payment': ship.payment,
                                       'ship_num': ship.storage_num,
                                       'status': dict(PRODUCT_STATUS).get(storage_item.status)}]
                }
        return [v for k, v in storage_map.iteritems()]

    def pay(self, payment, prepay=False, additional=False):
        """ 采购合同付款 """

        # 如果追加额外成本
        if additional:
            per_cost_avg = round(payment / self.purchase_num, FINANCIAL_FIXED)
            for item in self.effect_purchase_items:
                item.price = F('price') + per_cost_avg
                item.payment = F('payment') + per_cost_avg * item.purchase_num
                item.save()
        elif prepay:
            for item in self.effect_purchase_items:
                item.prepay = F('prepay') + round((item.total_fee / self.total_fee) * payment, FINANCIAL_FIXED)
                item.payment = F('payment') + round((item.total_fee / self.total_fee) * payment, FINANCIAL_FIXED)
                item.save()
        else:
            for item in self.effect_purchase_items:
                item.payment = item.payment + round((item.unpay_fee / self.total_unpay_fee) * payment, FINANCIAL_FIXED)
                item.save()


class PurchaseItem(models.Model):
    """ 采购项目 """

    purchase = models.ForeignKey(Purchase, related_name='purchase_items', verbose_name='采购单')
    supplier_item_id = models.CharField(max_length=64, blank=True, verbose_name='供应商货号')

    product_id = models.IntegerField(null=True, verbose_name='商品ID')
    sku_id = models.IntegerField(null=True, verbose_name='规格ID')

    outer_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='商品编码')
    name = models.CharField(max_length=64, null=False, blank=True, verbose_name='商品名称')
    outer_sku_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='规格编码')
    properties_name = models.CharField(max_length=64, null=False, blank=True, verbose_name='规格属性')

    purchase_num = models.IntegerField(null=True, default=0, verbose_name='采购数量')
    storage_num = models.IntegerField(null=True, default=0, verbose_name='已入库数')

    discount = models.FloatField(null=True, default=0, verbose_name='折扣')
    std_price = models.FloatField(default=0.0, verbose_name='实际进价')
    price = models.FloatField(default=0.0, verbose_name='标准进价')

    total_fee = models.FloatField(default=0.0, verbose_name='总费用')
    prepay = models.FloatField(default=0.0, verbose_name='预付款')
    payment = models.FloatField(default=0.0, verbose_name='已付款')

    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='修改日期')

    status = models.CharField(max_length=12, db_index=True, choices=PRODUCT_STATUS,
                              default=pcfg.NORMAL, verbose_name='状态')

    arrival_status = models.CharField(max_length=12, db_index=True, choices=PURCHASE_ARRIVAL_STATUS,
                                      default=pcfg.PD_UNARRIVAL, verbose_name='到货状态')

    extra_info = models.CharField(max_length=1000, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_purchases_item'
        unique_together = ("purchase", "product_id", "sku_id")
        app_label = 'purchases'
        verbose_name = u'采购项目'
        verbose_name_plural = u'采购项目列表'
        permissions = [
            ("can_storage_confirm", u"确认入库数量"),
        ]

    def __unicode__(self):
        return '<%s,%s,%s>' % (str(self.id or ''), self.outer_id, self.outer_sku_id)

    @property
    def cost(self):
        return self.price > self.std_price and self.price or self.std_price

    @property
    def unpay_fee(self):
        fee = self.total_fee - self.payment
        if fee < 0:
            return 0
        return round(fee, FINANCIAL_FIXED)

    @property
    def json(self):
        """ 获取采购项JSON信息 """

        return {
            'id': self.id,
            'supplier_item_id': self.supplier_item_id,
            'outer_id': self.outer_id,
            'product_id': self.product_id,
            'sku_id': self.sku_id,
            'name': self.name,
            'outer_sku_id': self.outer_sku_id,
            'properties_name': self.properties_name,
            'total_fee': round(self.total_fee, FINANCIAL_FIXED),
            'payment': round(self.payment, FINANCIAL_FIXED),
            'purchase_num': self.purchase_num,
            'price': round(self.price, FINANCIAL_FIXED),
            'std_price': round(self.std_price, FINANCIAL_FIXED),
        }


def update_purchase_info(sender, instance, *args, **kwargs):
    """ 更新采购单信息 """

    cost = instance.storage_num and instance.payment / instance.storage_num or 0
    instance.std_price = round(cost, FINANCIAL_FIXED) or instance.price
    instance.arrival_status = instance.storage_num <= 0 and pcfg.PD_UNARRIVAL or \
                              (
                              instance.storage_num >= instance.purchase_num and pcfg.PD_FULLARRIVAL or pcfg.PD_PARTARRIVAL)
    update_model_fields(instance, update_fields=['std_price', 'arrival_status'])

    purchase = instance.purchase
    purchase_items = instance.purchase.effect_purchase_items

    aggregate_dict = purchase_items.aggregate(total_fees=Sum('total_fee'), total_payment=Sum('payment'),
                                              total_purchase_num=Sum('purchase_num'), total_prepay=Sum('prepay'),
                                              total_storage_num=Sum('storage_num'))
    purchase.total_fee = aggregate_dict['total_fees'] or 0
    purchase.payment = aggregate_dict['total_payment'] or 0
    purchase.prepay = aggregate_dict['total_prepay'] or 0
    purchase.purchase_num = aggregate_dict['total_purchase_num'] or 0
    purchase.storage_num = aggregate_dict['total_storage_num'] or 0

    if purchase_items.count() > 0:
        if purchase.storage_num == 0:
            purchase.arrival_status = pcfg.PD_UNARRIVAL
        elif purchase.purchase_num > purchase.storage_num:
            purchase.arrival_status = pcfg.PD_PARTARRIVAL
        elif purchase.purchase_num == purchase.storage_num:
            purchase.arrival_status = pcfg.PD_FULLARRIVAL

        if purchase_items.exclude(status=pcfg.PURCHASE_CLOSE).count() == 0:
            purchase.status = pcfg.PURCHASE_CLOSE

    update_model_fields(purchase,
                        update_fields=['total_fee', 'payment', 'arrival_status', 'status', 'prepay', 'purchase_num',
                                       'storage_num'])


post_save.connect(update_purchase_info, sender=PurchaseItem)


class PurchaseStorage(models.Model):
    """ 采购入库单 """

    origin_no = models.CharField(max_length=256, db_index=True, blank=True, verbose_name='原单据号')

    supplier = models.ForeignKey(Supplier, null=True, blank=True, related_name='purchase_storages', verbose_name='供应商')
    deposite = models.ForeignKey(Deposite, null=True, blank=True, related_name='purchases_storages', verbose_name='仓库')

    forecast_date = models.DateField(null=True, blank=True, verbose_name='预计到货日期')
    post_date = models.DateField(null=True, db_index=True, blank=True, verbose_name='实际到货日期')

    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='修改日期')

    storage_num = models.IntegerField(null=True, default=0, verbose_name='入库数量')

    status = models.CharField(max_length=12, db_index=True, choices=PURCHASE_STORAGE_STATUS,
                              default=pcfg.PURCHASE_DRAFT, verbose_name='状态')

    total_fee = models.FloatField(default=0.0, verbose_name='总金额')
    prepay = models.FloatField(default=0.0, verbose_name='预付额')
    payment = models.FloatField(default=0.0, verbose_name='实付款')

    logistic_company = models.CharField(max_length=64, blank=True, verbose_name='物流公司')
    out_sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name='物流编号')

    is_addon = models.BooleanField(default=False, verbose_name='加入库存')

    extra_name = models.CharField(max_length=256, blank=True, verbose_name='标题')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    is_pod = models.BooleanField(default=False, verbose_name='需付款提货')

    attach_files = models.FileField(blank=True, upload_to='file/storage/')

    class Meta:
        db_table = 'shop_purchases_storage'
        app_label = 'purchases'
        verbose_name = u'入库单'
        verbose_name_plural = u'入库单列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (str(self.id or ''), self.origin_no, self.extra_name)

    @property
    def normal_storage_items(self):
        return self.purchase_storage_items.filter(status=pcfg.NORMAL)

    @property
    def total_unpay_fee(self):
        fee = 0
        for item in self.normal_storage_items:
            fee += item.unpay_fee

        if fee < 0:
            return 0
        return round(fee, FINANCIAL_FIXED)

    def gen_csv_tuple(self):

        pcsv = []
        pcsv.append((u'入库单号', str(self.id), u'入库标题', self.extra_name, u'供应商',
                     self.supplier and self.supplier.supplier_name or ''))
        pcsv.append((u'预测到货日期', self.forecast_date and format_date(self.forecast_date),
                     u'实际到货日期', self.post_date and format_date(self.post_date)))
        pcsv.append(('', ''))

        pcsv.append((u'商品编码', u'商品名称', u'规格编码', u'规格名称', u'入库数量'))
        for item in self.purchase_storage_items.exclude(
                status__in=(pcfg.PURCHASE_CLOSE, pcfg.PURCHASE_INVALID)).order_by('outer_id'):
            pcsv.append((item.outer_id,
                         item.name,
                         item.outer_sku_id,
                         item.properties_name,
                         str(item.storage_num)))

        return pcsv

    @property
    def items_dict(self):

        prod_dict = {}
        for item in self.normal_storage_items:
            product_id = item.product_id
            sku_id = item.sku_id
            if prod_dict.has_key(product_id):
                prod_dict[product_id].append((sku_id, item.storage_num))
            else:
                prod_dict[product_id] = [(sku_id, item.storage_num)]
        return prod_dict

    @property
    def json(self):
        """ 获取入库单JSON信息 """

        purchase_items = []
        for item in self.normal_storage_items:
            purchase_items.append(item.json)

        return {
            'id': self.id,
            'origin_no': self.origin_no,
            'supplier_id': self.supplier and self.supplier.id or '',
            'deposite_id': self.deposite and self.deposite.id or '',
            'forecast_date': self.forecast_date,
            'post_date': self.post_date,
            'logistic_company': self.logistic_company,
            'out_sid': self.out_sid,
            'extra_name': self.extra_name,
            'extra_info': self.extra_info,
            'is_pod': self.is_pod,
            'attach_files': self.attach_files,
            'status': dict(PURCHASE_STORAGE_STATUS).get(self.status, ''),
            'purchase_storage_items': purchase_items,
        }

    def distribute_storage_num(self):
        """ 分配入库项数量到采购单,返回未分配的采购项 """
        # 如果入库状态非草稿状态，直接返回空
        if self.status != pcfg.PURCHASE_DRAFT:
            return {}

        unmatch_storage_items = []
        uncomplete_purchase = Purchase.objects.filter(origin_no=self.origin_no, supplier=self.supplier,
                                                      arrival_status__in=(pcfg.PD_UNARRIVAL, pcfg.PD_PARTARRIVAL),
                                                      status=pcfg.PURCHASE_APPROVAL).order_by('service_date')

        for storage_item in self.normal_storage_items:
            storage_ships = PurchaseStorageRelationship.objects.filter(
                storage_id=self.id, storage_item_id=storage_item.id)

            undist_storage_num = storage_item.storage_num - (storage_ships.aggregate(
                dist_storage_num=Sum('storage_num')).get('dist_storage_num') or 0)  # 未分配库存数
            if undist_storage_num > 0:
                product_id = storage_item.product_id
                sku_id = storage_item.sku_id
                purchase_item = None
                purchase_items = []

                for purchase in uncomplete_purchase:
                    try:
                        purchase_item = PurchaseItem.objects.get(
                            purchase=purchase, product_id=product_id, sku_id=sku_id)
                    except PurchaseItem.DoesNotExist:
                        purchase_item = None
                    else:
                        purchase_items.append(purchase_item)

                for purchase_item in purchase_items:
                    diff_num = purchase_item.purchase_num - purchase_item.storage_num  # 采购项剩余未到货数
                    if diff_num > 0:
                        storage_ship, state = PurchaseStorageRelationship.objects.get_or_create(
                            purchase_id=purchase_item.purchase.id,
                            purchase_item_id=purchase_item.id,
                            storage_id=self.id,
                            storage_item_id=storage_item.id)
                        storage_ship.product_id = product_id
                        storage_ship.sku_id = sku_id
                        storage_ship.outer_id = storage_item.outer_id
                        storage_ship.outer_sku_id = storage_item.outer_sku_id

                        diff_num = min(diff_num, undist_storage_num)
                        storage_ship.storage_num = diff_num + storage_ship.storage_num
                        storage_ship.total_fee = round(storage_ship.storage_num * purchase_item.price, FINANCIAL_FIXED)
                        storage_ship.prepay = round(
                            storage_ship.storage_num * (purchase_item.prepay / purchase_item.purchase_num),
                            FINANCIAL_FIXED)
                        storage_ship.save()

                    undist_storage_num = undist_storage_num - diff_num
                    # 如果  未分配库存数 小于等于  采购项剩余未到货数,分配后退出循环
                    if undist_storage_num <= 0:
                        break

                if undist_storage_num > 0:
                    storage_item_json = storage_item.json
                    storage_item_json['undist_storage_num'] = undist_storage_num
                    unmatch_storage_items.append(storage_item_json)

        return unmatch_storage_items

    def get_ship_purchases(self):
        """ 获取关联采购信息 """
        purchase_map = {}
        relate_ship = PurchaseStorageRelationship.objects.filter(storage_id=self.id)
        for ship in relate_ship:

            purchase_id = ship.purchase_id
            purchase_item_id = ship.purchase_item_id

            purchase = Purchase.objects.get(id=purchase_id)
            purchase_item = PurchaseItem.objects.get(id=purchase_item_id)

            if purchase_map.has_key(purchase_id):
                purchase_map[purchase_id]['purchase_items'].append({
                    'id': purchase_item.id,
                    'product_id': purchase_item.product_id,
                    'sku_id': purchase_item.sku_id,
                    'outer_id': purchase_item.outer_id,
                    'name': purchase_item.name,
                    'outer_sku_id': purchase_item.outer_sku_id,
                    'properties_name': purchase_item.properties_name,
                    'purchase_num': purchase_item.purchase_num,
                    'storage_num': purchase_item.storage_num,
                    'ship_num': ship.storage_num,
                    'arrival_status': dict(PURCHASE_ARRIVAL_STATUS).get(purchase_item.arrival_status),
                    'status': dict(PRODUCT_STATUS).get(purchase_item.status)})

            else:
                purchase_map[purchase_id] = {
                    'id': purchase.id,
                    'origin_no': purchase.origin_no,
                    'extra_name': purchase.extra_name,
                    'supplier_name': purchase.supplier and purchase.supplier.supplier_name or '未填写',
                    'service_date': purchase.service_date,
                    'purchase_num': purchase.purchase_num,
                    'storage_num': purchase.storage_num,
                    'prepay_complete': purchase.prepay_complete,
                    'arrival_status': dict(PURCHASE_ARRIVAL_STATUS).get(purchase.arrival_status),
                    'status': dict(PURCHASE_STATUS).get(purchase.status),
                    'purchase_items': [{'id': purchase_item.id,
                                        'product_id': purchase_item.product_id,
                                        'sku_id': purchase_item.sku_id,
                                        'outer_id': purchase_item.outer_id,
                                        'name': purchase_item.name,
                                        'outer_sku_id': purchase_item.outer_sku_id,
                                        'properties_name': purchase_item.properties_name,
                                        'purchase_num': purchase_item.purchase_num,
                                        'storage_num': purchase_item.storage_num,
                                        'ship_num': ship.storage_num,
                                        'arrival_status': dict(PURCHASE_ARRIVAL_STATUS).get(
                                            purchase_item.arrival_status),
                                        'status': dict(PRODUCT_STATUS).get(purchase_item.status)}]
                }
        return [v for k, v in purchase_map.iteritems()]


class PurchaseStorageItem(models.Model):
    """ 采购入库项目 """

    purchase_storage = models.ForeignKey(PurchaseStorage, related_name='purchase_storage_items', verbose_name='入库单')
    supplier_item_id = models.CharField(max_length=64, blank=True, verbose_name='供应商货号')

    product_id = models.IntegerField(null=True, verbose_name='商品ID')
    sku_id = models.IntegerField(null=True, verbose_name='规格ID')

    outer_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='商品编码')
    name = models.CharField(max_length=64, null=False, blank=True, verbose_name='商品名称')
    outer_sku_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='规格编码')
    properties_name = models.CharField(max_length=64, null=False, blank=True, verbose_name='规格属性')

    storage_num = models.IntegerField(null=True, default=0, verbose_name='入库数量')

    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='修改日期')

    total_fee = models.FloatField(default=0.0, verbose_name='总金额')
    prepay = models.FloatField(default=0.0, verbose_name='预付额')
    payment = models.FloatField(default=0.0, verbose_name='已付款')

    status = models.CharField(max_length=12, db_index=True, choices=PRODUCT_STATUS,
                              default=pcfg.NORMAL, verbose_name='状态')

    is_addon = models.BooleanField(default=False, verbose_name='加入库存')

    extra_info = models.CharField(max_length=1000, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_purchases_storageitem'
        unique_together = ("purchase_storage", "product_id", "sku_id")
        app_label = 'purchases'
        verbose_name = u'入库项目'
        verbose_name_plural = u'入库项目列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.outer_sku_id, self.properties_name)

    @property
    def unpay_fee(self):
        fee = self.total_fee - self.prepay - self.payment
        if fee < 0:
            return 0
        return round(fee, FINANCIAL_FIXED)

    @property
    def json(self):
        """ 获取入库项JSON信息 """
        return {
            'id': self.id,
            'supplier_item_id': self.supplier_item_id,
            'product_id': self.product_id,
            'sku_id': self.sku_id,
            'outer_id': self.outer_id,
            'name': self.name,
            'outer_sku_id': self.outer_sku_id,
            'properties_name': self.properties_name,
            'storage_num': self.storage_num,
        }


def update_storage_info(sender, instance, *args, **kwargs):
    """ 更新采购单信息 """

    storage = instance.purchase_storage
    storage_items = storage.normal_storage_items

    storage_dict = storage_items.aggregate(total_fees=Sum('total_fee'), total_storage_num=Sum('storage_num'),
                                           total_prepay=Sum('prepay'), total_payment=Sum('payment'))

    storage.total_fee = storage_dict['total_fees'] or 0
    storage.prepay = storage_dict['total_prepay'] or 0
    storage.payment = storage_dict['total_payment'] or 0
    storage.storage_num = storage_dict['total_storage_num'] or 0

    update_model_fields(storage, update_fields=['total_fee', 'prepay', 'payment', 'storage_num'])


post_save.connect(update_storage_info, sender=PurchaseStorageItem)


class PurchaseStorageRelationship(models.Model):
    """ 采购与入库商品项目关联 """

    purchase_id = models.IntegerField(verbose_name='采购单ID')
    purchase_item_id = models.IntegerField(verbose_name='采购项目ID')
    storage_id = models.IntegerField(db_index=True, verbose_name='入库单ID')
    storage_item_id = models.IntegerField(verbose_name='入库项目ID')

    product_id = models.IntegerField(null=True, verbose_name='商品ID')
    sku_id = models.IntegerField(null=True, verbose_name='规格ID')

    outer_id = models.CharField(max_length=32, verbose_name='商品编码')
    outer_sku_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='规格编码')

    is_addon = models.BooleanField(default=False, verbose_name='确认收货')
    storage_num = models.IntegerField(null=True, default=0, verbose_name='关联入库数量')
    total_fee = models.FloatField(default=0.0, verbose_name='应付费用')
    prepay = models.FloatField(default=0.0, verbose_name='预付费用')
    payment = models.FloatField(default=0.0, verbose_name='支付费用')

    class Meta:
        db_table = 'shop_purchases_relationship'
        unique_together = (("purchase_id", "purchase_item_id", "storage_id", "storage_item_id"),)
        app_label = 'purchases'
        verbose_name = u'采购入库关联'
        verbose_name_plural = u'采购入库关联'

    def __unicode__(self):
        return '<%s,%s,%d>' % (self.outer_id, self.outer_sku_id, self.storage_num)

    @property
    def unpay_fee(self):
        fee = self.total_fee - self.prepay - self.payment
        if fee < 0:
            return 0
        return fee

    def confirm_storage(self, cost_addon=False):
        """ 确认关联入库 """
        prod = Product.objects.get(id=self.product_id)
        purchase_item = PurchaseItem.objects.get(id=self.purchase_item_id)

        if self.sku_id:
            prod_sku = ProductSku.objects.get(id=self.sku_id, product=prod)

            if cost_addon:
                prod_sku.cost = purchase_item.price
                prod_sku.save()
        else:

            if cost_addon:
                prod.cost = purchase_item.price
                prod.save()

        self.is_addon = True
        self.save()


def update_purchaseitem_storage_and_fee(sender, instance, *args, **kwargs):
    """ 更新入库单，采购单项目信息 """
    # 如果入库项审核通过，则可以更新入库项的库存到采购单
    storage_item = PurchaseStorageItem.objects.get(id=instance.storage_item_id)

    relation_dict = PurchaseStorageRelationship.objects.filter(
        storage_id=instance.storage_id, storage_item_id=instance.storage_item_id) \
        .aggregate(total_fees=Sum('total_fee'), total_payment=Sum('payment'), total_prepay=Sum('prepay'))

    storage_item.total_fee = relation_dict.get('total_fees') or 0
    storage_item.prepay = relation_dict.get('total_prepay') or 0
    storage_item.payment = relation_dict.get('total_payment') or 0
    storage_item.save()
    if not instance.is_addon:
        return

    purchase_item = PurchaseItem.objects.get(id=instance.purchase_item_id)

    relation_dict = PurchaseStorageRelationship.objects.filter(
        purchase_id=instance.purchase_id, purchase_item_id=instance.purchase_item_id, is_addon=True) \
        .aggregate(total_storage_num=Sum('storage_num'))

    total_storage_num = relation_dict.get('total_storage_num') or 0

    purchase_item.arrival_status = total_storage_num <= 0 and pcfg.PD_UNARRIVAL or \
                                   (
                                   total_storage_num >= purchase_item.purchase_num and pcfg.PD_FULLARRIVAL or pcfg.PD_PARTARRIVAL)
    purchase_item.storage_num = total_storage_num
    purchase_item.save()


# 修改，删除采购入库关联项时，应更新其对应的采购项信息
post_save.connect(update_purchaseitem_storage_and_fee, sender=PurchaseStorageRelationship)

post_delete.connect(update_purchaseitem_storage_and_fee, sender=PurchaseStorageRelationship)


class PurchasePayment(models.Model):
    """ 
        采购付款单 付款类型：
        1,货到付款
        2,预付款
        3,付款提货
    """
    origin_nos = models.TextField(blank=True, verbose_name='原单据号')

    pay_type = models.CharField(max_length=6, db_index=True, choices=PURCHASE_PAYMENT_TYPE, verbose_name='付款类型')
    apply_time = models.DateTimeField(null=True, blank=True, verbose_name='申请日期')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='付款日期')
    payment = models.FloatField(default=0, verbose_name='付款金额')

    supplier = models.ForeignKey(Supplier, null=True, blank=True, related_name='purchase_payments', verbose_name='收款方')

    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='修改日期')

    status = models.CharField(max_length=12, db_index=True, choices=PAYMENT_STATUS,
                              default=pcfg.PP_WAIT_APPLY, verbose_name='状态')

    applier = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='申请人')
    cashier = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='付款人')

    pay_no = models.CharField(max_length=256, db_index=True, blank=True, verbose_name='付款流水单号')
    pay_bank = models.CharField(max_length=128, blank=True, verbose_name='付款银行(平台)')

    extra_info = models.TextField(max_length=1000, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_purchases_payment'
        app_label = 'purchases'
        verbose_name = u'采购付款单'
        verbose_name_plural = u'采购付款单列表'
        permissions = [
            ("can_payment_confirm", u"确认采购付款"),
        ]

    def __unicode__(self):
        return '<%s,%s,%.2f>' % (str(self.id or ''), self.pay_type, self.payment)

    def invalid(self):
        self.status = pcfg.PURCHASE_INVALID
        self.save()

    def append_origins_no(self, origin_no):
        """ 将原始单号加入付款信息 """
        ono_set = set(self.origin_nos.split(','))
        if origin_no not in ono_set:
            ono_set.add(origin_no)
            self.origin_nos = ','.join(ono_set)
            self.save()

    def unappend_origins_no(self, origin_no):
        """ 将原始单号移除付款信息 """
        ono_set = set(self.origin_nos.split(','))
        if origin_no in ono_set:
            ono_set.remove(origin_no)
            self.origin_nos = ','.join(ono_set)
            self.save()

    @property
    def json(self):

        purchase_dict = None
        storages_dict = {}

        for item in self.payment_items.all():
            purchase_id = item.purchase_id
            storage_id = item.storage_id
            if purchase_id:
                if purchase_dict:
                    purchase_dict['dst_payment'] += item.payment
                    purchase_dict['payment_items'].append(item.json)
                else:
                    purchase = Purchase.objects.get(id=purchase_id)
                    purchase_dict = {
                        "id": purchase.id,
                        "title": purchase.extra_name,
                        'origin_no': purchase.origin_no,
                        "service_date": purchase.service_date,
                        "purchase_num": purchase.purchase_num,
                        "storage_num": purchase.storage_num,
                        "total_fee": purchase.total_fee,
                        "unpay_fee": purchase.total_unpay_fee,
                        "payment": purchase.payment,
                        "dst_payment": item.payment,
                        "payment_items": [item.json]
                    }
            else:
                if storages_dict.has_key(storage_id):
                    storages_dict[storage_id]['dst_payment'] += item.payment
                    storages_dict[storage_id]['payment_items'].append(item.json)
                else:
                    storage = PurchaseStorage.objects.get(id=storage_id)
                    storages_dict[storage_id] = {
                        "id": storage.id,
                        'origin_no': storage.origin_no,
                        "title": storage.extra_name,
                        "post_date": storage.post_date,
                        "storage_num": storage.storage_num,
                        "total_fee": storage.total_fee,
                        "unpay_fee": storage.total_unpay_fee,
                        "payment": round(storage.payment + storage.prepay, FINANCIAL_FIXED),
                        "dst_payment": item.payment,
                        "payment_items": [item.json]
                    }
        return {'id': self.id,
                'payment': self.payment,
                'applier': self.applier,
                "supplier": self.supplier and self.supplier.supplier_name or '',
                'extra_info': self.extra_info,
                'purchase': purchase_dict,
                'storages': storages_dict.values()}

    def cal_purchase_payment(self, purchase, payment, cal_by=0):
        """ 生成采购合同付款项：
            cal_by==0,按待付款数分配
            cal_by==1,按采购数量分配
            cal_by==2,按采购金额分配
        """
        total_unpay_fee = purchase.total_unpay_fee
        total_fee = purchase.total_fee
        total_purchase_num = purchase.purchase_num
        per_cost_avg = 0

        for item in purchase.effect_purchase_items:

            if cal_by == 1:
                per_cost_avg = payment / total_purchase_num
                item_payment = round(item.purchase_num * per_cost_avg, FINANCIAL_FIXED)
            elif cal_by == 2:
                item_payment = round((item.total_fee / total_fee) * payment, FINANCIAL_FIXED)
            else:
                if total_unpay_fee <= 0:
                    raise Exception(u'待付款金额不能为零')

                item_payment = round((item.unpay_fee / total_unpay_fee) * payment, FINANCIAL_FIXED)
            payment_item, state = PurchasePaymentItem.objects.get_or_create(
                purchase_payment=self, purchase_id=purchase.id, purchase_item_id=item.id)
            payment_item.product_id = item.product_id
            payment_item.sku_id = item.sku_id
            payment_item.outer_id = item.outer_id
            payment_item.outer_sku_id = item.outer_sku_id
            payment_item.name = item.name
            payment_item.properties_name = item.properties_name
            payment_item.payment = item_payment
            payment_item.save()

    def cal_storage_payment(self, storage, payment, cal_by=0):
        """ 生成入库单付款项：
            cal_by==0,按待付款数分配
            cal_by==1,按采购数量分配
            cal_by==2,按采购金额分配
        """
        total_unpay_fee = storage.total_unpay_fee
        total_fee = storage.total_fee
        total_storage_num = storage.storage_num
        per_cost_avg = 0

        for item in storage.normal_storage_items:
            if cal_by == 1:
                per_cost_avg = payment / total_storage_num
                item_payment = round(item.storage_num * per_cost_avg, FINANCIAL_FIXED)
            elif cal_by == 2:
                item_payment = round((item.total_fee / total_fee) * payment, FINANCIAL_FIXED)
            else:
                if total_unpay_fee <= 0:
                    raise Exception(u'待付款金额不能为零')
                item_payment = round((item.unpay_fee / total_unpay_fee) * payment, FINANCIAL_FIXED)

            payment_item, state = PurchasePaymentItem.objects.get_or_create(
                purchase_payment=self, storage_id=storage.id, storage_item_id=item.id)
            payment_item.product_id = item.product_id
            payment_item.sku_id = item.sku_id
            payment_item.outer_id = item.outer_id
            payment_item.outer_sku_id = item.outer_sku_id
            payment_item.name = item.name
            payment_item.properties_name = item.properties_name
            payment_item.payment = item_payment
            payment_item.save()

    def apply_for_prepay(self, purchase, payment):
        """ 生成预付款项 """
        self.append_origins_no(purchase.origin_no)
        self.cal_purchase_payment(purchase, payment, cal_by=0)

    def apply_for_podpay(self, storage, payment):
        """ 生成付款提货付款项 """
        self.append_origins_no(storage.origin_no)
        self.cal_storage_payment(storage, payment, cal_by=0)

    def apply_for_codpay(self, storage, payment):
        """ 生成货到付款项 """
        self.append_origins_no(storage.origin_no)
        self.cal_storage_payment(storage, payment, cal_by=0)

    def apply_for_otherpay(self, purchase, storages, payment):
        """ 生成其他付款项 """
        per_cost_avg = 0
        if purchase:
            self.cal_purchase_payment(purchase, payment, cal_by=1)

        total_storage_num = 0
        for storage in storages:
            total_storage_num += storage.storage_num

        for storage in storages:
            self.cal_storage_payment(storage, (storage.storage_num / total_storage_num) * payment, cal_by=1)

    def confirm_pay(self, cashier):
        """ 确认付款 """
        if self.pay_type == pcfg.PC_PREPAID_TYPE:
            for item in self.payment_items.all():
                purchase_item = PurchaseItem.objects.get(id=item.purchase_item_id)
                purchase_item.payment += item.payment
                purchase_item.prepay += item.payment
                purchase_item.save()

        elif self.pay_type in (pcfg.PC_COD_TYPE, pcfg.PC_POD_TYPE):
            for item in self.payment_items.all():
                storage_item = PurchaseStorageItem.objects.get(id=item.storage_item_id)
                relate_ships = PurchaseStorageRelationship.objects.filter(
                    storage_id=storage_item.purchase_storage.id, storage_item_id=storage_item.id)

                total_unpay_fee = storage_item.unpay_fee

                if total_unpay_fee <= 0 and item.payment > 0:
                    raise Exception('付款项有异常，待付费用为:0,实际付款费用为:%2f' % item.payment)

                if total_unpay_fee <= 0:
                    continue

                for ship in relate_ships:
                    ship_payment = round((ship.unpay_fee / total_unpay_fee) * item.payment, FINANCIAL_FIXED)
                    ship.payment += ship_payment
                    ship.save()

                    # 更新采购项付款金额
                    purchase_item = PurchaseItem.objects.get(id=ship.purchase_item_id)
                    purchase_item.payment += ship_payment
                    purchase_item.save()

        else:
            for item in self.payment_items.all():
                if item.purchase_id:
                    purchase_item = PurchaseItem.objects.get(id=item.purchase_item_id)
                    purchase_item.payment += item.payment
                    purchase_item.save()

                if item.storage_id:
                    storage_item = PurchaseStorageItem.objects.get(id=item.storage_item_id)
                    relate_ships = PurchaseStorageRelationship.objects.filter(
                        storage_id=storage_item.purchase_storage.id, storage_item_id=storage_item.id)

                    total_num = storage_item.storage_num

                    for ship in relate_ships:
                        ship_payment = round((ship.storage_num / total_num) * item.payment, FINANCIAL_FIXED)
                        ship.payment += ship_payment
                        ship.save()

                        # 更新采购项付款金额
                        purchase_item = PurchaseItem.objects.get(id=ship.purchase_item_id)
                        purchase_item.payment += ship_payment
                        purchase_item.save()

        self.status = pcfg.PP_HAS_PAYMENT
        self.cashier = cashier
        self.save()


class PurchasePaymentItem(models.Model):
    """ 采购付款单付款项 """

    purchase_payment = models.ForeignKey(PurchasePayment, related_name='payment_items', verbose_name='付款单')

    purchase_id = models.IntegerField(null=True, blank=True, verbose_name='采购单ID')
    purchase_item_id = models.IntegerField(null=True, blank=True, verbose_name='采购项目ID')

    storage_id = models.IntegerField(null=True, blank=True, verbose_name='入库单ID')
    storage_item_id = models.IntegerField(null=True, blank=True, verbose_name='入库项目ID')

    product_id = models.IntegerField(null=True, verbose_name='商品ID')
    sku_id = models.IntegerField(null=True, verbose_name='规格ID')

    outer_id = models.CharField(max_length=32, verbose_name='商品编码')
    name = models.CharField(max_length=64, null=False, blank=True, verbose_name='商品名称')
    outer_sku_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='规格编码')
    properties_name = models.CharField(max_length=64, null=False, blank=True, verbose_name='规格属性')

    payment = models.FloatField(default=0.0, verbose_name='支付费用')

    class Meta:
        db_table = 'shop_purchases_paymentitem'
        app_label = 'purchases'
        verbose_name = u'付款项目'
        verbose_name_plural = u'付款项目列表'

    def __unicode__(self):
        return '<%s,%.2f>' % (str(self.id or ''), self.payment)

    @property
    def json(self):
        if self.purchase_id:
            purchase_item = PurchaseItem.objects.get(id=self.purchase_item_id)
            return {
                "id": self.id,
                "purchase_id": self.purchase_id,
                "purchase_item_id": self.purchase_item_id,
                "dst_payment": self.payment,
                "product_id": self.product_id,
                "sku_id": self.sku_id,
                "outer_id": self.outer_id,
                "name": self.name,
                "outer_sku_id": self.outer_sku_id,
                "properties_name": self.properties_name,
                "price": purchase_item.price,
                "purchase_num": purchase_item.purchase_num,
                "storage_num": purchase_item.storage_num,
                "total_fee": purchase_item.total_fee,
                "payment": purchase_item.payment,
                "unpay_fee": purchase_item.unpay_fee,
            }
        else:
            storage_item = PurchaseStorageItem.objects.get(id=self.storage_item_id)
            return {
                "id": self.id,
                "storage_id": self.storage_id,
                "storage_item_id": self.storage_item_id,
                "dst_payment": self.payment,
                "product_id": self.product_id,
                "sku_id": self.sku_id,
                "outer_id": self.outer_id,
                "name": self.name,
                "outer_sku_id": self.outer_sku_id,
                "properties_name": self.properties_name,
                "storage_num": storage_item.storage_num,
                "total_fee": storage_item.total_fee,
                "payment": round(storage_item.payment + storage_item.prepay, FINANCIAL_FIXED),
                "unpay_fee": storage_item.unpay_fee
            }
