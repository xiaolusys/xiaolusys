# coding=utf-8
"""
退款率模型, 数据计算方法
"""
from django.db import models
from django.db.models import Sum


class PayRefundRate(models.Model):
    """"
    任务执行生成数据 每天定时运行 将过去15天内的特卖订单退款率数据写入数据库中
    """
    date_cal = models.DateField(db_index=True, unique=True, verbose_name=u'结算日期')  # 唯一
    ref_num = models.IntegerField(default=0, verbose_name=u'退款单数')
    pay_num = models.IntegerField(default=0, verbose_name=u'付款单数')
    ref_rate = models.FloatField(default=0.0, verbose_name=u'退款率')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'flashsale_pay_refundrate'
        verbose_name = u'特卖/退款率表'
        verbose_name_plural = u'特卖/退款率列表'

    def __unicode__(self):
        return u"%s" % self.date_cal


class PayRefNumRcord(models.Model):
    """"
    信号触发　
    付款24小时外未发货申请数       ref_num_out
    付款24小时内未发货申请数       ref_num_in
    付款发货后申请数              ref_sed_num
    """
    date_cal = models.DateField(db_index=True, unique=True, verbose_name=u'结算日期')  # 唯一
    ref_num_out = models.IntegerField(default=0, verbose_name=u'24h外未发货申请数')
    ref_num_in = models.IntegerField(default=0, verbose_name=u'24h内未发货申请数')
    ref_sed_num = models.IntegerField(default=0, verbose_name=u'发货后申请数')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'flashsale_pay_refund_num_record'
        verbose_name = u'特卖/退款数记录表'
        verbose_name_plural = u'特卖/退款数记录表'

    def __unicode__(self):
        return u"%s" % self.date_cal


class ProRefunRcord(models.Model):
    """
    信号触发记录　针对单个产品的　退货统计
    付款24小时外未发货申请数       ref_num_out
    付款24小时内未发货申请数       ref_num_in
    付款发货后申请数              ref_sed_num
    """
    product = models.IntegerField(db_index=True, unique=True, verbose_name=u'产品id')
    ref_num_out = models.IntegerField(default=0, verbose_name=u'24h外未发货申请数')
    ref_num_in = models.IntegerField(default=0, verbose_name=u'24h内未发货申请数')
    ref_sed_num = models.IntegerField(default=0, verbose_name=u'发货后申请数')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'flashsale_pay_product_refund_record'
        verbose_name = u'特卖/产品退款数记录表'
        verbose_name_plural = u'特卖/产品退款数记录表'

    def __unicode__(self):
        return u"%s" % self.product

    def sale_num(self):
        """ 返回该产品的销售数量　"""
        from shopback.items.models import ProductDaySale
        sale = ProductDaySale.objects.filter(product_id=self.product)
        sale_num = sale.aggregate(total_sale=Sum('sale_num')).get("total_sale") or 0
        return sale_num

    def item_product(self):
        from shopback.items.models import Product
        try:
            pro = Product.objects.get(id=self.product)
        except Product.DoesNotExist:
            pro = None
        return pro

    def same_mod(self):
        from shopback.items.models import Product
        pro = self.item_product()
        if pro is None:
            return []
        pro_ids = Product.objects.filter(model_id=pro.model_id).values('id')
        return pro_ids

    def same_mod_ref_num_out(self):
        pro_ids = self.same_mod()
        pro_rcds = ProRefunRcord.objects.filter(product__in=pro_ids)
        mod_ref_num_out = pro_rcds.aggregate(total_out=Sum('ref_num_out')).get("total_out") or 0
        return mod_ref_num_out

    def same_mod_ref_num_in(self):
        pro_ids = self.same_mod()
        pro_rcds = ProRefunRcord.objects.filter(product__in=pro_ids)
        mod_ref_num_in = pro_rcds.aggregate(total_in=Sum('ref_num_in')).get("total_in") or 0
        return mod_ref_num_in

    def same_mod_ref_num_sed(self):
        pro_ids = self.same_mod()
        pro_rcds = ProRefunRcord.objects.filter(product__in=pro_ids)
        mod_ref_sed_num = pro_rcds.aggregate(total_sed=Sum('ref_sed_num')).get("total_sed") or 0
        return mod_ref_sed_num

    def same_mod_sale_num(self):
        """ 同款销售数量　"""
        from shopback.items.models import ProductDaySale
        sale = ProductDaySale.objects.filter(product_id__in=self.same_mod())
        sale_num = sale.aggregate(total_sale=Sum('sale_num')).get("total_sale") or 0
        return sale_num

    def reason_ana(self):
        """ 同款原因分析　"""
        pro_ids = self.same_mod()
        from flashsale.pay.models_refund import SaleRefund
        sale_refunds = SaleRefund.objects.filter(item_id__in=pro_ids)
        reason = {}
        des = []
        for ref in sale_refunds:
            if reason.has_key(ref.reason):
                reason[ref.reason] += ref.refund_num
            else:
                reason[ref.reason] = ref.refund_num
            des.append(ref.desc)
        info_base = {"reason": reason, "desc": des}
        return info_base

    @property
    def sale_buyer(self):
        """ 选品买手　"""
        from supplychain.supplier.models import SaleProduct
        pro = self.item_product()
        if pro is None:
            return None
        try:
            sale_pro = SaleProduct.objects.get(id=pro.sale_product)
            contactor = sale_pro.contactor.id
        except SaleProduct.DoesNotExist:
            contactor = None
        return contactor