# coding=utf-8
from __future__ import unicode_literals
"""
退款率模型, 数据计算方法
"""
from django.db import models
from django.db.models import Sum
from shopback.items.models import Product
from shopback.items.models import ProductDaySale
from flashsale.pay.models import SaleRefund
from django.contrib.auth.models import User
from supplychain.supplier.models import SaleProduct


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
        app_label = 'refunds'
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
        app_label = 'refunds'
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
    contactor = models.BigIntegerField(default=0, db_index=True, verbose_name=u'接洽人')
    pro_model = models.BigIntegerField(default=0, db_index=True, verbose_name=u'产品款式id')
    sale_date = models.DateField(auto_now=True, db_index=True, verbose_name=u'上架时间')
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'flashsale_pay_product_refund_record'
        app_label = 'refunds'
        verbose_name = u'特卖/产品退款数记录表'
        verbose_name_plural = u'特卖/产品退款数记录表'
        permissions = [('browser_all_pro_duct_ref_lis', u'浏览买手所有产品的退货状况记录')]

    def __unicode__(self):
        return u"%s" % self.product

    def item_product(self):
        try:
            pro = Product.objects.get(id=self.product)
        except Product.DoesNotExist:
            pro = None
        return pro

    def same_mod(self):
        pro_ids = Product.objects.filter(model_id=self.pro_model).values('id')
        return pro_ids

    def same_mod_sale_num(self):
        """ 同款销售数量　"""
        sale = ProductDaySale.objects.filter(product_id__in=self.same_mod())
        sale_num = sale.aggregate(total_sale=Sum('sale_num')).get("total_sale") or 0
        return sale_num

    def reason_ana(self):
        """ 同款原因分析　"""
        pro_ids = self.same_mod()
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

    def pro_pic(self):
        pro = self.item_product()
        if pro is not None:
            return pro.pic_path
        else:
            return None

    def pro_contactor(self):
        """　接洽人　"""
        try:
            user = User.objects.get(id=self.contactor)
            return user.username
        except User.DoesNotExist:
            return None

    def sale_time(self):
        """ 上架时间　"""
        pro = self.item_product()
        if pro is not None:
            return pro.sale_time
        return None

    def pro_supplier(self):
        """ 供应商　"""
        try:
            pro = self.item_product()
            sale_product = pro.sale_product
            sal_pro = SaleProduct.objects.get(id=sale_product)
            supplier_name = sal_pro.sale_supplier.supplier_name
            return supplier_name
        except:
            return None

    @property
    def is_female(self):
        """ 通过外部编码　判断　是否是女装　"""
        pro = self.item_product()
        return 1 if pro and str(pro.outer_id).startswith('8')else 0

    @property
    def is_child(self):
        """ 通过外部编码　判断　是否是童装　"""
        pro = self.item_product()
        return 1 if pro and (str(pro.outer_id).startswith(('9', '1'))) else 0
