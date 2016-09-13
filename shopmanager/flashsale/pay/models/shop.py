# coding=utf-8

import random
from django.db import models

from .base import PayBaseModel
from ..managers import ShopProductCategoryManager

from .user import Customer

class CustomerShops(PayBaseModel):
    """
    用户店铺: 存储用户的＂我的店铺＂信息
    """
    customer = models.IntegerField(db_index=True, unique=True, verbose_name=u'用户ID')
    name = models.CharField(max_length=128, null=True, blank=True, verbose_name=u'店铺名称')

    class Meta:
        db_table = 'flashsale_customer_shop'
        app_label = 'pay'
        verbose_name = u'v2/特卖用户店铺'
        verbose_name_plural = u'v2/特卖用户/店铺列表'

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

    @classmethod
    def create_shop(cls, customer):
        shop = cls(customer=customer.id, name=customer.nick)
        shop.save()
        return shop


class CuShopPros(PayBaseModel):
    """
    用于添加从产品客户端＂产品列表＂添加的产品信息
    """
    UP_SHELF = 1
    DOWN_SHELF = 0
    PRO_STATUS = ((UP_SHELF, u'上架'), (DOWN_SHELF, u'下架'))

    shop = models.IntegerField(db_index=True, verbose_name=u'店铺ID')
    customer = models.IntegerField(db_index=True, verbose_name=u'用户id')
    product = models.BigIntegerField(db_index=True, verbose_name=u'店铺产品')
    model = models.IntegerField(db_index=True, default=0, verbose_name=u'款式id')
    pro_status = models.IntegerField(choices=PRO_STATUS, db_index=True, default=1, verbose_name=u'商品状态')

    name = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'商品名称')
    pic_path = models.CharField(max_length=256, blank=True, verbose_name=u'商品主图')
    std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    agent_price = models.FloatField(default=0, verbose_name=u'出售价')
    remain_num = models.IntegerField(default=0, verbose_name=u'预留数量')

    carry_scheme = models.IntegerField(default=0, db_index=True, verbose_name=u'返利模式')
    carry_amount = models.FloatField(default=0, verbose_name=u'返利金额')
    position = models.IntegerField(db_index=True, default=0, verbose_name=u'排序位置')

    pro_category = models.IntegerField(db_index=True, default=0, verbose_name=u'产品类别')
    offshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'下架时间')
    objects = ShopProductCategoryManager()

    class Meta:
        db_table = 'flashsale_cushops_detail'
        app_label = 'pay'
        verbose_name = u'v2/特卖用户店铺产品表'
        verbose_name_plural = u'v2/特卖用户/店铺产品明细列表'

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

    def sale_num_salt(self):
        """ 销量盐 """
        return self.remain_num * 19 + random.choice(xrange(19))

    @classmethod
    def update_down_shelf(cls, product_id):
        """
        修改店铺指定商品id的状态到下架状态
        :type product_id: shopback.item.model Product instance id
        """
        cls.objects.filter(product=product_id).update(pro_status=CuShopPros.DOWN_SHELF)
        return
