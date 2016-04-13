# -*- coding:utf-8 -*-
from django.db import models

from django.contrib.auth.models import User
from core.fields import BigIntegerAutoField

from core.fields import JSONCharMyField
from shopback.base.fields import BigIntegerAutoField, BigIntegerForeignKey
from shopback.items.models import ProductSku, Product
from shopback.refunds.models import Refund
from supplychain.supplier.models import SaleSupplier

from .models_user import MyUser, MyGroup
from .models_stats import SupplyChainDataStats


class OrderList(models.Model):
    # 订单状态
    SUBMITTING = u'草稿'  # 提交中
    APPROVAL = u'审核'  # 审核
    ZUOFEI = u'作废'  # 作废
    COMPLETED = u'验货完成'  # 验货完成
    QUESTION = u'有问题'  # 有问题
    CIPIN = u'5'  # 有次品
    QUESTION_OF_QUANTITY = u'6'  # 到货有问题
    DEALED = u'已处理'  # 已处理
    SAMPLE = u'7'  # 样品
    NEAR = u'1'  # 江浙沪皖
    SHANGDONG = u'2'  # 山东
    GUANGDONG = u'3'  # 广东
    YUNDA = u'YUNDA'
    STO = u'STO'
    ZTO = u'ZTO'
    EMS = u'EMS'
    ZJS = u'ZJS'
    SF = u'SF'
    YTO = u'YTO'
    HTKY = u'HTKY'
    TTKDEX = u'TTKDEX'
    QFKD = u'QFKD'
    DBKD = u'DBKD'

    CREATED_BY_PERSON = 1
    CREATED_BY_MACHINE = 2

    ORDER_PRODUCT_STATUS = (
        (SUBMITTING, u'草稿'),
        (APPROVAL, u'审核'),
        (ZUOFEI, u'作废'),
        (QUESTION, u'有次品又缺货'),
        (CIPIN, u'有次品'),
        (QUESTION_OF_QUANTITY, u'到货数量问题'),
        (COMPLETED, u'验货完成'),
        (DEALED, u'已处理'),
        (SAMPLE, u'样品'),
    )
    ORDER_DISTRICT = (
        (NEAR, u'江浙沪皖'),
        (SHANGDONG, u'山东'),
        (GUANGDONG, u'广东福建'),
    )
    EXPRESS_CONPANYS = (
        (YUNDA, u'韵达速递'),
        (STO, u'申通快递'),
        (ZTO, u'中通快递'),
        (EMS, u'邮政'),
        (ZJS, u'宅急送'),
        (SF, u'顺丰速运'),
        (YTO, u'圆通'),
        (HTKY, u'汇通快递'),
        (TTKDEX, u'天天快递'),
        (QFKD, u'全峰快递'),
        (DBKD, u'德邦快递'),
    )
    id = BigIntegerAutoField(primary_key=True)
    buyer = models.ForeignKey(User, null=True, related_name='dinghuo_orderlists', verbose_name=u'负责人')
    buyer_name = models.CharField(default="", max_length=32, verbose_name=u'买手')
    order_amount = models.FloatField(default=0, verbose_name=u'金额')
    supplier_name = models.CharField(default="", blank=True, max_length=128, verbose_name=u'商品链接')
    supplier_shop = models.CharField(default="", blank=True, max_length=32, verbose_name=u'供应商店铺名')
    supplier = models.ForeignKey(SaleSupplier, null=True, blank=True, related_name='dinghuo_orderlist',
                                 verbose_name=u'供应商')

    express_company = models.CharField(choices=EXPRESS_CONPANYS, blank=True, max_length=32, verbose_name=u'快递公司')
    express_no = models.CharField(default="", blank=True, max_length=32, verbose_name=u'快递单号')

    receiver = models.CharField(default="", max_length=32, verbose_name=u'负责人')
    costofems = models.IntegerField(default=0, verbose_name=u'快递费用')
    status = models.CharField(max_length=32, db_index=True, verbose_name=u'订货单状态', choices=ORDER_PRODUCT_STATUS)
    pay_status = models.CharField(max_length=32, db_index=True, verbose_name=u'收款状态')
    p_district = models.CharField(max_length=32, default=NEAR, verbose_name=u'地区', choices=ORDER_DISTRICT)  # 从发货地对应仓库
    reach_standard = models.BooleanField(default=False, verbose_name=u"达标")
    created = models.DateField(auto_now_add=True, db_index=True, verbose_name=u'订货日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    note = models.TextField(default="", blank=True, verbose_name=u'备注信息')
    created_by = models.SmallIntegerField(choices=((CREATED_BY_PERSON, '人工'), (CREATED_BY_MACHINE, '自动')),
                                          default=CREATED_BY_PERSON, verbose_name=u'创建方式')
    last_pay_date = models.DateField(null=True, blank=True, verbose_name=u'最后下单日期')
    is_postpay = models.BooleanField(default=False, verbose_name=u'是否后付款')

    class Meta:
        db_table = 'suplychain_flashsale_orderlist'
        app_label = 'dinghuo'
        verbose_name = u'订货表'
        verbose_name_plural = u'订货表'
        permissions = [("change_order_list_inline", u"修改后台订货信息"), ]

    def costofems_cash(self):
        return self.costofems / 100.0

    costofems_cash.allow_tags = True
    costofems_cash.short_description = u"快递费用"

    def __unicode__(self):
        return '<%s,%s>' % (str(self.id or ''), self.buyer_name)


class OrderDetail(models.Model):
    id = BigIntegerAutoField(primary_key=True)
    orderlist = models.ForeignKey(OrderList, related_name='order_list', verbose_name=u'订单编号')
    product_id = models.CharField(db_index=True, max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, db_index=True, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, db_index=True, verbose_name=u'规格id')
    product_chicun = models.CharField(max_length=100, verbose_name=u'产品尺寸')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'正品数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')
    non_arrival_quantity = models.IntegerField(default=0, verbose_name=u'未到数量')

    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'生成日期')  # index
    updated = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'更新日期')  # index
    arrival_time = models.DateTimeField(blank=True, verbose_name=u'到货时间')

    class Meta:
        db_table = 'suplychain_flashsale_orderdetail'
        app_label = 'dinghuo'
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
        app_label = 'dinghuo'
        verbose_name = u'草稿表'
        verbose_name_plural = u'草稿表'

    def __unicode__(self):
        return self.product_name


class ProductSkuDetail(models.Model):
    product_sku = models.BigIntegerField(unique=True, verbose_name=u'库存商品规格')
    exist_stock_num = models.IntegerField(default=0, verbose_name=u'上架前库存')
    sample_num = models.IntegerField(default=0, verbose_name=u'样品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'flash_sale_product_sku_detail'
        app_label = 'dinghuo'
        verbose_name = u'特卖商品库存'
        verbose_name_plural = u'特卖商品库存列表'

    def __unicode__(self):
        return u'<%s>' % (self.product_sku)


from shopback import signals


def init_stock_func(sender, product_list, *args, **kwargs):
    import datetime
    from django.db.models import Sum
    today = datetime.date.today()

    for pro_bean in product_list:
        sku_qs = pro_bean.prod_skus.all()
        for sku_bean in sku_qs:
            total_num = OrderDetail.objects.filter(chichu_id=sku_bean.id,
                                                   orderlist__created__range=(
                                                       today - datetime.timedelta(days=7), today)).exclude(
                orderlist__status=OrderList.ZUOFEI).aggregate(total_num=Sum('arrival_quantity')).get(
                'total_num') or 0
            pro_sku_beans = ProductSkuDetail.objects.get_or_create(product_sku=sku_bean.id)
            pro_sku_bean = pro_sku_beans[0]
            result_num = sku_bean.quantity - sku_bean.wait_post_num - total_num
            pro_sku_bean.exist_stock_num = result_num if result_num > 0 else 0
            pro_sku_bean.sample_num = 0
            sku_bean.memo = ""
            sku_bean.save()
            pro_sku_bean.save()


signals.signal_product_upshelf.connect(init_stock_func, sender=Product)


class ReturnGoods(models.Model):
    CREATE_RG = 0
    VERIFY_RG = 1
    OBSOLETE_RG = 2
    DELIVER_RG = 3
    SUCCEED_RG = 4
    FAILED_RG = 5
    MEMO_DEFAULT = u'\u6536\u4ef6\u4eba:\r\n\u624b\u673a/\u7535\u8bdd:\r\n\u6536\u4ef6\u5730\u5740:'
    RG_STATUS = ((CREATE_RG, u"创建退货单"), (VERIFY_RG, u"审核通过"), (OBSOLETE_RG, u"作废退货单")
                 , (DELIVER_RG, u"已发货退货单"), (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))

    product_id = models.BigIntegerField(db_index=True, verbose_name=u"退货商品id")
    supplier_id = models.IntegerField(db_index=True, verbose_name=u"供应商id")
    return_num = models.IntegerField(default=0, verbose_name=u"退货数量")
    sum_amount = models.FloatField(default=0.0, verbose_name=u"退货总金额")
    noter = models.CharField(max_length=32, verbose_name=u"退货单录入人")
    consigner = models.CharField(max_length=32, blank=True, verbose_name=u"发货人")
    consign_time = models.DateTimeField(blank=True, null=True, verbose_name=u'发货时间')
    sid = models.CharField(max_length=64, blank=True, verbose_name=u"发货物流单号")
    status = models.IntegerField(default=0, choices=RG_STATUS, db_index=True, verbose_name=u"退货状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=512, blank=True, default=MEMO_DEFAULT, verbose_name=u"退货备注")

    class Meta:
        db_table = 'flashsale_dinghuo_returngoods'
        app_label = 'dinghuo'
        verbose_name = u'商品库存退货表'
        verbose_name_plural = u'商品库存退货列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.supplier_id, self.product_id)


class RGDetail(models.Model):
    skuid = models.BigIntegerField(db_index=True, verbose_name=u"退货商品skuid")
    return_goods = models.ForeignKey(ReturnGoods, related_name='rg_details', verbose_name=u'退货单信息')
    num = models.IntegerField(default=0, verbose_name=u"正品退货数量")
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品退货数量")
    price = models.FloatField(default=0.0, verbose_name=u"退回价格")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'flashsale_dinghuo_rg_detail'
        app_label = 'dinghuo'
        verbose_name = u'商品库存退货明细表'
        verbose_name_plural = u'商品库存退货明细列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.skuid, self.return_goods)

    def sync_rg_field(self):
        rgds = self.return_goods.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_goods.return_num = total_num
        self.return_goods.sum_amount = total_amount
        self.return_goods.save()


from django.db.models.signals import post_save


def syncRGdTreturn(sender, instance, **kwargs):
    instance.sync_rg_field()


post_save.connect(syncRGdTreturn, sender=RGDetail)


class SaleInventoryStat(models.Model):
    """
    （只统计小鹿特卖商品）统计当天的订货表的新增采购数，未到货总数，到货数，发出件数，总库存数
    """
    CHILD = 1
    FEMALE = 2

    INVENTORY_CATEGORY = ((CHILD, u'童装'), (FEMALE, u'女装'))
    newly_increased = models.IntegerField(default=0, verbose_name=u'新增采购数')
    not_arrive = models.IntegerField(default=0, verbose_name=u'未到货数')
    arrived = models.IntegerField(default=0, verbose_name=u'到货数')
    deliver = models.IntegerField(default=0, verbose_name=u'发出数')
    inventory = models.IntegerField(default=0, verbose_name=u'库存')
    category = models.IntegerField(blank=True, null=True, db_index=True, choices=INVENTORY_CATEGORY,
                                   verbose_name=u'分类')
    stat_date = models.DateField(verbose_name=u'统计日期')

    class Meta:
        db_table = 'flashsale_inventory_stat'
        app_label = 'dinghuo'
        verbose_name = u'特卖入库及库存每日统计'
        verbose_name_plural = u'特卖入库及库存每日统计列表'

    def __unicode__(self):
        return u'<%s>' % self.stat_date


class InBound(models.Model):
    INVALID = 0
    NORMAL = 1
    PENDING = 2

    SUPPLIER = 1
    REFUND = 2

    STATUS_CHOICES = (
        (INVALID, u'作废'),
        (NORMAL, u'正常'),
        (PENDING, u'待处理')
    )
    supplier = models.ForeignKey(SaleSupplier, null=True, blank=True,
                                 related_name='inbounds', verbose_name=u'供应商')
    express_no = models.CharField(max_length=32, blank=True, verbose_name=u'快递单号')
    sent_from = models.SmallIntegerField(default=SUPPLIER,
                                         choices=((SUPPLIER, u'供应商'), (REFUND, u'退货')), verbose_name=u'包裹类型')
    refund = models.ForeignKey(Refund, null=True, blank=True,
                               related_name='inbounds', verbose_name=u'退货单')
    creator = models.ForeignKey(User, related_name='inbounds', verbose_name=u'创建人')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(default=NORMAL, choices=STATUS_CHOICES, verbose_name=u'状态')
    images = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'图片')
    orderlist_ids = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'订货单ID')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'


class InBoundDetail(models.Model):
    NORMAL = 1
    PROBLEM = 2

    inbound = models.ForeignKey(InBound, related_name='details', verbose_name=u'入库单')
    product = models.ForeignKey(Product, null=True, blank=True,
                                related_name='inbound_details', verbose_name=u'入库颜色')
    sku = models.ForeignKey(ProductSku, null=True, blank=True,
                            related_name='inbound_details', verbose_name=u'入库规格')

    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'颜色编码')
    properties_name = models.CharField(max_length=128, blank=True, verbose_name=u'规格')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'已到数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    status = models.SmallIntegerField(default=NORMAL, choices=((NORMAL, u'正常'), (PROBLEM, u'疑难')), verbose_name=u'状态')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'flashsale_dinghuo_inbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓单明细'
        verbose_name_plural = u'入仓单明细列表'


class OrderDetailInBoundDetail(models.Model):
    INVALID = 0
    NORMAL = 1

    orderdetail = models.ForeignKey(OrderDetail, related_name='records', verbose_name=u'订货明细')
    inbounddetail = models.ForeignKey(InBoundDetail, related_name='records', verbose_name=u'入仓明细')
    arrival_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'正品数')
    inferior_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'次品数')
    status = models.SmallIntegerField(default=NORMAL,
                                      choices=((NORMAL, u'正常'), (INVALID, u'无效')), verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'dinghuo_orderdetailinbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓订货明细对照'
        verbose_name_plural = u'入仓订货明细对照列表'
