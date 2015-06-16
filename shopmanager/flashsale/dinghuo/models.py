# -*- coding:utf-8 -*-
from django.db import models
from shopback.base.fields import BigIntegerAutoField, BigIntegerForeignKey
from .models_user import MyUser, MyGroup
from .models_stats import SupplyChainDataStats
from shopback.items.models import ProductSku, Product


class OrderList(models.Model):
    
    #订单状态
    SUBMITTING = u'草稿'  #提交中
    APPROVAL = u'审核'  #审核
    ZUOFEI = u'作废'  #作废
    COMPLETED = u'验货完成'  #验货完成
    QUESTION = u'有问题'  #有问题
    CIPIN = u'5'  #有次品
    QUESTION_OF_QUANTITY = u'6'  #到货有问题
    DEALED = u'已处理' #已处理
    
    ORDER_PRODUCT_STATUS = (
        (SUBMITTING, u'草稿'),
        (APPROVAL, u'审核'),
        (ZUOFEI, u'作废'),
        (QUESTION, u'有次品又缺货'),
        (CIPIN, u'有次品'),
        (QUESTION_OF_QUANTITY, u'到货数量问题'),
        (COMPLETED, u'验货完成'),
        (DEALED, u'已处理'),
    )
    
    id = BigIntegerAutoField(primary_key=True)
    buyer_name = models.CharField(default="",max_length=32, verbose_name=u'买手')
    order_amount = models.FloatField(default=0, verbose_name=u'金额')
    supplier_name = models.CharField(default="",blank=True, max_length=128, verbose_name=u'供应商')
    express_company = models.CharField(default="", blank=True, max_length=32, verbose_name=u'快递公司')
    express_no = models.CharField(default="",blank=True, max_length=32, verbose_name=u'快递单号')
    receiver = models.CharField(default="", max_length=32, verbose_name=u'仓库负责人')
    costofems = models.IntegerField(default=0, verbose_name=u'快递费用')
    status = models.CharField(max_length=32, verbose_name=u'订货单状态', choices=ORDER_PRODUCT_STATUS)
    created = models.DateField(auto_now_add=True, verbose_name=u'订货日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    note = models.TextField(default="", blank=True, verbose_name=u'备注信息')

    class Meta:
        db_table = 'suplychain_flashsale_orderlist'
        verbose_name = u'订货表'
        verbose_name_plural = u'订货表'

    def costofems_cash(self):
        return self.costofems / 100.0
    costofems_cash.allow_tags = True
    costofems_cash.short_description = u"快递费用"

    def __unicode__(self):
        return '<%s,%s,%s>' % (str(self.id or ''), self.id, self.buyer_name)


class OrderDetail(models.Model):
    
    id = BigIntegerAutoField(primary_key=True)
    
    orderlist = BigIntegerForeignKey(OrderList, verbose_name=u'订单编号')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(max_length=100, verbose_name=u'产品尺寸')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'正品数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')
    non_arrival_quantity = models.IntegerField(default=0, verbose_name=u'未到数量')

    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'生成日期')#index
    updated = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'更新日期')#index
    arrival_time = models.DateTimeField(blank=True, verbose_name=u'到货时间')

    class Meta:
        db_table = 'suplychain_flashsale_orderdetail'
        verbose_name = u'订货明细表'
        verbose_name_plural = u'订货明细表'

    def __unicode__(self):
        return self.product_id


class orderdraft(models.Model):
    buyer_name = models.CharField(default="None", max_length=32, verbose_name=u'买手')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(default="", max_length=20, verbose_name=u'产品尺寸')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    created = models.DateField(auto_now_add=True, verbose_name=u'生成日期')

    class Meta:
        db_table = 'suplychain_flashsale_orderdraft'
        verbose_name = u'草稿表'
        verbose_name_plural = u'草稿表'

    def __unicode__(self):
        return self.product_name


class ProductSkuDetail(models.Model):

    product_sku = models.OneToOneField(ProductSku, primary_key=True, related_name='details', verbose_name=u'库存商品规格')
    exist_stock_num = models.IntegerField(default=0, verbose_name=u'上架前库存')
    sample_num = models.IntegerField(default=0, verbose_name=u'样品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'flash_sale_product_sku_detail'
        verbose_name = u'特卖商品库存'
        verbose_name_plural = u'特卖商品库存列表'

    def __unicode__(self):
        return '<%s,%s,%s>'%(self.product_sku.id, self.product_sku.properties_name, self.product_sku.outer_id)

from shopback import signals 

def init_stock_func(sender,product_list,*args,**kwargs):
    
    for pro_bean in product_list:
        sku_qs = pro_bean.prod_skus.all()
        for sku_bean in sku_qs:
            pro_sku_bean = ProductSkuDetail.objects.get_or_create(product_sku_id=sku_bean.id)
            pro_sku_bean[0].exist_stock_num = sku_bean.quantity
            pro_sku_bean[0].save()
            
signals.signal_product_upshelf.connect(init_stock_func, sender=Product)

