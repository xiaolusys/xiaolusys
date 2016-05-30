# -*- coding:utf-8 -*-
import datetime

from django.db import models
from django.db.models import Sum, Count
from django.db.models.signals import post_save
from django.db.models import Sum, F
from django.contrib.auth.models import User

from core.fields import JSONCharMyField

from shopback.items.models import ProductSku, Product
from shopback.refunds.models import Refund
from supplychain.supplier.models import SaleSupplier


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
    TO_BE_PAID = u'待收款'
    TO_PAY = u'待付款'
    CLOSED = u'完成'
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

    ORDER_PRODUCT_STATUS = ((SUBMITTING, u'草稿'), (APPROVAL, u'审核'),
                            (ZUOFEI, u'作废'), (QUESTION, u'有次品又缺货'),
                            (CIPIN, u'有次品'), (QUESTION_OF_QUANTITY, u'到货数量问题'),
                            (COMPLETED, u'验货完成'), (DEALED, u'已处理'),
                            (SAMPLE, u'样品'), (TO_PAY, u'待付款'),
                            (TO_BE_PAID, u'待收款'), (CLOSED, u'完成'))
    BUYER_OP_STATUS = ((DEALED, u'已处理'), (TO_BE_PAID, u'待收款'), (TO_PAY, u'待付款'),
                       (CLOSED, u'完成'))

    ORDER_DISTRICT = ((NEAR, u'江浙沪皖'),
                      (SHANGDONG, u'山东'),
                      (GUANGDONG, u'广东福建'),)
    EXPRESS_CONPANYS = ((YUNDA, u'韵达速递'),
                        (STO, u'申通快递'),
                        (ZTO, u'中通快递'),
                        (EMS, u'邮政'),
                        (ZJS, u'宅急送'),
                        (SF, u'顺丰速运'),
                        (YTO, u'圆通'),
                        (HTKY, u'汇通快递'),
                        (TTKDEX, u'天天快递'),
                        (QFKD, u'全峰快递'),
                        (DBKD, u'德邦快递'),)
    id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(User,
                              null=True,
                              related_name='dinghuo_orderlists',
                              verbose_name=u'负责人')
    buyer_name = models.CharField(default="", max_length=32, verbose_name=u'买手')
    order_amount = models.FloatField(default=0, verbose_name=u'金额')
    supplier_name = models.CharField(default="",
                                     blank=True,
                                     max_length=128,
                                     verbose_name=u'商品链接')
    supplier_shop = models.CharField(default="",
                                     blank=True,
                                     max_length=32,
                                     verbose_name=u'供应商店铺名')
    supplier = models.ForeignKey(SaleSupplier,
                                 null=True,
                                 blank=True,
                                 related_name='dinghuo_orderlist',
                                 verbose_name=u'供应商')

    express_company = models.CharField(choices=EXPRESS_CONPANYS,
                                       blank=True,
                                       max_length=32,
                                       verbose_name=u'快递公司')
    express_no = models.CharField(default="",
                                  blank=True,
                                  max_length=32,
                                  verbose_name=u'快递单号')

    receiver = models.CharField(default="", max_length=32, verbose_name=u'负责人')
    costofems = models.IntegerField(default=0, verbose_name=u'快递费用')
    status = models.CharField(max_length=32,
                              db_index=True,
                              verbose_name=u'订货单状态',
                              choices=ORDER_PRODUCT_STATUS)
    pay_status = models.CharField(max_length=32,
                                  db_index=True,
                                  verbose_name=u'收款状态')
    p_district = models.CharField(max_length=32,
                                  default=NEAR,
                                  verbose_name=u'地区',
                                  choices=ORDER_DISTRICT)  # 从发货地对应仓库
    reach_standard = models.BooleanField(default=False, verbose_name=u"达标")
    created = models.DateField(auto_now_add=True,
                               db_index=True,
                               verbose_name=u'订货日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    note = models.TextField(default="", blank=True, verbose_name=u'备注信息')
    created_by = models.SmallIntegerField(
        choices=((CREATED_BY_PERSON, '人工'), (CREATED_BY_MACHINE, '自动')),
        default=CREATED_BY_PERSON,
        verbose_name=u'创建方式')
    last_pay_date = models.DateField(null=True,
                                     blank=True,
                                     verbose_name=u'最后下单日期')
    is_postpay = models.BooleanField(default=False, verbose_name=u'是否后付款')

    class Meta:
        db_table = 'suplychain_flashsale_orderlist'
        app_label = 'dinghuo'
        verbose_name = u'订货表'
        verbose_name_plural = u'订货表'
        permissions = [("change_order_list_inline", u"修改后台订货信息"),]

    def costofems_cash(self):
        return self.costofems / 100.0

    costofems_cash.allow_tags = True
    costofems_cash.short_description = u"快递费用"

    def __unicode__(self):
        return '<%s,%s>' % (str(self.id or ''), self.buyer_name)

    
def check_with_purchase_order(sender, instance, created, **kwargs):
    if not created:
        return
    
    from flashsale.dinghuo.tasks import task_check_with_purchase_order
    task_check_with_purchase_order.delay(instance)

post_save.connect(
    check_with_purchase_order,
    sender=OrderList,
    dispatch_uid='post_save_check_with_purchase_order')

    
class OrderDetail(models.Model):
    id = models.AutoField(primary_key=True)
    orderlist = models.ForeignKey(OrderList,
                                  related_name='order_list',
                                  verbose_name=u'订单编号')
    product_id = models.CharField(db_index=True,
                                  max_length=32,
                                  verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32,
                                db_index=True,
                                verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32,
                                 db_index=True,
                                 verbose_name=u'规格id')
    product_chicun = models.CharField(max_length=100, verbose_name=u'产品尺寸')
    buy_quantity = models.IntegerField(default=0, verbose_name=u'产品数量')
    buy_unitprice = models.FloatField(default=0, verbose_name=u'买入价格')
    total_price = models.FloatField(default=0, verbose_name=u'单项总价')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'正品数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')
    non_arrival_quantity = models.IntegerField(default=0, verbose_name=u'未到数量')

    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True,
                                   verbose_name=u'生成日期')  # index
    updated = models.DateTimeField(auto_now=True,
                                   db_index=True,
                                   verbose_name=u'更新日期')  # index
    arrival_time = models.DateTimeField(blank=True,
                                        null=True,
                                        db_index=True,
                                        verbose_name=u'到货时间')

    class Meta:
        db_table = 'suplychain_flashsale_orderdetail'
        app_label = 'dinghuo'
        verbose_name = u'订货明细表'
        verbose_name_plural = u'订货明细表'
        permissions = [('change_orderdetail_quantity', u'修改订货明细数量')]

    def __unicode__(self):
        return self.product_id

    @property
    def not_arrival_quantity(self):
        """
            未到数量
        :return:
        """
        return self.buy_quantity - self.arrival_quantity - self.inferior_quantity


def update_productskustats_inbound_quantity(sender, instance, created,
                                            **kwargs):
    # Note: chichu_id is actually the id of related ProductSku record.
    from flashsale.dinghuo.tasks import task_orderdetail_update_productskustats_inbound_quantity
    task_orderdetail_update_productskustats_inbound_quantity.delay(
        instance.chichu_id)


post_save.connect(
    update_productskustats_inbound_quantity,
    sender=OrderDetail,
    dispatch_uid='post_save_update_productskustats_inbound_quantity')


class orderdraft(models.Model):
    buyer_name = models.CharField(default="None",
                                  max_length=32,
                                  verbose_name=u'买手')
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_id = models.CharField(max_length=32, verbose_name=u'产品外部编码')
    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    chichu_id = models.CharField(max_length=32, verbose_name=u'规格id')
    product_chicun = models.CharField(default="",
                                      max_length=20,
                                      verbose_name=u'产品尺寸')
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
            total_num = OrderDetail.objects.filter(
                chichu_id=sku_bean.id,
                orderlist__created__range=
                (today - datetime.timedelta(days=7), today)).exclude(
                    orderlist__status=OrderList.ZUOFEI).aggregate(
                        total_num=Sum('arrival_quantity')).get('total_num') or 0
            pro_sku_beans = ProductSkuDetail.objects.get_or_create(
                product_sku=sku_bean.id)
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
    REFUND_RG = 31
    SUCCEED_RG = 4
    FAILED_RG = 5
    MEMO_DEFAULT = u'\u6536\u4ef6\u4eba:\r\n\u624b\u673a/\u7535\u8bdd:\r\n\u6536\u4ef6\u5730\u5740:'
    RG_STATUS = ((CREATE_RG, u"新建"), (VERIFY_RG, u"已审核"), (OBSOLETE_RG, u"已作废"),
                 (DELIVER_RG, u"已发货"), (REFUND_RG, u"待验退款"),
                 (SUCCEED_RG, u"退货成功"), (FAILED_RG, u"退货失败"))
    product_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u"退货商品id")
    # supplier_id = models.IntegerField(db_index=True, verbose_name=u"供应商id")
    supplier = models.ForeignKey(SaleSupplier, null=True, verbose_name=u"供应商")
    return_num = models.IntegerField(default=0, verbose_name=u"退件总数")
    sum_amount = models.FloatField(default=0.0, verbose_name=u"退款总额")
    confirm_pic_url = models.URLField(blank=True, verbose_name=u"付款截图")
    upload_time = models.DateTimeField(null=True, verbose_name=u"上传截图时间")
    refund_fee = models.FloatField(default=0.0, verbose_name=u"客户退款额")
    confirm_refund = models.BooleanField(default=False, verbose_name=u"退款额确认")
    refund_confirmer_id = models.IntegerField(default=None, null=True, verbose_name=u"退款额确认人")
    transactor_id = models.IntegerField(default=None, null=True, db_index=True, verbose_name=u"处理人id")
    # transactor_id = models.IntegerField(choices=[(i.id, i.username) for i in return_goods_transcations()], default=None,
    #                                     null=True, db_index=True, verbose_name=u"处理人id")
    # transactor = models.ForeignKey(User, choices=ReturnGoods.transactors, null=True, verbose_name=u"处理人id")
    transaction_number = models.CharField(default='', max_length=64, verbose_name=u"交易单号")
    noter = models.CharField(max_length=32, verbose_name=u"录入人")
    consigner = models.CharField(max_length=32, blank=True, verbose_name=u"发货人")

    consign_time = models.DateTimeField(blank=True, null=True, verbose_name=u'发货时间')
    sid = models.CharField(max_length=64, null=True, blank=True, verbose_name=u"发货物流单号")
    logistics_company_id = models.BigIntegerField(null=True, verbose_name='物流公司ID')
    # logistics_company = models.ForeignKey(LogisticsCompany, null=True, blank=True, verbose_name=u'物流公司')
    status = models.IntegerField(default=0, choices=RG_STATUS, db_index=True, verbose_name=u"状态")
    REFUND_STATUS = ((0, u"未付"), (1, u"已完成"), (2, u"部分支付"), (3,u"已关闭"))
    refund_status = models.IntegerField(default=0, choices=REFUND_STATUS, db_index=True, verbose_name=u"退款状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=512,
                            blank=True,
                            default=MEMO_DEFAULT,
                            verbose_name=u"退货备注")

    class Meta:
        db_table = 'flashsale_dinghuo_returngoods'
        app_label = 'dinghuo'
        verbose_name = u'仓库退货单'
        verbose_name_plural = u'仓库退货单列表'

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['skuid'] for i in self.rg_details.values('skuid')]
        return self._sku_ids_
    @property
    def product_skus(self):
        if not hasattr(self, '_product_skus_'):
            self._product_skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._product_skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(prod_skus__id__in=self.sku_ids).distinct()
        return self._products_

    @property
    def logistics_company(self):
        if not hasattr(self, '_logistics_company_'):
            from shopback.logistics.models import LogisticsCompany
            self._logistics_company_ = LogisticsCompany.objects.get(id=self.logistics_company_id)
        return self._logistics_company_

    @property
    def transactor(self):
        if not hasattr(self, '_transactor_'):
            self._transactor_ = User.objects.get(id=self.transactor_id)
        return self._transactor_

    def products_item_sku(self):
        products = self.products
        for sku in self.product_skus:
            for product in products:
                if sku.product_id == product.id:
                    if not hasattr(product, 'detail_skus'):
                        product.detail_skus = []
                    product.detail_skus.append(sku)
                    break
                    continue
        for product in products:
            product.detail_sku_ids = [sku.id for sku in product.detail_skus]
            product.detail_length = len(product.detail_sku_ids)
        for detail in self.rg_details.all():
            for product in products:
                if detail.skuid in product.detail_sku_ids:
                    if not hasattr(product, 'detail_items'):
                        product.detail_items = []
                    product.detail_items.append(detail)
        return products

    @staticmethod
    def generate(sku_dict, noter):
        """
            产生sku
        :param sku_dict:
        :param noter:
        :return:
        """
        product_sku_dict = dict([(p.id, p) for p in ProductSku.objects.filter(id__in=sku_dict.keys())])
        supplier = {}
        for sku_id in product_sku_dict:
            if sku_dict[sku_id] > 0:
                sku = product_sku_dict[sku_id]
                detail = RGDetail(
                    skuid=sku_id,
                    num=sku_dict[sku_id],
                    price=sku.cost,
                )
                supplier_id = sku.product.sale_product_item.sale_supplier_id
                if supplier_id not in supplier:
                    supplier[supplier_id] = []
                supplier[supplier_id].append(detail)
        res = []
        for supplier_id in supplier:
            if ReturnGoods.can_return(supplier_id):
                rg_details = supplier[supplier_id]
                rg = ReturnGoods(supplier_id=supplier_id,
                                 noter=noter,
                                 return_num=sum([d.num for d in rg_details]),
                                 sum_amount=sum([d.num * d.price for d in rg_details])
                                 )
                rg.transactor_id = ReturnGoods.get_user_by_supplier(supplier_id)
                rg.save()
                details = []
                for detail in supplier[supplier_id]:
                    detail.return_goods = rg
                    detail.return_goods_id = rg.id
                    details.append(detail)
                RGDetail.objects.bulk_create(details)
                res.append(rg)
        return res

    @staticmethod
    def can_return(supplier_id):
        """
            近七天内没有有效退货单
        :param supplier_id:
        :return:
        """
        return not ReturnGoods.objects.filter(created__gt=datetime.datetime.now()-datetime.timedelta(days=7),
                                          supplier_id=supplier_id, status__in=[ReturnGoods.CREATE_RG, ReturnGoods.VERIFY_RG,
                                                                               ReturnGoods.DELIVER_RG, ReturnGoods.REFUND_RG,
                                                                               ReturnGoods.SUCCEED_RG]).exists()

    @staticmethod
    def get_user_by_supplier(supplier_id):
        r = OrderList.objects.filter(supplier_id=supplier_id).values('buyer_id').annotate(s=Count('buyer_id'))
        def get_max_from_list(l):
            max_i = 0
            buyer_id = None
            for i in l:
                if i['s']>max_i:
                    max_i = i['s']
                    buyer_id = i['buyer_id']
            return buyer_id
        return get_max_from_list(r)

    def set_stat(self):
        rgds = self.rg_details.all()
        total_num = 0
        total_amount = 0
        for rgd in rgds:
            sum_num = rgd.num + rgd.inferior_num
            total_num += sum_num
            total_amount += sum_num * rgd.price
        self.return_num = total_num
        self.sum_amount = total_amount
        self.save()

    def has_sent(self):
        return self.status >= ReturnGoods.DELIVER_RG

    def has_refund(self):
        return self.status in [ReturnGoods.REFUND_RG, ReturnGoods.SUCCEED_RG]

    def set_transactor(self, transactor):
        self.transactor_id = User.objects.get(username=transactor).id
        self.save()

    def delivery_by(self, logistics_no, logistics_company_id, consigner):
        self.sid = logistics_no
        self.logistics_company_id = logistics_company_id
        self.consigner = consigner
        self.consign_time = datetime.datetime.now()
        self.status = ReturnGoods.DELIVER_RG
        self.save()
        for d in self.rg_details.all():
            ProductSku.objects.filter(id=d.skuid).update(quantity=F('quantity')-d.num)

    def supply_notify_refund(self):
        """
            供应商说他已经退款了
        :return:
        """
        self.status = ReturnGoods.REFUND_RG
        self.save()

    def set_confirm_refund_status(self, refund_status=u'已完成'):
        self.refund_status = dict([(r[1], r[0]) for r in ReturnGoods.REFUND_STATUS]).get(refund_status, 0)
        if self.refund_status == 1:
            self.status = ReturnGoods.REFUND_RG
        self.save()

    def set_fail_closed(self):
        self.status = ReturnGoods.FAILED_RG
        self.save()

    @staticmethod
    def transactors():
        return User.objects.filter(is_staff=True,
                                        groups__name__in=(u'小鹿买手资料员', u'小鹿采购管理员', u'小鹿采购员', u'管理员', u'小鹿管理员')). \
                distinct().order_by('id')

    def __unicode__(self):
        return u'<%s,%s>' % (self.supplier_id, self.id)


def update_product_sku_stat_rg_quantity(sender, instance, created, **kwargs):
    from shopback.items.models_stats import PRODUCT_SKU_STATS_COMMIT_TIME
    if instance.created >= PRODUCT_SKU_STATS_COMMIT_TIME and instance.status in [
            ReturnGoods.REFUND_RG, ReturnGoods.DELIVER_RG,
            ReturnGoods.SUCCEED_RG
    ]:
        from flashsale.dinghuo.tasks import task_update_product_sku_stat_rg_quantity
        for rg in instance.rg_details.all():
            task_update_product_sku_stat_rg_quantity.delay(rg.skuid)


post_save.connect(update_product_sku_stat_rg_quantity,
                  sender=ReturnGoods,
                  dispatch_uid='post_save_update_product_sku_stat_rg_quantity')


class RGDetail(models.Model):
    skuid = models.BigIntegerField(db_index=True, verbose_name=u"退货商品skuid")
    return_goods = models.ForeignKey(ReturnGoods,
                                     related_name='rg_details',
                                     verbose_name=u'退货单信息')
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

    @property
    def product_sku(self):
        return ProductSku.objects.get(id=self.skuid)

def sync_rgd_return(sender, instance, created, **kwargs):
    instance.return_goods.set_stat()

post_save.connect(sync_rgd_return, sender=RGDetail, dispatch_uid='post_save_sync_rgd_return')


# class UnReturnList(models.Model):
#     pass

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
    category = models.IntegerField(blank=True,
                                   null=True,
                                   db_index=True,
                                   choices=INVENTORY_CATEGORY,
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
    PENDING = 1
    COMPLETED = 2

    SUPPLIER = 1
    REFUND = 2

    STATUS_CHOICES = ((INVALID, u'作废'), (PENDING, u'待处理'), (COMPLETED, u'完成'))
    supplier = models.ForeignKey(SaleSupplier,
                                 null=True,
                                 blank=True,
                                 related_name='inbounds',
                                 verbose_name=u'供应商')
    express_no = models.CharField(max_length=32,
                                  blank=True,
                                  verbose_name=u'快递单号')
    sent_from = models.SmallIntegerField(
        default=SUPPLIER,
        choices=((SUPPLIER, u'供应商'), (REFUND, u'退货')),
        verbose_name=u'包裹类型')
    refund = models.ForeignKey(Refund,
                               null=True,
                               blank=True,
                               related_name='inbounds',
                               verbose_name=u'退货单')
    creator = models.ForeignKey(User,
                                related_name='inbounds',
                                verbose_name=u'创建人')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(default=PENDING,
                                      choices=STATUS_CHOICES,
                                      verbose_name=u'状态')
    images = JSONCharMyField(max_length=10240,
                             blank=True,
                             default='[]',
                             verbose_name=u'图片')
    orderlist_ids = JSONCharMyField(max_length=10240,
                                    blank=True,
                                    default='[]',
                                    verbose_name=u'订货单ID',
                                    help_text=u'冗余的订货单关联')

    def __unicode__(self):
        return str(self.id)

    def assign_to_order_detail(self, orderlist_id, orderlist_ids):
        return {}
        orderlist_ids = [x for x in orderlist_ids if x != orderlist_id]
        inbound_skus = dict([(inbound_detail.sku_id,
                              inbound_detail.arrival_quantity)
                             for inbound_detail in self.details.all()])
        order_details_first = OrderDetail.objects.filter(
            orderlist_id=orderlist_id,
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = OrderDetail.objects.filter(
            orderlist_id__in=list(orderlist_ids),
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = list(order_details)
        order_details = list(order_details_first) + order_details
        assign_dict = {}
        for order_detail in order_details:
            if order_detail.not_arrival_quantity < inbound_skus.get(
                    order_detail.chichu_id, 0):
                order_detail.arrival_quantity += order_detail.not_arrival_quantity
                inbound_skus[
                    order_detail.chichu_id] -= order_detail.not_arrival_quantity
                assign_dict[order_detail.id] = order_detail.not_arrival_quantity
                # order_detail.save()
            else:
                order_detail.arrival_quantity += inbound_skus.get(
                    order_detail.chichu_id, 0)
                inbound_skus[order_detail.chichu_id] = 0
                assign_dict[order_detail.id] = inbound_skus.get(
                    order_detail.chichu_id, 0)
        return assign_dict

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'


class InBoundDetail(models.Model):
    NORMAL = 1
    PROBLEM = 2

    OUT_ORDERING = 2
    ERR_ORDERING = 3
    ERR_OUT_ORDERING = 4

    inbound = models.ForeignKey(InBound,
                                related_name='details',
                                verbose_name=u'入库单')
    product = models.ForeignKey(Product,
                                null=True,
                                blank=True,
                                related_name='inbound_details',
                                verbose_name=u'入库商品')
    sku = models.ForeignKey(ProductSku,
                            null=True,
                            blank=True,
                            related_name='inbound_details',
                            verbose_name=u'入库规格')

    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'颜色编码')
    properties_name = models.CharField(max_length=128,
                                       blank=True,
                                       verbose_name=u'规格')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'已到数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    status = models.SmallIntegerField(
        default=PROBLEM,
        choices=((NORMAL, u'已分配'), (PROBLEM, u'未分配')),
        verbose_name=u'状态')
    district = models.CharField(max_length=64, blank=True, verbose_name=u'库位')

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

    orderdetail = models.ForeignKey(OrderDetail,
                                    related_name='records',
                                    verbose_name=u'订货明细')
    inbounddetail = models.ForeignKey(InBoundDetail,
                                      related_name='records',
                                      verbose_name=u'入仓明细')
    arrival_quantity = models.IntegerField(default=0,
                                           blank=True,
                                           verbose_name=u'正品数')
    inferior_quantity = models.IntegerField(default=0,
                                            blank=True,
                                            verbose_name=u'次品数')
    status = models.SmallIntegerField(
        default=NORMAL,
        choices=((NORMAL, u'正常'), (INVALID, u'无效')),
        verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'dinghuo_orderdetailinbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓订货明细对照'
        verbose_name_plural = u'入仓订货明细对照列表'


def update_inbound_record(sender, instance, created, **kwargs):
    orderdetail = instance.orderdetail
    orderdetail.arrival_quantity = orderdetail.records.filter(
        status=OrderDetailInBoundDetail.NORMAL).aggregate(
            n=Sum('arrival_quantity')).get('n') or 0
    orderdetail.inferior_quantity = orderdetail.records.filter(
        status=OrderDetailInBoundDetail.NORMAL).aggregate(
            n=Sum('inferior_quantity')).get('n') or 0
    orderdetail.arrival_time = datetime.datetime.now()
    orderdetail.save()
    inbounddetail = instance.inbounddetail
    inbounddetail.arrival_quantity = inbounddetail.records.aggregate(
        n=Sum('arrival_quantity')).get('n') or 0
    inbounddetail.inferior_quantity = inbounddetail.records.aggregate(
        n=Sum('inferior_quantity')).get('n') or 0
    if inbounddetail.arrival_quantity > 0:
        inbounddetail.status = InBoundDetail.NORMAL
    else:
        inbounddetail.status = InBoundDetail.PROBLEM
    inbounddetail.save()


post_save.connect(update_inbound_record,
                  sender=OrderDetailInBoundDetail,
                  dispatch_uid='update_inbound_record')
