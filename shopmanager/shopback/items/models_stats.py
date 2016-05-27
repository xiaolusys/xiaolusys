# coding: utf-8
import logging
import datetime

from django.db import models
from django.db.models.signals import pre_save, post_save
from django.db.models import F

logger = logging.getLogger('django.request')

# This is the commit time, and also the time we start.
# after switch, we can't update product sku quantity any more!!!
PRODUCT_SKU_STATS_COMMIT_TIME = datetime.datetime(2016, 4, 20, 01, 00, 00)


class ProductSkuStats(models.Model):
    class Meta:
        db_table = 'shop_items_productskustats'
        app_label = 'items'
        verbose_name = u'SKU库存'
        verbose_name_plural = u'SKU库存列表'

    STATUS = ((0, 'EFFECT'), (1, 'DISCARD'))

    #sku_id = models.IntegerField(null=True, unique=True, verbose_name=u'SKUID')
    #product_id = models.IntegerField(null=True, db_index=True, verbose_name=u'商品ID')
    sku = models.ForeignKey('ProductSku', verbose_name=u'SKU')
    product = models.ForeignKey('Product', null=True, verbose_name=u'商品')

    assign_num = models.IntegerField(default=0, verbose_name=u'分配数')  # 未出库包裹单中已分配的sku数量
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品数")  # 保存对应sku的次品数量

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

    @property
    def realtime_quantity(self):
        return self.history_quantity + self.inbound_quantity + self.return_quantity - self.post_num - self.rg_quantity

    @property
    def aggregate_quantity(self):
        return self.history_quantity + self.inbound_quantity

    @property
    def wait_post_num(self):
        return self.sold_num - self.post_num

    @property
    def wait_assign_num(self):
        return self.sold_num - self.assign_num - self.post_num

    @property
    def wait_order_num(self):
        res = self.sold_num - self.post_num - self.realtime_quantity
        return res if res > 0 else 0

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
        from shopback.items.models import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])

    @property
    def product_sku(self):
        return self.sku
        # if not hasattr(self, '_product_sku_'):
        #     from shopback.items.models import ProductSku
        #     self._product_sku_ = ProductSku.objects.get(id=self.sku_id)
        # return self._product_sku_

    @staticmethod
    def redundancies():
        """
            实时库存 - 待发数 >0
            不在卖
            供应商退货限定时间内进货
        :return:
        """
        from flashsale.dinghuo.models import OrderDetail
        from shopback.items.models import ProductSku
        order_skus = [o['chichu_id'] for o in OrderDetail.objects.filter(
            arrival_time__gt=(datetime.datetime.now() - datetime.timedelta(days=20)), arrival_quantity__gt=0).values(
            'chichu_id').distinct()]
        has_nouse_stock_skus = [stat['sku_id'] for stat in ProductSkuStats.objects.filter(sku_id__in=order_skus,
            sold_num__lt=F('history_quantity') + F('inbound_quantity') + F('return_quantity')\
            - F('rg_quantity')).values('sku_id')]
        need_return_skus = []
        for sku in has_nouse_stock_skus:
            pro = ProductSku.objects.get(id=sku).product
            if pro.sale_time and pro.offshelf_time and not datetime.datetime(pro.sale_time.year, pro.sale_time.month,
                                 pro.sale_time.day) < datetime.datetime.now() < pro.offshelf_time:
                need_return_skus.append(sku)
        return ProductSkuStats.objects.filter(sku_id__in=need_return_skus)


def assign_stock_to_package_sku_item(sender, instance, created, **kwargs):
    if instance.realtime_quantity > instance.assign_num:
        from shopback.items.tasks import task_assign_stock_to_package_sku_item
        task_assign_stock_to_package_sku_item.delay(instance)
    elif instance.realtime_quantity < instance.assign_num:
        logger.error('assign_num error: sku assign_num bigger than quantity:' + str(instance.id))
        from shopback.items.tasks import task_relase_package_sku_item
        task_relase_package_sku_item.delay(instance)


post_save.connect(assign_stock_to_package_sku_item, sender=ProductSkuStats,
                  dispatch_uid='post_save_assign_stock_to_package_sku_item')


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
        from shopback.items.models import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])


def gen_productsksalestats_unikey(sku_id):
    count = ProductSkuSaleStats.objects.filter(sku_id=sku_id, status=ProductSkuSaleStats.ST_FINISH).count()
    return "%s-%s" % (sku_id, count)
