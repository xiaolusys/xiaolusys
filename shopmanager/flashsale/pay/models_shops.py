# coding=utf-8

from django.db import models
from .base import PayBaseModel


class CustomerShops(PayBaseModel):
    """
    用户店铺: 存储用户的＂我的店铺＂信息
    """
    customer = models.IntegerField(db_index=True, unique=True, verbose_name=u'用户ID')
    name = models.CharField(max_length=128, null=True, blank=True, verbose_name=u'店铺名称')

    class Meta:
        db_table = 'flashsale_customer_shop'
        verbose_name = u'特卖用户店铺'
        verbose_name_plural = u'特卖用户/店铺列表'

    def __unicode__(self):
        return u'%s-%s' % (self.id, self.customer)

    def get_customer(self):
        """获取用户"""
        from flashsale.pay.models import Customer

        try:
            customer = Customer.objects.get(id=self.customer)
            return customer
        except Customer.DoesNotExist:
            None


class CuShopPros(PayBaseModel):
    """
    用于添加从产品客户端＂产品列表＂添加的产品信息
    """
    UP_SHELF = 1
    DOWN_SHELF = 0
    PRO_STATUS = ((UP_SHELF, u'上架'), (DOWN_SHELF, u'下架'))

    shop = models.IntegerField(db_index=True, verbose_name=u'店铺ID')
    product = models.BigIntegerField(db_index=True, verbose_name=u'店铺产品')
    pro_status = models.IntegerField(choices=PRO_STATUS, default=1, verbose_name=u'商品状态')

    name = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'商品名称')
    pic_path = models.CharField(max_length=256, blank=True, verbose_name=u'商品主图')
    std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    agent_price = models.FloatField(default=0, verbose_name=u'出售价')
    remain_num = models.IntegerField(verbose_name=u'预留数量')

    carry_scheme = models.IntegerField(db_index=True, verbose_name=u'返利模式')
    carry_amount = models.FloatField(default=0, verbose_name=u'返利金额')
    position = models.IntegerField(db_index=True, default=0, verbose_name=u'排序位置')

    class Meta:
        db_table = 'flashsale_cushops_detail'
        verbose_name = u'特卖用户店铺产品表'
        verbose_name_plural = u'特卖用户/店铺产品明细列表'

    def __unicode__(self):
        return u'%s-%s' % (self.id, self.shop)

    def down_shelf_pro(self):
        """ 修改为下架状态 """
        if self.pro_status == CuShopPros.UP_SHELF:
            self.pro_status = CuShopPros.DOWN_SHELF
            self.save()
        return

    def up_shelf_pro(self):
        """ 修改为上架状态 """
        if self.pro_status == CuShopPros.DOWN_SHELF:
            self.pro_status = CuShopPros.UP_SHELF
            self.save()
        return

    def get_customer(self):
        """ 获取店铺商品的添加用户 """
        shop = CustomerShops.objects.get(id=self.shop)
        return shop
