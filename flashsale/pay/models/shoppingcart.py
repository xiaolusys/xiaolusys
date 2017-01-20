# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import uuid
import datetime
import urlparse
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.db.models.signals import post_save
from django.conf import settings
from django.db import transaction

from .base import PayBaseModel, BaseModel
from shopback.items.models import Product
from .product import ProductSku

from mall.xiaolupay import apis as xiaolupay


import logging
logger = logging.getLogger(__name__)


class ShoppingCart(BaseModel):
    """ 购物车 """

    NORMAL = 0
    CANCEL = 1

    STATUS_CHOICE = ((NORMAL, u'正常'),
                     (CANCEL, u'关闭'))

    id = models.AutoField(primary_key=True)
    buyer_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    item_id = models.IntegerField(db_index=True, null=False, verbose_name=u'商品ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')
    std_sale_price = models.FloatField(default=0.0, verbose_name=u'标准售价')

    sku_id = models.IntegerField(db_index=True, null=False, verbose_name=u'规格ID')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')

    sku_name = models.CharField(max_length=256, blank=True, verbose_name=u'规格名称')

    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    remain_time = models.DateTimeField(null=True, blank=True, verbose_name=u'保留时间')

    status = models.IntegerField(choices=STATUS_CHOICE, default=NORMAL,
                                 db_index=True, blank=True, verbose_name=u'订单状态')
    TEAMBUY = 3
    SECONDBUY = 4
    COUPONBUY = 5
    VIRTUALBUY = 6
    TYPE_CHOICES = (
        (0, u'特卖订单'),
        (TEAMBUY, u'团购订单'),
        (SECONDBUY, u'秒杀订单'),
        (COUPONBUY, u'优惠券订单'),  # 只能使用优惠券购买
        (VIRTUALBUY, u'券商品订单'),  # 主要指精品券
    )
    type = models.IntegerField(choices=TYPE_CHOICES, default=0)

    class Meta:
        db_table = 'flashsale_shoppingcart'
        index_together = [('buyer_id', 'item_id', 'sku_id')]
        app_label = 'pay'
        verbose_name = u'特卖/购物车'
        verbose_name_plural = u'特卖/购物车'

    def __unicode__(self):
        return '%s' % (self.id)

    @property
    def product(self):
        if not hasattr(self, '_product_'):
            self._product_ = Product.objects.filter(id=self.item_id).first()
        return self._product_

    def get_modelproduct(self):
        if not hasattr(self, '_modelproduct_'):
            self._modelproduct_ = self.product.get_product_model()
        return self._modelproduct_

    @transaction.atomic
    def close_cart(self, release_locknum=True):
        """ 关闭购物车 """
        try:
            ShoppingCart.objects.get(id=self.id, status=ShoppingCart.NORMAL)
        except ShoppingCart.DoesNotExist:
            return

        self.status = self.CANCEL
        self.save()
        if release_locknum:
            sku = get_object_or_404(ProductSku, pk=self.sku_id)
            Product.objects.releaseLockQuantity(sku, self.num)

    # def std_sale_price(self):
    #     sku = ProductSku.objects.get(id=self.sku_id)
    #     return sku.std_sale_price

    def is_deposite(self):
        product = Product.objects.get(id=self.item_id)
        return product.outer_id.startswith('RMB')

    def is_good_enough(self):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return (product_sku.product.shelf_status == Product.UP_SHELF
                and product_sku.free_num >= self.num)

    def calc_discount_fee(self, xlmm=None):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return product_sku.calc_discount_fee(xlmm)

    def is_repayable(self):
        """ can repay able """
        pro_sku = ProductSku.objects.filter(id=self.sku_id).first()
        if pro_sku and pro_sku.product.is_onshelf():
            return pro_sku.sale_out
        return False

    def get_item_weburl(self):
        product = self.product
        return urlparse.urljoin(settings.M_SITE_URL,
                                Product.MALL_PRODUCT_TEMPLATE_URL.format(product.model_id))


from shopback import signals


def off_the_shelf_func(sender, product_list, *args, **kwargs):
    from core.options import log_action, CHANGE, get_systemoa_user
    from .trade import SaleTrade
    from flashsale.pay.tasks import notifyTradePayTask
    sysoa_user = get_systemoa_user()
    for pro_bean in product_list:
        all_cart = ShoppingCart.objects.filter(item_id=pro_bean.id, status=ShoppingCart.NORMAL, type=0)
        for cart in all_cart:
            cart.close_cart()
            log_action(sysoa_user.id, cart, CHANGE, u'下架后更新')
        all_trade = SaleTrade.objects.filter(sale_orders__item_id=pro_bean.id, status=SaleTrade.WAIT_BUYER_PAY)
        for trade in all_trade:
            try:
                charge = xiaolupay.Charge.retrieve(trade.tid)
                if charge and charge.paid:
                    notifyTradePayTask.delay(charge)
                else:
                    trade.close_trade()
                    log_action(sysoa_user.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)


signals.signal_product_downshelf.connect(off_the_shelf_func, sender=Product)


def shoppingcart_update_productskustats_shoppingcart_num(sender, instance, created, **kwargs):
    if created:
        # from flashsale.restpro.tasks import task_add_shoppingcart_num
        # task_add_shoppingcart_num.delay(instance)
        from flashsale.restpro.tasks import close_timeout_carts_and_orders_reset_cart_num
        from shopback.items.models.stats import SkuStock
        def _update_skustock_and_close_carts(sku_id, sku_num):
            stat = SkuStock.get_by_sku(sku_id)
            SkuStock.objects.filter(sku_id=stat.sku_id).update(shoppingcart_num=F('shoppingcart_num') + sku_num)
            close_timeout_carts_and_orders_reset_cart_num([sku_id])

        transaction.on_commit(lambda : _update_skustock_and_close_carts(instance.sku_id, instance.num))
    else:
        from shopback.items.tasks_stats import task_shoppingcart_update_productskustats_shoppingcart_num
        transaction.on_commit(lambda: task_shoppingcart_update_productskustats_shoppingcart_num(instance.sku_id))


post_save.connect(shoppingcart_update_productskustats_shoppingcart_num, sender=ShoppingCart,
                  dispatch_uid='post_save_shoppingcart_update_productskustats_shoppingcart_num')
