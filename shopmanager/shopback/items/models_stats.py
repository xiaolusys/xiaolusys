# coding: utf-8
from django.db import models


class ProductSkuStats(models.Model):
    class Meta:
        db_table = 'shop_items_productskustats'
        app_label = 'items'
        verbose_name = u'库存商品统计数据'
        verbose_name_plural = u'库存商品统计数据列表'

    STATUS = ((0,'EFFECT'),(1,'DISCARD'))
    
    sku_id = models.IntegerField(null=True, unique=True, verbose_name='商品SKU记录ID')
    product_id = models.IntegerField(null=True, db_index=True, verbose_name='商品记录ID')

    assign_num = models.IntegerField(default=0, verbose_name='分配数')  # 未出库包裹单中已分配的sku数量
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品数")  # 保存对应sku的次品数量
    
    history_quantity = models.IntegerField(default=0, verbose_name='历史库存数')  #
    inbound_quantity = models.IntegerField(default=0, verbose_name='入仓库存数')  #
    post_num = models.IntegerField(default=0, verbose_name='已发货数')  #
    sold_num = models.IntegerField(default=0, verbose_name='已被购买数')  #

    shoppingcart_num = models.IntegerField(default=0, verbose_name='加入购物车数')  #
    waitingpay_num = models.IntegerField(default=0, verbose_name='等待付款数')  #
    
    created = models.DateTimeField(null=True, blank=True, db_index=True,auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name='状态') 

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.product_id ,self.sku_id)

    @property
    def realtime_quantity(self):
        return self.history_quantity + self.inbound_quantity - self.post_num

    @property
    def aggregate_quantity(self):
        return self.history_quantity + self.inbound_quantity

    @property
    def wait_post_num(self):
        return self.sold_num - self.post_num

    @property
    def wait_assign_num(self):
        return self.sold_num - self.assign_num

    @property
    def realtime_lock_num(self):
        return self.shoppingcart_num + self.waitingpay_num

    @property
    def properties_name(self):
        from shopback.items.models import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])

    
class ProductSkuSaleStats(models.Model):
    class Meta:
        db_table = 'shop_items_productskusalestats'
        app_label = 'items'
        verbose_name = u'商品购买统计数据'
        verbose_name_plural = u'商品购买统计数据列表'
    
    STATUS = ((0,'EFFECT'), (1,'DISCARD'), (2,'FINISH'))

    # uni_key = sku_id + number of finished records
    uni_key = models.IntegerField(null=True, unique=True, verbose_name='UNIQUE ID')
    
    sku_id = models.IntegerField(null=True, db_index=True, verbose_name='商品SKU记录ID')
    product_id = models.IntegerField(null=True, db_index=True, verbose_name='商品记录ID')

    init_wait_assign_num = models.IntegerField(default=0, verbose_name='上架前待分配数')
    num = models.IntegerField(default=0, verbose_name='上架期间购买数')
    sale_start_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='开始时间')
    sale_end_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='结束时间')
    
    created = models.DateTimeField(null=True, blank=True, db_index=True,auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')
    status = models.IntegerField(default=0, db_index=True, choices=STATUS, verbose_name='状态') 

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.properties_alias or self.properties_name)

    @property
    def properties_name(self):
        from shopback.items.models import ProductSku
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return ':'.join([product_sku.properties_name, product_sku.properties_alias])

def gen_productsksalestats_unikey(sku_id):
    count = ProductSkuSaleStats.objects.filter(sku_id=sku_id,status=1).count()
    return "%s-%s" % (sku_id, count)
    
    
