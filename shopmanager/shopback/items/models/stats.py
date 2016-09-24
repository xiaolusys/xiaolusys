# coding: utf-8

import datetime
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.db.models import F
from django.db import transaction
from django.core.cache import cache

from shopback.warehouse import WARE_SH, WARE_CHOICES

import logging

logger = logging.getLogger(__name__)


# This is the commit time, and also the time we start.
# after switch, we can't update product sku quantity any more!!!

class ProductDaySale(models.Model):
    id = models.AutoField(primary_key=True)

    day_date = models.DateField(verbose_name=u'销售日期')
    sale_time = models.DateField(null=True, verbose_name=u'上架日期')

    user_id = models.BigIntegerField(null=False, verbose_name=u'店铺用户ID')
    product_id = models.IntegerField(null=False, verbose_name='商品ID')
    sku_id = models.IntegerField(null=True, verbose_name='规格ID')
    outer_id = models.CharField(max_length=64, blank=True, db_index=True, verbose_name='商品编码')

    sale_num = models.IntegerField(default=0, verbose_name='销售数量')
    sale_payment = models.FloatField(default=0.0, verbose_name='销售金额')
    sale_refund = models.FloatField(default=0.0, verbose_name='退款金额')

    confirm_num = models.IntegerField(default=0, verbose_name='成交数量')
    confirm_payment = models.FloatField(default=0.0, verbose_name='成交金额')

    class Meta:
        db_table = 'shop_items_daysale'
        unique_together = ("day_date", "user_id", "product_id", "sku_id")
        app_label = 'items'
        verbose_name = u'商品销量统计'
        verbose_name_plural = u'商品销量统计'

    def __unicode__(self):
        return '<%s,%s,%d,%d,%s>' % (self.id,
                                     self.day_date,
                                     self.user_id,
                                     self.product_id,
                                     str(self.sku_id))


class ProductSkuStats(models.Model):

    class Meta:
        db_table = 'shop_items_productskustats'
        app_label = 'items'
        verbose_name = u'SKU库存'
        verbose_name_plural = u'SKU库存列表'

    API_CACHE_KEY_TPL = 'api_productskustat_{0}'
    STATUS = ((0, 'EFFECT'), (1, 'DISCARD'))
    PRODUCT_SKU_STATS_COMMIT_TIME = datetime.datetime(2016, 4, 20, 01, 00, 00)

    # sku_id = models.IntegerField(null=True, unique=True, verbose_name=u'SKUID')
    # product_id = models.IntegerField(null=True, db_index=True, verbose_name=u'商品ID')
    sku = models.OneToOneField('ProductSku', null=True, verbose_name=u'SKU')
    product = models.ForeignKey('Product', null=True, verbose_name=u'商品')
    # ware_by = models.IntegerField(default=WARE_SH, db_index=True, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    assign_num = models.IntegerField(default=0, verbose_name=u'分配数')  # 未出库包裹单中已分配的sku数量
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品数", help_text=u"已作废的数据")  # 保存对应sku的次品数量

    adjust_quantity = models.IntegerField(default=0, verbose_name=u'调整数')  #
    history_quantity = models.IntegerField(default=0, verbose_name=u'历史库存数')  #
    inbound_quantity = models.IntegerField(default=0, verbose_name=u'入仓库存数')  #
    return_quantity = models.IntegerField(default=0, verbose_name=u'客户退货数')  #
    rg_quantity = models.IntegerField(default=0, verbose_name=u'退还供应商货数')  #
    post_num = models.IntegerField(default=0, verbose_name=u'已发货数')  #
    sold_num = models.IntegerField(default=0, verbose_name=u'购买数')  #

    shoppingcart_num = models.IntegerField(default=0, verbose_name=u'加入购物车数')  #
    waitingpay_num = models.IntegerField(default=0, verbose_name=u'等待付款数')  #

    created = models.DateTimeField(null=True, blank=True, db_index=True, auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name=u'状态')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id, self.sku_id)

    @staticmethod
    @transaction.atomic
    def get_by_sku(sku_id):
        stat = ProductSkuStats.objects.filter(sku_id=sku_id).first()
        if stat:
            return stat
        else:
            from shopback.items.models import ProductSku
            sku = ProductSku.objects.get(id=sku_id)
            stat = ProductSkuStats(sku_id=sku.id, product_id=sku.product_id)
            stat.save()
            return stat

    @property
    def realtime_quantity(self):
        return self.history_quantity + self.inbound_quantity + self.adjust_quantity + self.return_quantity - self.post_num - self.rg_quantity

    @property
    def aggregate_quantity(self):
        return self.history_quantity + self.inbound_quantity + self.adjust_quantity

    @property
    def wait_post_num(self):
        return self.sold_num - self.post_num

    @property
    def not_assign_num(self):
        from shopback.trades.models import PackageSkuItem
        return PackageSkuItem.get_not_assign_num(self.sku_id)

    @property
    def wait_assign_num(self):
        return self.sold_num - self.assign_num - self.post_num

    @property
    def wait_order_num(self):
        res = self.sold_num - self.post_num - self.realtime_quantity
        return res if res > 0 else 0

    @property
    def lock_num(self):
        """老锁定数（仓库里待发货，加购物车待支付）"""
        return self.shoppingcart_num + self.waitingpay_num + self.sold_num - self.return_quantity - self.post_num

    @property
    def realtime_lock_num(self):
        return self.shoppingcart_num + self.waitingpay_num

    def realtime_lock_num_display(self):
        try:
            sale_state = ProductSkuSaleStats.objects.get(sku_id=self.id, status=ProductSkuSaleStats.ST_EFFECT)
        except ProductSkuSaleStats.DoesNotExist:
            sale_state = None
        return '%s(c:%s|w:%s|i:%s|s%s)' % (self.realtime_lock_num,
                                           self.shoppingcart_num,
                                           self.waitingpay_num,
                                           sale_state and sale_state.init_waitassign_num or 0,
                                           sale_state and sale_state.num or 0)

    realtime_lock_num_display.short_description = u"实时锁定库存"

    @property
    def properties_name(self):
        from .product import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])

    @property
    def product_sku(self):
        return self.sku
        # if not hasattr(self, '_product_sku_'):
        #     from shopback.items.models import ProductSku
        #     self._product_sku_ = ProductSku.objects.get(id=self.sku_id)
        # return self._product_sku_

    @property
    def unused_stock(self):
        """冗余库存数"""
        return self.history_quantity + self.inbound_quantity + self.adjust_quantity + self.return_quantity - self.rg_quantity - self.sold_num

    @staticmethod
    def redundancies():
        """
            实时库存 - 待发数 >0
            不在卖
            供应商退货限定时间内进货
        :return:
        """
        from flashsale.dinghuo.models import OrderDetail
        from .product import Product
        order_skus = [o['chichu_id'] for o in OrderDetail.objects.filter(
            arrival_time__gt=(datetime.datetime.now() - datetime.timedelta(days=20)), arrival_quantity__gt=0).values(
            'chichu_id').distinct()]
        has_nouse_stock_sku_product = [(stat['id'], stat['product_id']) for stat in
                                       ProductSkuStats.objects.filter(sku_id__in=order_skus,
                                                                      sold_num__lt=F('history_quantity') + F(
                                                                          'adjust_quantity') + F(
                                                                          'inbound_quantity') + F('return_quantity') \
                                                                                   - F('rg_quantity')).values('id',
                                                                                                              'product_id')]
        has_nouse_stock_products = {product_id for (_id, product_id) in has_nouse_stock_sku_product}
        products = Product.objects.filter(id__in=has_nouse_stock_products)
        product_dict = {p.id: p for p in products}
        sku_product = [(id, product_dict[product_id]) for (id, product_id) in has_nouse_stock_sku_product]
        return_ids = []
        for id, pro in sku_product:
            if pro.sale_time and pro.offshelf_time and not datetime.datetime(pro.sale_time.year, pro.sale_time.month,
                                                                             pro.sale_time.day) < datetime.datetime.now() < pro.offshelf_time:
                return_ids.append(id)
        return return_ids

    @staticmethod
    def filter_by_supplier(supplier_id):
        from .product import Product
        return [p['id'] for p in Product.get_by_supplier(supplier_id).values('id')]

    @staticmethod
    def update_adjust_num(sku_id, adjust_quantity):
        stat = ProductSkuStats.objects.get(sku_id=sku_id)
        stat.adjust_quantity = adjust_quantity
        stat.save()
        # ProductSkuStats.objects.filter(sku_id=sku_id).update(adjust_quantity=adjust_quantity)

    @staticmethod
    def get_auto_sale_stock():
        from shopback.categorys.models import ProductCategory
        from .product import Product
        pid = ProductCategory.objects.get(name=u'优尼世界').cid
        return ProductSkuStats.objects.filter(product__status=Product.NORMAL).filter(
            return_quantity__gt=F('sold_num') + F('rg_quantity')
                                - F('history_quantity') - F('adjust_quantity') - F(
                'inbound_quantity')).exclude(product__category_id=pid).exclude(product__outer_id__startswith='RMB')

    def to_apimodel(self):
        from apis.v1.products import Skustat as APIModel, SkuCtl
        data = self.__dict__
        sku_obj = SkuCtl.retrieve(self.sku_id)
        data.update({
            'id': self.sku_id,
            'remain_num': sku_obj and sku_obj.remain_num or 0
        })
        return APIModel(**data)

def invalid_apiskustat_cache(sender, instance, *args, **kwargs):
    if hasattr(sender, 'API_CACHE_KEY_TPL'):
        logger.debug('invalid_apiskustat_cache: %s'%instance.sku_id)
        cache.delete(ProductSkuStats.API_CACHE_KEY_TPL.format(instance.sku_id))

post_save.connect(invalid_apiskustat_cache, sender=ProductSkuStats, dispatch_uid='post_save_invalid_apiskustat_cache')

def assign_stock_to_package_sku_item(sender, instance, created, **kwargs):
    if instance.realtime_quantity > instance.assign_num:
        from shopback.items.tasks import task_assign_stock_to_package_sku_item
        task_assign_stock_to_package_sku_item.delay(instance)
    elif instance.realtime_quantity < instance.assign_num:
        from shopback.items.tasks import task_relase_package_sku_item
        task_relase_package_sku_item.delay(instance)


post_save.connect(assign_stock_to_package_sku_item, sender=ProductSkuStats,
                  dispatch_uid='post_save_assign_stock_to_package_sku_item')


def update_productsku(sender, instance, created, **kwargs):
    from shopback.items.tasks import task_productskustats_update_productsku
    task_productskustats_update_productsku.delay(instance)


post_save.connect(update_productsku, sender=ProductSkuStats, dispatch_uid='post_save_productskustats_update_productsku')


def product_sku_stats_agg(sender, instance, created, **kwargs):
    # import elasticsearch
    """ 统计实时库存的变化到统计app中"""
    try:
        from statistics.tasks import task_update_product_sku_stats
        task_update_product_sku_stats.delay(instance)
    except Exception, exc:
        logger.error(exc.message)


post_save.connect(product_sku_stats_agg, sender=ProductSkuStats, dispatch_uid='post_save_product_sku_stats')


class InferiorSkuStats(models.Model):
    class Meta:
        db_table = 'shop_items_inferiorskustats'
        app_label = 'items'
        verbose_name = u'次品记录'
        verbose_name_plural = u'次品库存列表'

    STATUS = ((0, 'EFFECT'), (1, 'DISCARD'))
    sku = models.OneToOneField('ProductSku', null=True, verbose_name=u'SKU')
    product = models.ForeignKey('Product', null=True, verbose_name=u'商品')
    ware_by = models.IntegerField(default=WARE_SH, db_index=True, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    history_quantity = models.IntegerField(default=0, verbose_name=u'历史库存数')
    inbound_quantity = models.IntegerField(default=0, verbose_name=u'入仓库存数')
    return_quantity = models.IntegerField(default=0, verbose_name=u'客户退货数')
    rg_quantity = models.IntegerField(default=0, verbose_name=u'退还供应商货数')
    adjust_num = models.IntegerField(default=0, verbose_name=u'调整数')
    created = models.DateTimeField(null=True, blank=True, db_index=True, auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name=u'状态')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id, self.sku_id)

    @staticmethod
    def get_by_sku(sku_id):
        stat = InferiorSkuStats.objects.filter(sku_id=sku_id).first()
        if stat:
            return stat
        else:
            return InferiorSkuStats.create(sku_id)

    @staticmethod
    def create(sku_id, real_quantity_zreo=False):
        from .product import ProductSku
        from shopback.refunds.models import RefundProduct
        from flashsale.dinghuo.models import RGDetail, InBoundDetail
        sku = ProductSku.objects.get(id=sku_id)
        stat = InferiorSkuStats(sku_id=sku.id, product_id=sku.product_id)
        stat.save()
        stat.rg_quantity = RGDetail.get_inferior_total(sku_id, ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
        stat.return_quantity = RefundProduct.get_total(sku_id, can_reuse=False,
                                                       begin_time=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
        stat.inbound_quantity = InBoundDetail.get_inferior_total(
            sku_id, begin_time=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
        if stat.realtime_quantity < 0 and real_quantity_zreo:
            stat.history_quantity = -stat.realtime_quantity
        stat.save()
        return stat

    @property
    def realtime_quantity(self):
        return self.history_quantity + self.inbound_quantity + self.return_quantity + self.adjust_num - self.rg_quantity

    @staticmethod
    def update_adjust_num(sku_id, adjust_quantity):
        InferiorSkuStats.objects.filter(sku_id=sku_id).update(adjust_num=adjust_quantity)


class ProductSkuSaleStats(models.Model):
    class Meta:
        db_table = 'shop_items_productskusalestats'
        app_label = 'items'
        verbose_name = u'库存/商品购买统计数据'
        verbose_name_plural = u'库存/商品购买统计数据列表'

    ST_EFFECT = 0
    ST_DISCARD = 1
    ST_FINISH = 2

    STATUS = ((ST_EFFECT, 'EFFECT'), (ST_DISCARD, 'DISCARD'), (ST_FINISH, 'FINISH'))

    # uni_key = sku_id + number of finished records
    uni_key = models.CharField(max_length=32, null=True, unique=True, verbose_name='UNIQUE ID')

    sku_id = models.IntegerField(null=True, db_index=True, verbose_name='商品SKU记录ID')
    product_id = models.IntegerField(null=True, db_index=True, verbose_name='商品记录ID')

    init_waitassign_num = models.IntegerField(default=0, verbose_name='上架前待分配数')
    num = models.IntegerField(default=0, verbose_name='上架期间购买数')
    sale_start_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='开始时间')
    sale_end_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='结束时间')

    created = models.DateTimeField(null=True, blank=True, db_index=True, auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name='状态')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id, self.sku_id)

    @property
    def properties_name(self):
        from .product import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])


def gen_productsksalestats_unikey(sku_id):
    count = ProductSkuSaleStats.objects.filter(sku_id=sku_id, status=ProductSkuSaleStats.ST_FINISH).count()
    return "%s-%s" % (sku_id, count)


class ItemNumTaskLog(models.Model):
    id = models.AutoField(primary_key=True)

    user_id = models.CharField(max_length=64, blank=True, verbose_name='店铺ID')
    outer_id = models.CharField(max_length=64, blank=True, verbose_name='商品编码')
    sku_outer_id = models.CharField(max_length=64, blank=True, verbose_name='规格编码')

    num = models.IntegerField(verbose_name='同步数量')

    start_at = models.DateTimeField(null=True, blank=True, verbose_name='同步期始')
    end_at = models.DateTimeField(null=True, blank=True, verbose_name='同步期末')

    class Meta:
        db_table = 'shop_items_itemnumtasklog'
        app_label = 'items'
        verbose_name = u'库存同步日志'
        verbose_name_plural = u'库存同步日志'

    def __unicode__(self):
        return '<%s,%s,%d>' % (self.outer_id,
                               self.sku_outer_id,
                               self.num)
