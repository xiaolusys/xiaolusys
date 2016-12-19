# -*- coding:utf-8 -*-
import datetime
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.signals import post_save
from django.conf import settings

from core.models import BaseModel
from flashsale.dinghuo import utils
from shopback.trades.constants import PSI_STATUS
import logging

logger = logging.getLogger(__name__)


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
    # inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')

    total_price = models.IntegerField(default=0, verbose_name=u'总价')

    status = models.IntegerField(choices=STATUS, default=OPEN, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_order'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货'
        verbose_name_plural = u'v2/订货表'

    @transaction.atomic
    def book(self, third_package=False):
        from shopback.trades.models import PackageSkuItem
        self.status = PurchaseOrder.BOOKED
        self.save()
        self.details.update(status=PurchaseOrder.BOOKED)
        self.arrangements.filter(status=PurchaseArrangement.EFFECT).update(purchase_order_status=self.status, initial_book=True)
        oids = [pa.oid for pa in self.arrangements.filter(status=PurchaseArrangement.EFFECT)]
        book_time = datetime.datetime.now()
        # PackageSkuItem.objects.filter(oid__in=oids).update(purchase_order_unikey=self.uni_key, booked_time=book_time)
        if not third_package:
            for p in PackageSkuItem.objects.filter(oid__in=oids):
                p.set_status_booked(self.uni_key)
        else:
            for p in PackageSkuItem.objects.filter(oid__in=oids):
                p.set_status_virtual_booked(self.uni_key)

    @staticmethod
    def gen_purchase_order_unikey(psi):
        from shopback.trades.models import ProductSku
        supplier = ProductSku.objects.get(id=psi.sku_id).product.get_supplier()
        if not supplier:
            return 's0'  # TODO@hy
        cnt = PurchaseOrder.objects.filter(supplier_id=supplier.id).exclude(status=PurchaseOrder.OPEN).count()
        return '%s-%s' % (supplier.id, cnt + 1)

    @property
    def details(self):
        return PurchaseDetail.objects.filter(purchase_order_unikey=self.uni_key)

    @property
    def arrangements(self):
        return PurchaseArrangement.objects.filter(purchase_order_unikey=self.uni_key)

    @property
    def skuitems(self):
        from shopback.trades.models import PackageSkuItem
        return PackageSkuItem.objects.filter(purchase_order_unikey=self.uni_key)

    @property
    def supplier(self):
        return PurchaseOrder.get_supplier(self.uni_key)

    @staticmethod
    def get_supplier(purchase_order_unikey):
        from supplychain.supplier.models import SaleSupplier
        supplier_id = int(purchase_order_unikey.split('-')[0])
        return SaleSupplier.objects.get(id=supplier_id)

    @staticmethod
    def restat(purchase_order_unikey):
        res = PurchaseDetail.objects.filter(purchase_order_unikey=purchase_order_unikey). \
            aggregate(b_num=Sum('book_num'), n_num=Sum('need_num'), a_num=Sum('arrival_num'))
        book_num = res['b_num'] or 0
        need_num = res['n_num'] or 0
        arrival_num = res['a_num'] or 0
        supplier = PurchaseOrder.get_supplier(purchase_order_unikey)
        po = PurchaseOrder.objects.filter(uni_key=purchase_order_unikey).first()
        if not po:
            po = PurchaseOrder(uni_key=purchase_order_unikey, supplier_id=supplier.id,
                               supplier_name=supplier.supplier_name,
                               book_num=book_num, need_num=need_num, arrival_num=arrival_num)
            po.save()
        else:
            if po.status == PurchaseOrder.OPEN:
                if po.book_num != book_num or po.need_num != need_num or po.arrival_num != arrival_num:
                    po.book_num = book_num
                    po.need_num = need_num
                    po.arrival_num = arrival_num
                    po.save(update_fields=['book_num', 'need_num', 'arrival_num', 'modified'])
        po.sync_order_list()

    def restatall(self):
        for pd in self.details.all():
            pd.restat()

    def sync_order_list(self):
        from flashsale.dinghuo.models import OrderList
        ol = OrderList.objects.filter(purchase_order_unikey=self.uni_key).first()
        if not ol:
            supplier = self.supplier
            if not supplier:
                return
            now = datetime.datetime.now()
            ol = OrderList(purchase_order_unikey=self.uni_key, order_amount=self.total_price,
                           supplier_id=supplier.id, created_by=OrderList.CREATED_BY_MACHINE,
                           status=OrderList.SUBMITTING, note=u'-->%s:动态生成订货单' % now.strftime('%m月%d %H:%M'))
            ol.save()
        else:
            if ol.order_amount != self.total_price or ol.purchase_total_num != self.book_num:
                if ol.is_open():
                    ol.order_amount = self.total_price
                    ol.purchase_total_num = self.book_num
                    ol.save(update_fields=['order_amount', 'updated', 'purchase_total_num'])
                else:
                    logger.error("HY error: trying to modify booked order_list| ol.id: %s" % (ol.id,))
            else:
                ol.save(update_fields=['updated'])


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
    # extra_num = models.IntegerField(default=0, verbose_name=u'Extra数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'Arrival数量')
    # inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')

    status = models.IntegerField(choices=PurchaseOrder.STATUS, default=PurchaseOrder.OPEN, db_index=True,
                                 verbose_name=u'状态')

    unit_price = models.IntegerField(default=0, verbose_name=u'买入单价')
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

    @property
    def sku(self):
        from shopback.items.models import ProductSku
        return ProductSku.objects.get(id=self.sku_id)

    @property
    def purchase_order(self):
        return PurchaseOrder.objects.get(uni_key=self.purchase_order_unikey)

    @property
    def arrangements(self):
        return self.purchase_order.arrangements.filter(sku_id=self.sku_id, status=1, num__gt=0)

    def has_extra(self):
        return self.status == PurchaseOrder.BOOKED and self.book_num > self.need_num

    def is_open(self):
        return self.status == PurchaseOrder.OPEN

    def is_booked(self):
        return self.status == PurchaseOrder.BOOKED

    @staticmethod
    def create(pa):
        uni_key = '%s-%s' % (pa.sku_id, pa.purchase_order_unikey)
        res = PurchaseArrangement.objects.filter(purchase_order_unikey=pa.purchase_order_unikey,
                                                 sku_id=pa.sku_id, status=PurchaseArrangement.EFFECT).aggregate(
            total=Sum('num'))
        total = res['total'] or 0
        unit_price = int(pa.sku.cost * 100)
        total_price = int(pa.sku.cost * 100 * total)
        pd = PurchaseDetail(uni_key=uni_key, purchase_order_unikey=pa.purchase_order_unikey,
                            unit_price=unit_price, book_num=total, need_num=total,
                            total_price=total_price)
        fields = ['outer_id', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name']
        utils.copy_fields(pd, pa, fields)
        pd.save()
        pd.sync_order_detail()
        PurchaseOrder.restat(pa.purchase_order_unikey)
        return pd

    def restat(self):
        res = PurchaseArrangement.objects.filter(purchase_order_unikey=self.purchase_order_unikey,
                                                 sku_id=self.sku_id, status=PurchaseArrangement.EFFECT).aggregate(
            total=Sum('num'))
        total = res['total'] or 0
        unit_price = int(self.sku.cost * 100)
        total_price = int(self.sku.cost * 100 * total)
        if self.book_num != total or self.total_price != total_price:
            self.book_num = total
            self.need_num = total
            self.unit_price = unit_price
            self.total_price = unit_price * total
            self.save(update_fields=['book_num', 'need_num', 'unit_price', 'total_price', 'modified'])
        self.sync_order_detail()
        PurchaseOrder.restat(self.purchase_order_unikey)

    def sync_order_detail(pd):
        from flashsale.dinghuo.models import OrderDetail, OrderList
        od = OrderDetail.objects.filter(purchase_detail_unikey=pd.uni_key).first()
        if not od:
            product = utils.get_product(pd.sku_id)
            od = OrderDetail(product_id=product.id, outer_id=pd.outer_id, product_name=pd.title, chichu_id=pd.sku_id,
                             product_chicun=pd.sku_properties_name,
                             buy_quantity=pd.book_num,
                             buy_unitprice=pd.unit_price_display,
                             total_price=pd.total_price_display,
                             purchase_detail_unikey=pd.uni_key,
                             purchase_order_unikey=pd.purchase_order_unikey)
            ol = OrderList.objects.filter(purchase_order_unikey=pd.purchase_order_unikey).first()
            if ol:
                od.orderlist_id = ol.id
            od.save()
        else:
            if od.orderlist_id and OrderList.objects.get(id=od.orderlist_id).stage > 0:
                return
            if od.total_price != pd.total_price or od.buy_quantity != pd.book_num:
                od.buy_quantity = pd.book_num
                od.buy_unitprice = pd.unit_price_display
                od.total_price = pd.total_price_display
                od.save(update_fields=['buy_quantity', 'buy_unitprice', 'total_price', 'updated'])

    def set_pa_inbound(self):
        self.arrangements.update(inbound_in=False)
        num = self.arrival_num
        for pa in self.arrangements:
            if num >= pa.num:
                pa.inbound_in = True
                num -= pa.num
                pa.save()


# def update_purchase_order(sender, instance, created, **kwargs):
#     from flashsale.dinghuo.tasks import task_purchase_detail_update_purchase_order
#     task_purchase_detail_update_purchase_order.delay(instance)
#


# def update_orderdetail(sender, instance, created, **kwargs):
#     from flashsale.dinghuo.tasks import task_purchasedetail_update_orderdetail
#     task_purchasedetail_update_orderdetail.delay(instance)

#
# if not settings.CLOSE_CELERY:
#     post_save.connect(update_purchase_order, sender=PurchaseDetail, dispatch_uid='post_save_update_purchase_order')
#     # post_save.connect(update_orderdetail, sender=PurchaseDetail, dispatch_uid='post_save_update_orderdetail')


class PurchaseArrangement(BaseModel):
    EFFECT = 1
    CANCEL = 2
    STATUS = ((EFFECT, u'有效'), (CANCEL, u'取消'))

    package_sku_item_id = models.IntegerField(default=0, db_index=True, verbose_name=u'包裹ID')
    oid = models.CharField(max_length=32, db_index=True, verbose_name=u'sku交易单号')

    # PurchaseRecord.uni_key + purchase_order_unikey
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一id ')
    purchase_order_unikey = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'订货单唯一id')
    purchase_record_unikey = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'PR唯一id')

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
    gen_order = models.BooleanField(default=False)
    inbound_in = models.BooleanField(default=False, db_index=True, verbose_name=u'是否已入仓')

    class Meta:
        db_table = 'flashsale_dinghuo_purchase_arrangement'
        app_label = 'dinghuo'
        verbose_name = u'v2/订货分配记录'
        verbose_name_plural = u'v2/订货分配表'

    def __unicode__(self):
        return "%s-%s/%s" % (self.id, self.title, self.sku_properties_name)

    @property
    def purchase_order(self):
        return PurchaseOrder.objects.get(uni_key=self.purchase_order_unikey)

    @property
    def sku(self):
        from shopback.items.models import ProductSku
        return ProductSku.objects.get(id=self.sku_id)

    @property
    def skuitem(self):
        from shopback.trades.models import PackageSkuItem
        return PackageSkuItem.objects.get(oid=self.oid)

    @staticmethod
    def create(psi, purchase_order_unikey=None):
        if purchase_order_unikey is None:
            purchase_order_unikey = PurchaseOrder.gen_purchase_order_unikey(psi)
        uni_key = PurchaseArrangement.gen_purchase_arrangement_unikey(purchase_order_unikey, psi.get_purchase_uni_key())
        pa = PurchaseArrangement(package_sku_item_id=psi.id,
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
                            status=PurchaseArrangement.EFFECT if psi.is_booking_needed() else PurchaseArrangement.CANCEL
                            )
        pa.save()
        return pa

    def reset_purchase_order(self):
        if not self.initial_book:
            psi = self.skuitem
            pa_new_uni_key = PurchaseOrder.gen_purchase_order_unikey(psi)
            self.purchase_order_unikey = pa_new_uni_key
            self.uni_key = PurchaseArrangement.gen_purchase_arrangement_unikey(pa_new_uni_key,
                                                                               psi.get_purchase_uni_key())
            self.status = PurchaseArrangement.EFFECT

    @staticmethod
    def gen_purchase_arrangement_unikey(po_unikey, pr_unikey):
        return '%s-%s' % (po_unikey, pr_unikey)

    def generate_order(pa, retry=False):
        # 已执行过本方法的再次执行没有问题 应该注意 initial_book为True和status为１正常不该执行此方法
        if pa.purchase_order_unikey == 's0':
            return
        PurchaseArrangement.objects.filter(id=pa.id).update(gen_order=True)
        uni_key = utils.gen_purchase_detail_unikey(pa)
        pd = PurchaseDetail.objects.filter(uni_key=uni_key).first()
        if not pd:
            PurchaseDetail.create(pa)
        else:
            if pd.is_open():
                pd.restat()
            else:
                if retry:
                    pa.reset_purchase_order()
                    # pa.save() 防止死循环
                    PurchaseArrangement.objects.filter(id=pa.id).update(purchase_order_unikey=pa.purchase_order_unikey,
                                                                        uni_key=pa.uni_key,
                                                                        status=pa.status)
                    pa = PurchaseArrangement.objects.get(id=pa.id)
                    pa.generate_order(retry=False)
                else:
                    raise Exception(u'PA(%s)对应的订货单(%s)已订货无法再订' % (pa.oid, pa.purchase_order_unikey))
        pa.skuitem.set_status_prepare_book()

    def get_purchase_detail_unikey(pa):
        sku_id = pa.sku_id
        sku_id = sku_id.strip()
        return "%s-%s" % (sku_id, pa.purchase_order_unikey)

    # def generate_order(pa, retry=True):
    #     if not pa.gen_order:
    #         uni_key = utils.gen_purchase_detail_unikey(pa)
    #         pd = PurchaseDetail.objects.filter(uni_key=uni_key).first()
    #         if not pd:
    #             PurchaseDetail.create(pa)
    #         else:
    #             if pd.is_open():
    #                 pd.restat()
    #             else:
    #                 if retry:
    #                     pa.reset_purchase_order()
    #                     pa.save()
    #                     pa.generate_order(retry=False)
    #                 else:
    #                     raise Exception(u'PA(%s)对应的订货单()已订货无法再订' % (pa.oid, pa.purchase_order_unikey))
    #         pa.gen_order = True
    #         pa.save()

    def cancel(self):
        """
            仅在未订货情况下可以取消
        """
        if self.initial_book:
            return
            # raise Exception(u'此订单已订货:%s' % self.oid)
        self.status = PurchaseArrangement.CANCEL
        self.save()
        uni_key = utils.gen_purchase_detail_unikey(self)
        pd = PurchaseDetail.objects.filter(uni_key=uni_key).first()
        if pd and pd.is_open():
            pd.restat()
            pd.save()


def update_purchase_detail(sender, instance, created, **kwargs):
    if instance.gen_order:
        return
    from flashsale.dinghuo.tasks import task_purchasearrangement_update_purchasedetail
    transaction.on_commit(lambda: task_purchasearrangement_update_purchasedetail.delay(instance.id))

post_save.connect(update_purchase_detail, sender=PurchaseArrangement,
                      dispatch_uid='post_save_update_purchase_detail')
