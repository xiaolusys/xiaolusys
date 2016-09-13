# -*- coding:utf-8 -*-
import datetime
from django.db import models, transaction
from django.db.models.signals import post_save

from core.models import BaseModel
from flashsale.dinghuo import utils


class PurchaseOrder(BaseModel):
    OPEN = 1
    BOOKED = 2
    FINISHED = 3
    CANCELED = 4

    STATUS = ((OPEN, 'OPEN'), (BOOKED, 'BOOKED'), (FINISHED, 'FINISHED'), (CANCELED, 'CANCELED'))

    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'订货单唯一ID')

    supplier_id = models.IntegerField(default=0, verbose_name=u'Supplier ID')
    supplier_name = models.CharField(max_length=128, verbose_name=u'Supplier名称')

    book_num = models.IntegerField(default=0, verbose_name=u'Book数量')
    need_num = models.IntegerField(default=0, verbose_name=u'Need数量')
    # extra_num = models.IntegerField(default=0, verbose_name=u'Extra数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'Arrival数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')

    total_price = models.IntegerField(default=0, verbose_name=u'总价')

    status = models.IntegerField(choices=STATUS, default=OPEN, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_order'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货'
        verbose_name_plural = u'v2/订货表'

    @transaction.atomic
    def book(self):
        from shopback.trades.models import PackageSkuItem
        self.status = PurchaseOrder.BOOKED
        self.save()
        PurchaseDetail.objects.filter(purchase_order_unikey=self.uni_key).update(status=PurchaseOrder.BOOKED)
        pas = PurchaseArrangement.objects.filter(purchase_order_unikey=self.uni_key, status=PurchaseArrangement.EFFECT)
        pas.update(purchase_order_status=self.status, initial_book=True)
        oids = [p.oid for p in pas]
        PackageSkuItem.objects.filter(oid__in=oids).update(purchase_order_unikey=self.uni_key, book_time=datetime.datetime.now())

    @staticmethod
    def gen_purchase_order_unikey(psi):
        from shopback.trades.models import ProductSku
        supplier = ProductSku.objects.get(id=psi.sku_id).product.get_supplier()
        if not supplier:
            return 's0' # TODO@hy
        cnt = PurchaseOrder.objects.filter(supplier_id=supplier.id).exclude(status=PurchaseOrder.OPEN).count()
        return '%s-%s' % (supplier.id, cnt + 1)


class PurchaseDetail(BaseModel):
    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ')  # sku_id+purchase_order_unikey
    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一ID')

    outer_id = models.CharField(max_length=20, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    sku_id = models.CharField(db_index=True, max_length=32, verbose_name=u'sku商品id')
    title = models.CharField(max_length=128, verbose_name=u'产品名称')
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格')  # sku level info (size)

    book_num = models.IntegerField(default=0, verbose_name=u'Book数量')
    need_num = models.IntegerField(default=0, verbose_name=u'Need数量')
    extra_num = models.IntegerField(default=0, verbose_name=u'Extra数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'Arrival数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')

    status = models.IntegerField(choices=PurchaseOrder.STATUS, default=PurchaseOrder.OPEN, db_index=True,
                                 verbose_name=u'状态')

    unit_price = models.IntegerField(default=0, verbose_name=u'买入价格')
    total_price = models.IntegerField(default=0, verbose_name=u'单项总价')

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_detail'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货明细'
        verbose_name_plural = u'v2/订货明细表'

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

    @property
    def unit_price_display(self):
        return float('%.2f' % (self.unit_price * 0.01))

    @property
    def total_price_display(self):
        total = self.unit_price * self.book_num * 0.01
        return float('%.2f' % total)

    def has_extra(self):
        return self.status == PurchaseOrder.BOOKED and self.book_num > self.need_num

    def is_open(self):
        return self.status == PurchaseOrder.OPEN

    def is_booked(self):
        return self.status == PurchaseOrder.BOOKED


def update_purchase_order(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchase_detail_update_purchase_order
    task_purchase_detail_update_purchase_order.delay(instance)


post_save.connect(update_purchase_order, sender=PurchaseDetail, dispatch_uid='post_save_update_purchase_order')


def update_orderdetail(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchasedetail_update_orderdetail
    task_purchasedetail_update_orderdetail.delay(instance)


post_save.connect(update_orderdetail, sender=PurchaseDetail, dispatch_uid='post_save_update_orderdetail')


class PurchaseArrangement(BaseModel):
    EFFECT = 1
    CANCEL = 2
    STATUS = ((EFFECT, u'有效'), (CANCEL, u'取消'))

    package_sku_item_id = models.IntegerField(default=0, db_index=True, verbose_name=u'包裹ID')
    oid = models.CharField(max_length=32, db_index=True, verbose_name=u'sku交易单号')

    # PurchaseRecord.uni_key + purchase_order_unikey
    uni_key = models.CharField(max_length=32, unique=True, verbose_name=u'唯一id ')
    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一id')
    purchase_record_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'PR唯一id')

    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码')  # color-level code
    outer_sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格ID')  # size-level code

    sku_id = models.CharField(max_length=32, db_index=True, verbose_name=u'sku商品id')  # sku-level id
    title = models.CharField(max_length=128, verbose_name=u'颜色级产品名称')  # color-level product name
    sku_properties_name = models.CharField(max_length=16, blank=True, verbose_name=u'购买规格')  # sku level info (size)

    num = models.IntegerField(default=0, verbose_name=u'订购量')
    status = models.IntegerField(choices=STATUS, default=EFFECT, db_index=True,
                                 verbose_name=u'状态')
    purchase_order_status = models.IntegerField(choices=PurchaseOrder.STATUS, default=PurchaseOrder.OPEN, db_index=True,
                                                verbose_name=u'PO状态')
    initial_book = models.BooleanField(default=False, db_index=True, verbose_name=u'是否已订货')

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_arrangement'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货分配记录'
        verbose_name_plural = u'v2/订货分配表'

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

    @property
    def purchase_order(self):
        return PurchaseOrder.objects.get(unikey=self.purchase_order_unikey)

    @staticmethod
    def create(psi, purchase_order_unikey=None):
        if purchase_order_unikey is None:
            purchase_order_unikey = PurchaseOrder.gen_purchase_order_unikey(psi)
        uni_key = PurchaseArrangement.gen_purchase_arrangement_unikey(purchase_order_unikey, psi.get_purchase_uni_key())
        PurchaseArrangement(package_sku_item_id=psi.id,
                            oid=psi.oid,
                            outer_id=psi.outer_id,
                            outer_sku_id=psi.outer_sku_id,
                            sku_id=psi.sku_id,
                            title=psi.title,
                            sku_properties_name=psi.sku_properties_name,
                            uni_key=uni_key,
                            purchase_order_unikey=purchase_order_unikey,
                            purchase_record_unikey=psi.get_purchase_uni_key(),
                            num=psi.num,
                            status=psi.is_booking_needed()
                            ).save()

    @staticmethod
    def gen_purchase_arrangement_unikey(po_unikey, pr_unikey):
        return '%s-%s' % (po_unikey, pr_unikey)


def update_purchase_detail(sender, instance, created, **kwargs):
    from flashsale.dinghuo.tasks import task_purchasearrangement_update_purchasedetail
    task_purchasearrangement_update_purchasedetail.delay(instance)


post_save.connect(update_purchase_detail, sender=PurchaseArrangement, dispatch_uid='post_save_update_purchase_detail')