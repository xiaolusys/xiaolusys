# coding: utf-8
from __future__ import unicode_literals

import traceback
import datetime
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save
from django.db.models import F
from django.db import transaction
from django.core.cache import cache
from shopback.trades.constants import PSI_STATUS
from shopback.warehouse import WARE_SH, WARE_CHOICES, WARE_NONE
from django.db.models import Manager
import logging

logger = logging.getLogger(__name__)
STAT_SIGN = True
WARNING = True


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


class SkuStock(models.Model):
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

    # [('paid', u'待成订货单'),
    # ('prepare_book', u'待订货'),
    # ('booked', u'待备货'),
    # ('assigned', u'待发货'),
    # ('waitscan', u'待扫描'),
    # ('waitpost', u'待称重'),
    # ('sent', u'待收货'),
    # ('finish', u'完成'),]

    # ware_by = models.IntegerField(default=WARE_NONE, db_index=True, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    # 目前一种SKU只能在一个仓库里 按product的ware_by查看
    # 发货库存数
    psi_paid_num = models.IntegerField(default=0, verbose_name=u'待处理数')
    psi_prepare_book_num = models.IntegerField(default=0, verbose_name=u'待订货数')
    psi_booked_num = models.IntegerField(default=0, verbose_name=u'已订货数')
    psi_ready_num = models.IntegerField(default=0, verbose_name=u'待分配数')
    psi_third_send_num = models.IntegerField(default=0, verbose_name=u'待供应商发货数')
    psi_assigned_num = models.IntegerField(default=0, verbose_name=u'待合单数')
    psi_merged_num = models.IntegerField(default=0, verbose_name=u'待打单数')
    psi_waitscan_num = models.IntegerField(default=0, verbose_name=u'待扫描数')
    psi_waitpost_num = models.IntegerField(default=0, verbose_name=u'待称重数')
    psi_sent_num = models.IntegerField(default=0, verbose_name=u'待签收数')
    psi_finish_num = models.IntegerField(default=0, verbose_name=u'完成数')

    # 仓库库存数
    adjust_quantity = models.IntegerField(default=0, verbose_name=u'调整数')  #
    history_quantity = models.IntegerField(default=0, verbose_name=u'历史库存数')  #
    inbound_quantity = models.IntegerField(default=0, verbose_name=u'入仓库存数')  #
    return_quantity = models.IntegerField(default=0, verbose_name=u'客户退货数')  #
    rg_quantity = models.IntegerField(default=0, verbose_name=u'退还供应商货数')  #

    # 统计数
    assign_num = models.IntegerField(default=0, verbose_name=u'已分配数')  # 未出库包裹单中已分配的sku数量【已经】
    post_num = models.IntegerField(default=0, verbose_name=u'已发货数')  #

    # 收卖库存
    shoppingcart_num = models.IntegerField(default=0, verbose_name=u'加入购物车数')  #
    waitingpay_num = models.IntegerField(default=0, verbose_name=u'等待付款数')  #
    sold_num = models.IntegerField(default=0, verbose_name=u'购买数')  #
    paid_num = models.IntegerField(default=0, verbose_name=u'付款数')  # 付款不一定等同于购买成功,如团购

    inferior_num = models.IntegerField(default=0, verbose_name=u"次品数", help_text=u"已作废的数据")  # 保存对应sku的次品数量
    created = models.DateTimeField(null=True, blank=True, db_index=True, auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name=u'状态')
    _objects = Manager()
    objects = Manager()

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id, self.sku_id)

    @staticmethod
    @transaction.atomic
    def add_return_quantity(sku_id,num):
        SkuStock.objects.filter(sku_id=sku_id).update(return_quantity = F('return_quantity')+num)


    @staticmethod
    @transaction.atomic
    def get_by_sku(sku_id):
        stat = SkuStock._objects.filter(sku_id=sku_id).first()
        if stat:
            return stat
        else:
            from shopback.items.models import ProductSku
            sku = ProductSku.objects.get(id=sku_id)
            stat = SkuStock(sku_id=sku.id, product_id=sku.product_id)
            stat.save()
            return stat

    @property
    def realtime_quantity(self):
        return self.history_quantity + self.inbound_quantity + self.adjust_quantity + self.return_quantity - self.post_num - self.rg_quantity

    # sum([p.realtime_quantity for p in
    # SkuStock._objects.filter(rg_quantity__lt=F('history_quantity')+F('inbound_quantity')+ F('adjust_quantity')+F('return_quantity')-F('post_num'))
    # .exclude(product__outer_id__startswith='RMB')])
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
    def new_lock_num(self):
        """老锁定数（仓库里待发货，加购物车待支付）"""
        return self.shoppingcart_num + self.waitingpay_num + self.sold_num - self.return_quantity - self.post_num

    @property
    def lock_num(self):
        salestat = ProductSkuSaleStats.get_by_sku(self.sku_id)
        if salestat:
            return salestat.init_waitassign_num + salestat.num + self.waitingpay_num
        else:
            # 没有取得salestat，就把过往卖出的全部当做锁定的。
            return self.sold_num - self.return_quantity + self.waitingpay_num

    @property
    def realtime_lock_num(self):
        return self.shoppingcart_num + self.waitingpay_num + self.sold_num - self.post_num

    def restat(self, need_stat=[]):
        """
            用统计方式重新计算库存
        """
        from shopback.trades.models import PackageSkuItem
        from flashsale.dinghuo.models import OrderDetail
        from shopback.refunds.models import RefundProduct
        if not need_stat:
            sum_res = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                    pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME). \
                exclude(assign_status=PackageSkuItem.CANCELED).values("assign_status").annotate(total=Sum('num'))
            wait_assign_num, assign_num, post_num, third_assign_num = 0, 0, 0, 0
            for entry in sum_res:
                if entry["assign_status"] == PackageSkuItem.NOT_ASSIGNED:
                    wait_assign_num = entry["total"]
                elif entry["assign_status"] == PackageSkuItem.ASSIGNED:
                    assign_num = entry["total"]
                elif entry["assign_status"] == PackageSkuItem.FINISHED:
                    post_num = entry["total"]
                elif entry['assign_status'] == PackageSkuItem.VIRTUAL_ASSIGNED:
                    third_assign_num = entry["total"]
            sold_num = wait_assign_num + assign_num + post_num + third_assign_num
            params = {"sold_num": sold_num, "assign_num": assign_num, "post_num": post_num}
            sum_res_status = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                           pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME). \
                exclude(status=PackageSkuItem.CANCELED).values("status").annotate(total=Sum('num'))
            for entry in sum_res_status:
                params['psi_%s_num' % entry.keys()[0]] = entry.values()[0]
        else:
            params = {}
            for attr in need_stat:
                psi_attr_status = [l[0] for l in PSI_STATUS.CHOICES]
                psi_attrs_dict = {'psi_%s_num' % s: s for s in psi_attr_status}
                if attr in psi_attrs_dict:
                    status = psi_attrs_dict[attr]
                    params[attr] = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                                 pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                 status=status). \
                                       exclude(status=PSI_STATUS.CANCEL).aggregate(total=Sum('num')).get(
                        'total') or 0
                if attr == 'assign_num':
                    params[attr] = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                                 pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                 assign_status=1).values(
                        'sku_id').aggregate(total=Sum('num')).get('total') or 0
                if attr == 'inbound_num':
                    params[attr] = OrderDetail.objects.filter(chichu_id=str(self.sku_id),
                                                              arrival_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME) \
                                       .aggregate(total=Sum('arrival_quantity')).get('total') or 0
                if attr == 'sold_num':
                    params[attr] = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                                 pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                 assign_status__in=[2, 0, 1, 4]).aggregate(
                        total=Sum('num')).get(
                        'total') or 0
                if attr == 'post_num':
                    params[attr] = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                                 pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                 assign_status=2).aggregate(total=Sum('num')).get(
                        'total') or 0
                if attr == 'refund_num':
                    params[attr] = RefundProduct.objects.filter(sku_id=self.sku_id,
                                                                created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                can_reuse=True).exclude(
                        sku_id=None).aggregate(total=Sum('num')).get('total') or 0
                if attr == 'return_num':
                    params[attr] = RefundProduct.objects.filter(sku_id=self.sku_id,
                                                                created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                                                can_reuse=True).exclude(
                        sku_id=None).aggregate(total=Sum('num')).get('total') or 0
        update_fields = []
        for k, v in params.iteritems():
            if hasattr(self, k):
                if getattr(self, k) != v:
                    setattr(self, k, v)
                    update_fields.append(k)
        if update_fields:
            update_fields.append('modified')
        return update_fields

    @staticmethod
    def stat_warning(sku_id, update_fields=[], warning=True, stat=False):
        sku_stock = SkuStock.get_by_sku(sku_id)
        update_fields = sku_stock.restat(update_fields)
        if update_fields:
            if warning:
                db_stock = SkuStock.get_by_sku(sku_id)
                db_data = {attr: getattr(db_stock, attr) for attr in update_fields}
                stat_data = {attr: getattr(sku_stock, attr) for attr in update_fields}
                s = ';'.join(['%s:stat:%s,db:%s' % (attr, stat_data[attr], db_data[attr],) for attr in update_fields])
                logging.error(u'统计库存与当前库存不相符合:sku_id:%s;info:%s' % (sku_id, s))
            if stat:
                sku_stock.save(update_fields=update_fields)
        return

    @staticmethod
    def set_psi_init_paid(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['sold_num', 'paid_num', 'psi_paid_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, False, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(sold_num=F('sold_num') + num,
                                                           psi_paid_num=F('psi_paid_num') + num,
                                                           paid_num=F('paid_num') + num,
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_prepare_book(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_paid_num', 'psi_prepare_book_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_paid_num=F('psi_paid_num') - num,
                                                           psi_prepare_book_num=F('psi_prepare_book_num') + num,
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_booked(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_booked_num', 'psi_prepare_book_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_booked_num=F('psi_booked_num') + num,
                                                           psi_prepare_book_num=F('psi_prepare_book_num') - num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_booked_to_ready(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_booked_num', 'psi_ready_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_ready_num=F('psi_ready_num') + num,
                                                           psi_booked_num=F('psi_booked_num') - num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_init_ready(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['sold_num', 'paid_num', 'psi_ready_num', 'assign_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(sold_num=F('sold_num') + num,
                                                           psi_ready_num=F('psi_ready_num') + num,
                                                           paid_num=F('paid_num') + num)
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_init_assigned(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['sold_num', 'paid_num', 'psi_assign_num', 'assign_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(sold_num=F('sold_num') + num,
                                                           psi_ready_num=F('psi_assign_num') + num,
                                                           paid_num=F('paid_num') + num,
                                                           assign_num=F('assign_num') + num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_assigned(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        pass

    @staticmethod
    def set_psi_not_assigned(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['assign_num', 'psi_paid_num', 'psi_assigned_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(assign_num=F('assign_num') - num,
                                                           psi_paid_num=F('psi_paid_num') + num,
                                                           psi_assigned_num=F('psi_assigned_num') - num)
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_merged(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_merged_num', 'psi_ready_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_ready_num=F('psi_ready_num') - num,
                                                           psi_booked_num=F('psi_merged_num') + num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_waitscan(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_merged_num', 'psi_waitscan_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_waitscan_num=F('psi_waitscan_num') + num,
                                                           psi_merged_num=F('psi_merged_num') - num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_waitpost(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_waitpost_num', 'psi_waitscan_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_waitscan_num=F('psi_waitscan_num') - num,
                                                           psi_waitpost_num=F('psi_waitpost_num') + num
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_sent(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_waitpost_num', 'psi_sent_num', 'post_num', 'assign_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_waitscan_num=F('psi_waitscan_num') - num,
                                                           psi_sent_num=F('psi_sent_num') + num,
                                                           post_num=F('post_num') + num,
                                                           assign_num=F('assign_num ') - num,
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_finish(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['psi_finish_num', 'psi_sent_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(psi_finish_num=F('psi_finish_num') + num,
                                                           psi_sent_num=F('psi_sent_num') - num,
                                                           )
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def set_psi_cancel(sku_id, num, status, stat=STAT_SIGN, warning=WARNING):
        if status == PSI_STATUS.CANCEL:
            return 
        attr = 'psi_%s_num' % status
        change_fields = []
        if hasattr(stat, attr):
            change_fields.append(attr)
        change_fields.extend(['assign_num', 'sold_num'])
        SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        # if stat:
        #   SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        # else:
        #     updation = {
        #         attr: F(attr) - num,
        #     }
        #     if 'assign_num' in change_fields:
        #         updation[attr] = F(attr) - num
        #     SkuStock.objects.filter(sku_id=sku_id).update(**updation)
            # if warning or stat:
            #     SkuStock.stat_warning(sku_id, ['sold_num', 'paid_num'], warning, stat)
            # else:
            #     SkuStock.objects.filter(id=sku_id).update(sold_num=F('sold_num') + num,
            #                                               psi_paid_num=F('psi_paid_num') + num,
            #                                               paid_num=F('paid_num') + num,
            #                                               )

    @staticmethod
    def set_psi_paid_prepare_book(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        if stat:
            sku_stock = SkuStock.get_by_sku(sku_id)
            update_fields = sku_stock.restat(['sold_num', 'paid_num'])
            if update_fields:
                sku_stock.save(update_fields=update_fields)
        else:
            SkuStock.objects.filter(id=sku_id).update(sold_num=F('sold_num') + num,
                                                      psi_paid_num=F('psi_paid_num') + num,
                                                      paid_num=F('paid_num') + num,
                                                      )

    @staticmethod
    def add_inbound_quantity(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['inbund_quantity']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(inbund_quantity=F('inbund_quantity') + num)
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

    @staticmethod
    def add_shoppingcart_num(sku_id, num, stat=STAT_SIGN, warning=WARNING):
        change_fields = ['shoppingcart_num']
        if stat:
            SkuStock.stat_warning(sku_id, change_fields, warning, stat)
        else:
            SkuStock._objects.filter(sku_id=sku_id).update(shoppingcart_num=F('shoppingcart_num') + num)
            if warning:
                SkuStock.stat_warning(sku_id, change_fields, warning, stat)

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
        from flashsale.dinghuo.models import ReturnGoods, RGDetail
        rg_sku = RGDetail.objects.filter(return_goods__status__in=[1, 3, 31, 4]).values('skuid')
        rg_sku = [i['skuid'] for i in rg_sku]
        order_skus = [o['chichu_id'] for o in OrderDetail.objects.filter(
            arrival_time__gt=(datetime.datetime.now() - datetime.timedelta(days=20)), arrival_quantity__gt=0).values(
            'chichu_id').distinct()]

        has_nouse_stock_sku_product = [(stat['id'], stat['product_id']) for stat in
                                       SkuStock._objects.exclude(sku_id__in=rg_sku).filter(sku_id__in=order_skus,
                                                                                           sold_num__lt=F(
                                                                                               'history_quantity') + F(
                                                                                               'adjust_quantity') + F(
                                                                                               'inbound_quantity') + F(
                                                                                               'return_quantity') \
                                                                                                        - F(
                                                                                               'rg_quantity')).values(
                                           'id',
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
        stat = SkuStock._objects.get(sku_id=sku_id)
        ori_adjust_quantity = stat.adjust_quantity
        stat.adjust_quantity = adjust_quantity
        stat.save()

        # SkuStock._objects.filter(sku_id=sku_id).update(adjust_quantity=adjust_quantity)

    @staticmethod
    def add_adjust_num(sku_id, num):
        SkuStock._objects.filter(sku_id=sku_id).update(adjust_quantity=F('adjust_quantity') + num)

    @staticmethod
    def get_auto_sale_stock():
        from shopback.categorys.models import ProductCategory
        from .product import Product
        pid = ProductCategory.objects.get(name=u'优尼世界').cid
        return SkuStock._objects.filter(product__status=Product.NORMAL).filter(
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

    def assign(self, psi_id=None, orderlist=None, again=True):
        """
            分配有从库存分配和从订货单分配两种方式。
            订货入仓一般走订货单分配法，以确保正确分配。
            加个again，防止库存错误造成递归死循环
        """
        from shopback.trades.models import PackageSkuItem
        now_num = self.realtime_quantity - self.assign_num
        if now_num == 0:
            return
        if now_num < 0:
            self.relase_assign(psi_id, orderlist)
            return
        if psi_id:
            psi = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                id=psi_id,
                                                assign_status=PackageSkuItem.NOT_ASSIGNED).first()
            if psi:
                if now_num >= psi.num:
                    now_num -= psi.num
                    psi.set_status_assigned(save=True)
        elif orderlist:
            psis = []
            new_assign_num = 0
            for psi in PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                     purchase_order_unikey=orderlist.purchase_order_unikey,
                                                     assign_status=PackageSkuItem.NOT_ASSIGNED):
                if now_num >= psi.num:
                    now_num -= psi.num
                    new_assign_num += psi.num
                    psi.set_status_assigned(save=False)
                    psis.append(psi)
                else:
                    continue
            self.assign_num += new_assign_num
            for psi in psis:
                psi.save()
            self.save()
            if again:
                self.assign(again=False)
        else:
            # if self.realtime_quantity > PackageSkuItem.objects.filter(sku_id=self.sku_id, assign_status=PackageSkuItem.NOT_ASSIGNED).aggregate(Sum('num')):
            psis = []
            new_assign_num = 0
            for psi in PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                     assign_status=PackageSkuItem.NOT_ASSIGNED).order_by('pay_time'):
                if now_num >= psi.num:
                    now_num -= psi.num
                    new_assign_num += psi.num
                    psi.set_status_assigned(save=False)
                    psis.append(psi)
                else:
                    break
            self.assign_num += new_assign_num
            self.save()
            for psi in psis:
                psi.save()

    def can_assign(self, sku_item):
        from shopback.trades.models import PackageSkuItem
        if PackageSkuItem.objects.filter(# status=PSI_STATUS.READY,
                                         sku_id=self.sku_id, assign_status=PackageSkuItem.NOT_ASSIGNED).exists():
            self.assign()
        now_num = self.realtime_quantity - self.assign_num
        return now_num > sku_item.num

    def relase_assign(self, psi_id=None, orderlist=None, again=True):
        """
            分配的反向操作
        """
        from shopback.trades.models import PackageSkuItem
        if self.assign_num <= 0:
            return
        now_num = self.realtime_quantity - self.assign_num
        check_if_err = False
        if now_num > 0:
            return
        if psi_id:
            psi = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                purchase_order_unikey=orderlist.purchase_order_unikey,
                                                # status=PSI_STATUS.ASSIGNED,
                                                assign_status=PackageSkuItem.ASSIGNED).first()
            if psi:
                # psi.set_status_not_assigned()
                psi.reset_assign_status()
            else:
                check_if_err = True
                SkuStock.set_psi_not_assigned(self.sku_id, 0, stat=True, warning=True)
        elif orderlist:
            psi = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                purchase_order_unikey=orderlist.purchase_order_unikey,
                                                # status=PSI_STATUS.ASSIGNED,
                                                assign_status=PackageSkuItem.ASSIGNED).first()
            if psi:
                # psi.set_status_not_assigned()
                psi.reset_assign_status()
                SkuStock.set_psi_not_assigned(self.sku_id, 0, stat=True, warning=True)
            else:
                check_if_err = True
                SkuStock.set_psi_not_assigned(self.sku_id, 0, stat=True, warning=True)
        else:
            psi = PackageSkuItem.objects.filter(sku_id=self.sku_id,
                                                # status=PSI_STATUS.ASSIGNED,
                                                assign_status=PackageSkuItem.ASSIGNED).order_by(
                '-pay_time').first()
            if psi:
                # psi.set_status_not_assigned()
                psi.reset_assign_status()
            else:
                check_if_err = True
                SkuStock.set_psi_not_assigned(self.sku_id, 0, stat=True, warning=True)
        # if self.realtime_quantity - self.assign_num < 0 and self.assign_num > 0 and check_if_err and again:
        #     self.relase_assign(again=False)


def invalid_apiskustat_cache(sender, instance, *args, **kwargs):
    if hasattr(sender, 'API_CACHE_KEY_TPL'):
        logger.debug('invalid_apiskustat_cache: %s' % instance.sku_id)
        cache.delete(SkuStock.API_CACHE_KEY_TPL.format(instance.sku_id))


post_save.connect(invalid_apiskustat_cache, sender=SkuStock, dispatch_uid='post_save_invalid_apiskustat_cache')


#
# def assign_stock_to_package_sku_item(sender, instance, created, **kwargs):
#     from shopback.items.tasks import task_assign_stock_to_package_sku_item
#     if not created:
#         logger = logging.getLogger('service')
#         logger.info({
#             'action': 'skustat.pstat.assign_stock_to_package_sku_item',
#             'instance': instance.sku_id,
#             'realtime_quantity': instance.realtime_quantity,
#             'assign_num': instance.assign_num,
#             'sold_num': instance.sold_num,
#             'post_num': instance.post_num,
#             'not_assign_num': instance.not_assign_num,
#         })
#         task_assign_stock_to_package_sku_item.delay(instance)
#
# from shopmanager.celery_settings import CLOSE_CELERY
# if not CLOSE_CELERY:
#     post_save.connect(assign_stock_to_package_sku_item, sender=SkuStock,
#                   dispatch_uid='post_save_assign_stock_to_package_sku_item')


def product_sku_stats_agg(sender, instance, created, **kwargs):
    # import elasticsearch
    """ 统计实时库存的变化到统计app中"""
    try:
        from statistics.tasks import task_update_product_sku_stats
        task_update_product_sku_stats.apply_async(args=[instance], countdown=3)
    except Exception, exc:
        logger.error(exc.message)


post_save.connect(product_sku_stats_agg, sender=SkuStock, dispatch_uid='post_save_product_sku_stats')


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
        stat.rg_quantity = RGDetail.get_inferior_total(sku_id, SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME)
        stat.return_quantity = RefundProduct.get_total(sku_id, can_reuse=False,
                                                       begin_time=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME)
        stat.inbound_quantity = InBoundDetail.get_inferior_total(
            sku_id, begin_time=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME)
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

    # sku_id = models.IntegerField(null=True, db_index=True, verbose_name=u'商品SKU记录ID')
    # product_id = models.IntegerField(null=True, db_index=True, verbose_name=u'商品记录ID')
    sku = models.ForeignKey('ProductSku', null=True, verbose_name=u'SKU')
    product = models.ForeignKey('Product', null=True, verbose_name=u'商品')

    init_waitassign_num = models.IntegerField(default=0, verbose_name=u'上架前待分配数')
    num = models.IntegerField(default=0, verbose_name=u'上架期间购买数')
    sale_start_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'开始时间')
    sale_end_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'结束时间')

    created = models.DateTimeField(null=True, blank=True, db_index=True, auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name=u'状态')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id, self.sku_id)

    @property
    def properties_name(self):
        from .product import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])

    @staticmethod
    def stop_pre_stat(product_id):
        ProductSkuSaleStats.objects.filter(product_id=product_id, status=0).update(
            status=ProductSkuSaleStats.ST_DISCARD)

    @staticmethod
    def create(sku):
        product_id = sku.product_id
        sku_stats = SkuStock.get_by_sku(sku.id)
        wait_assign_num = sku_stats.wait_assign_num
        stats_uni_key = gen_productsksalestats_unikey(sku.id)
        stat = ProductSkuSaleStats(uni_key=stats_uni_key,
                                   sku_id=sku.id,
                                   product_id=product_id,
                                   init_waitassign_num=wait_assign_num,
                                   sale_start_time=sku.product.upshelf_time,
                                   sale_end_time=sku.product.offshelf_time)
        stat.save()
        return stat

    @staticmethod
    def get_by_sku(sku_id, status=0, num=None):
        condition = {'sku_id': sku_id}
        if num:
            condition['num'] = num
        else:
            condition['status'] = status
        stat = ProductSkuSaleStats.objects.filter(**condition).order_by('-id').first()
        return stat

    def get_sold_num(self):
        from shopback.trades.models import PackageSkuItem
        total = PackageSkuItem.objects.filter(sku_id=self.sku_id, pay_time__gte=self.sale_start_time,
                                              pay_time__lte=self.sale_end_time, assign_status__in=[0, 1, 2, 4]). \
                    aggregate(total=Sum('num')).get('total') or 0
        return total

    def restat(self):
        if self.num != self.get_sold_num():
            self.num = self.get_sold_num()
            self.save()

    # @property
    # def lock_num(self):
    #     return self.init_waitassign_num + self.num

    def finish(self):
        if not self.sale_end_time:
            self.sale_end_time = self.product.offshelf_time
        self.status = ProductSkuSaleStats.ST_FINISH
        self.save(update_fields=["sale_end_time", "status"])

    def teambuy_out_sale_check(self):
        model_product = self.product.get_product_model()
        if model_product and model_product.is_teambuy:
            from flashsale.pay.models import TeamBuy
            if self.num + model_product.teambuy_person_num > self.sku.remain_num:
                TeamBuy.end_teambuy(self.sku)


def teambuy_out_sale_check(sender, instance, created, **kwargs):
    if not created:
        instance.teambuy_out_sale_check()


post_save.connect(teambuy_out_sale_check, sender=ProductSkuSaleStats, dispatch_uid='post_save_invalid_apiskustat_cache')


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
