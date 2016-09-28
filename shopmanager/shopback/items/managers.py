# coding: utf-8
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models import Sum
from shopback import paramconfig as pcfg
from core.ormcache.managers import CacheManager


class ProductManager(CacheManager):
    def getProductByOuterid(self, outer_id):

        try:
            return self.get(outer_id=outer_id)
        except self.model.DoesNotExist:
            None

    def getProductByBarcode(self, barcode):

        if not barcode or not isinstance(barcode, (str, unicode)) or len(barcode) == 0:
            return []

        from shopback.items.models import ProductSku

        product_skus = ProductSku.objects.filter(product__status__in=(pcfg.NORMAL, pcfg.REMAIN), barcode=barcode)
        if product_skus.count() > 0:
            return list(set([sku.product for sku in product_skus]))

        products = self.filter(status__in=(pcfg.NORMAL, pcfg.REMAIN), barcode=barcode)
        if products.count() > 0:
            return [p for p in products]

        cur_products = []
        bar_len = len(barcode)
        for index in range(0, bar_len - 1):
            outer_id = barcode[0:bar_len - index]
            outer_sku_id = barcode[bar_len - index:]

            products = self.filter(outer_id=outer_id)
            if products.count() > 0 and not cur_products:
                cur_products = list(products)

            for product in products:
                skus = product.prod_skus.filter(outer_id=outer_sku_id)
                if skus.count() > 0:
                    return [product]

        return cur_products

    def getProductSkuByBarcode(self, barcode):

        if not barcode or not isinstance(barcode, (str, unicode)) or len(barcode) == 0:
            return []

        from shopback.items.models import ProductSku

        product_skus = ProductSku.objects.filter(product__status__in=(pcfg.NORMAL, pcfg.REMAIN), barcode=barcode)
        if product_skus.count() > 0:
            return list(product_skus)

        bar_len = len(barcode)
        for index in range(0, bar_len - 1):
            outer_id = barcode[0:bar_len - index]
            outer_sku_id = barcode[bar_len - index:]

            products = self.filter(outer_id=outer_id)
            for product in products:
                skus = product.prod_skus.filter(outer_id=outer_sku_id)
                if skus.count() > 0:
                    return list(skus)

        return []

    def getSaleProductByCharger(self, charger, from_sale_time=None, to_sale_time=None):

        assert isinstance(charger, User)

        user_name = charger.username
        product_list = self.filter(models.Q(sale_charger=user_name)
                                   | models.Q(storage_charger=user_name))

        if from_sale_time:
            product_list.filter(sale_time__gte=from_sale_time)

        if to_sale_time:
            product_list.filter(sale_time__lte=to_sale_time)

        return product_list

    def getOrderListByOuterid(self, outer_ids):

        from shopback.trades.models import MergeOrder

        trade_list = set([])
        mos = MergeOrder.objects.filter(outer_id__in=outer_ids, sys_status=pcfg.IN_EFFECT) \
            .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS))

        for o in mos:
            trade_list.add(o.merge_trade)

        return list(trade_list)

    def getBarcodeByOuterid(self, outer_id, outer_sku_id=''):

        product = self.get(outer_id=outer_id)
        product_sku = None
        if outer_sku_id:
            product_sku = product.prod_skus.get(outer_id=outer_sku_id)

        return product_sku and product_sku.BARCODE or product.BARCODE

    def getProductSkuByOuterid(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except ProductSku.DoesNotExist:
            None

    def isProductOutOfStock(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

        return (product.is_out_stock,
                product_sku and product_sku.is_out_stock)[product_sku and 1 or 0]

    def isProductOutingStockEnough(self, outer_id, outer_sku_id, num):

        assert num >= 0

        from .models import ProductSku
        from shopback.trades.models import MergeTrade
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

        outing_num = MergeTrade.objects.getProductOrSkuOrderOutingNum(outer_id, outer_sku_id)

        if product_sku:
            return product_sku.quantity - outing_num - num >= 0
        else:
            return product.collect_num - outing_num - num >= 0

    def isProductRuelMatch(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)

            return product.is_match or (product_sku and product_sku.is_match)

        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def isProductRuleSplit(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)

            return product.is_split or (product_sku and product_sku.is_split)

        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def getProductMatchReason(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)

            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                return (product_sku.match_reason
                        or product.match_reason
                        or u'匹配原因不明')

            return product.match_reason or u'匹配原因不明'

        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def getPrudocutCostByCode(self, outer_id, outer_sku_id):

        from .models import ProductSku
        try:
            product = self.get(outer_id=outer_id)
            product_sku = None
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

        return (product.cost,
                product_sku and product_sku.cost)[product_sku and 1 or 0]

    def updateWaitPostNumByCode(self, outer_id, outer_sku_id, order_num):

        from .models import ProductSku
        try:
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                product_sku.update_wait_post_num(order_num)
            else:
                product = self.get(outer_id=outer_id)
                product.update_wait_post_num(order_num)

        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def reduceWaitPostNumByCode(self, outer_id, outer_sku_id, order_num):

        from .models import ProductSku
        try:
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                     product__outer_id=outer_id)
                product_sku.update_wait_post_num(order_num, dec_update=True)

            else:
                product = self.get(outer_id=outer_id)
                product.update_wait_post_num(order_num, dec_update=True)

        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def reduceLockNumByCode(self, outer_id, outer_sku_id, order_num):

        from .models import ProductSku
        try:
            product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                 product__outer_id=outer_id)
            product_sku.update_lock_num(order_num, dec_update=True)
        except (self.model.DoesNotExist, ProductSku.DoesNotExist):
            raise self.model.ProductCodeDefect(u'(%s,%s)编码组合未匹配到商品' % (outer_id, outer_sku_id))

    def trancecode(self, outer_id, outer_sku_id, sku_code_prior=False):

        conncate_code = outer_sku_id or outer_id

        index = conncate_code.rfind(self.model.PRODUCT_CODE_DELIMITER)
        if sku_code_prior and index > 0:
            return conncate_code[index + 1:].strip(), conncate_code[0:index].strip()

        if index > 0:
            return conncate_code[0:index].strip(), conncate_code[index + 1:].strip()

        return outer_id.strip(), outer_sku_id.strip()

    def updateProductWaitPostNum(self, product):
        """
            更新商品待发数
            如果在新库存系统中有售卖
        :param product:
        :return:
        """
        from shopback.items.models import ProductSkuStats
        prod_skus = product.pskus
        sku_ids = [k.id for k in prod_skus]
        sold_num_total = ProductSkuStats.objects.filter(sku_id__in=sku_ids).aggregate(Sum('sold_num'))
        if sold_num_total > 0:
            for sku in prod_skus:
                stat = ProductSkuStats.objects.get(sku_id=sku.id)
                sku.wait_post_num = stat.wait_post_num
                sku.save(update_fields=['wait_post_num'])
        else:
            from shopback.trades.models import MergeTrade
            outer_id = product.outer_id
            prod_skus = product.pskus
            if prod_skus.count() > 0:
                for sku in prod_skus:
                    outer_sku_id = sku.outer_id
                    wait_post_num = MergeTrade.objects.getProductOrSkuWaitPostNum(outer_id, outer_sku_id)
                    sku.wait_post_num = wait_post_num
                    sku.save()
            else:
                outer_sku_id = ''
                wait_post_num = MergeTrade.objects.getProductOrSkuWaitPostNum(outer_id, outer_sku_id)
                product.wait_post_num = wait_post_num
                product.save()


    def isQuantityLockable(self, sku, num):

        try:
            product_detail = sku.product.details
            if product_detail.buy_limit and num > product_detail.per_limit:
                return False
        except ObjectDoesNotExist:
            pass
        return True

    def lockQuantity(self, sku, num):
        # 锁定库存
        # urows = (sku.__class__.objects.filter(id=sku.id,
        #                                       remain_num__gte=models.F('lock_num') + num)
        #          .update(lock_num=models.F('lock_num') + num))
        # return urows > 0
        return True

    def releaseLockQuantity(self, sku, num):
        # 释放锁定库存
        if sku.lock_num < num:
            num = sku.lock_num

        urows = (sku.__class__.objects.filter(id=sku.id)
                 .update(lock_num=models.F('lock_num') - num))

        return urows > 0
