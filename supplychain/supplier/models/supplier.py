# -*- coding:utf-8 -*-
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from .managers.supplier import SaleSupplierManager
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES


class SaleSupplier(models.Model):
    CHARGED = 'charged'
    UNCHARGE = 'uncharge'
    FROZEN = 'frozen'
    STATUS_CHOICES = (
        (UNCHARGE, u'待接管'),
        (CHARGED, u'已接管'),
        (FROZEN, u'已冻结'),
    )

    LEVEL_BEST = 100
    LEVEL_BETTER = 80
    LEVEL_GOOD = 60
    LEVEL_NORMAL = 50
    LEVEL_INFERIOR = 0
    LEVEL_CHOICES = (
        (LEVEL_BEST, u'特级'),
        (LEVEL_BETTER, u'一级'),
        (LEVEL_GOOD, u'二级'),
        (LEVEL_NORMAL, u'三级'),
        (LEVEL_INFERIOR, u'四级'),
    )

    MANUAL = 'manual'
    MANUALINPUT = 'manualinput'
    TAOBAO = 'taobao'
    TMALL = 'tianmao'
    ZHEBABAI = 'zhe800'
    XIAOHER = 'xiaoher'
    VIP = 'vip'
    JHS = 'jhs'
    BBW = 'bbw'
    PLATFORM_CHOICE = (
        (MANUAL, u'线上联系'),
        (MANUALINPUT, u'线下厂店'),
        (TAOBAO, u'淘宝'),
        (TMALL, u'天猫'),
        (ZHEBABAI, u'折800'),
        (XIAOHER, u'小荷特卖'),
        (VIP, u'唯品会'),
        (JHS, u'聚划算'),
        (BBW, u'贝贝网'),)

    SELECTED = 'selected'
    PRICING = 'pricing'
    STORAGED = 'storaged'
    PASSED = 'passed'
    IGNORED = 'ignored'
    REJECTED = 'rejected'
    PROGRESS_CHOICES = (
        (SELECTED, u'待接洽'),
        (PRICING, u'锁定价格'),
        (STORAGED, u'锁定库存'),
        (PASSED, u'已签合同'),
        (REJECTED, u'淘汰'),
        (IGNORED, u'忽略'),)
    NO_TYPE = 0
    MANUFACTURER = 1
    WHOLESALER = 2
    BRAND_OWNER = 3
    CLOTHING_FACTORY = 4
    SUPPLIER_TYPE = ((NO_TYPE, u'未分类'),
                     (MANUFACTURER, u'生产加工'),
                     (WHOLESALER, u'经销批发'),
                     (BRAND_OWNER, u'品牌'),
                     (CLOTHING_FACTORY, u'源头大厂'))

    supplier_name = models.CharField(max_length=64, unique=True, db_index=True, blank=False, verbose_name=u'供应商名')
    supplier_code = models.CharField(max_length=64, blank=True, verbose_name=u'品牌缩写')

    description = models.CharField(max_length=1024, blank=True, verbose_name=u'品牌简介')
    brand_url = models.CharField(max_length=512, blank=True, verbose_name=u'商标图片')
    main_page = models.CharField(max_length=256, blank=True, verbose_name=u'品牌主页')
    product_link = models.CharField(max_length=256, blank=True, verbose_name=u'商品链接')

    platform = models.CharField(max_length=16, blank=True, choices=PLATFORM_CHOICE,
                                default=MANUAL, verbose_name=u'来自平台')

    category = models.ForeignKey('supplier.SaleCategory', null=True,
                                 related_name='category_suppliers', verbose_name=u'类别')

    level = models.IntegerField(db_index=True, default=LEVEL_NORMAL,
                                choices=LEVEL_CHOICES, verbose_name=u'等级')
    speciality = models.CharField(max_length=256, blank=True, verbose_name=u'产品特长')
    total_select_num = models.IntegerField(default=0, verbose_name=u'总选款数量')
    total_sale_num = models.FloatField(default=0.0, verbose_name=u'总销售件数')
    total_sale_amount = models.FloatField(default=0.0, verbose_name=u'总销售额')
    total_refund_num = models.IntegerField(default=0, verbose_name=u'总退款件数')
    total_refund_amount = models.FloatField(default=0.0, verbose_name=u'总退款额')
    avg_post_days = models.FloatField(default=0, verbose_name=u'平均发货天数')
    return_goods_limit_days = models.IntegerField(default=20, verbose_name=u'退货截止时间')
    last_select_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'最后选款日期')
    last_schedule_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'最后上架日期')

    contact = models.CharField(max_length=32, blank=False, verbose_name=u'联系人')
    phone = models.CharField(max_length=32, blank=True, verbose_name=u'电话')
    mobile = models.CharField(max_length=16, blank=False, verbose_name=u'手机')
    qq = models.CharField(max_length=32, blank=True, verbose_name=u'QQ号码')
    weixin = models.CharField(max_length=32, blank=True, verbose_name=u'微信号', help_text=u'不要填写微信昵称')
    fax = models.CharField(max_length=16, blank=True, verbose_name=u'传真')
    zip_code = models.CharField(max_length=16, blank=True, verbose_name=u'其它联系')
    email = models.CharField(max_length=64, blank=True, verbose_name=u'邮箱')

    address = models.CharField(max_length=128, blank=False, verbose_name=u'地址')
    account_bank = models.CharField(max_length=32, blank=True, verbose_name=u'汇款银行')
    account_no = models.CharField(max_length=32, blank=True, verbose_name=u'汇款帐号')

    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              db_index=True, default=UNCHARGE, verbose_name=u'状态')

    progress = models.CharField(max_length=16, blank=True, choices=PROGRESS_CHOICES,
                                default=SELECTED, verbose_name=u'进度')
    supplier_type = models.IntegerField(choices=SUPPLIER_TYPE, blank=True, default=0, verbose_name=u"供应商类型")
    supplier_zone = models.IntegerField(default=0, db_index=True, verbose_name=u'供应商所属区域')
    buyer = models.ForeignKey('auth.User', null=True, related_name='buyers', verbose_name=u'买手')
    ware_by = models.SmallIntegerField(default=WARE_SH, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    return_ware_by = models.SmallIntegerField(default=WARE_NONE, choices=WARE_CHOICES, verbose_name=u'退货仓库')

    delta_arrive_days = models.IntegerField(default=3, verbose_name=u'预计到货天数')

    objects = SaleSupplierManager()

    class Meta:
        db_table = 'supplychain_supply_supplier'
        app_label = 'supplier'
        verbose_name = u'特卖/供应商'
        verbose_name_plural = u'特卖/供应商列表'
        permissions = [
            ("sale_supplier_mgr", u"特卖供应商管理"),
        ]

    @staticmethod
    def get_by_id(supplier_id):
        return SaleSupplier.objects.get(id=supplier_id)

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.supplier_name)

    def is_active(self):
        """ 是否有效 """
        return self.status != self.FROZEN and self.progress not in (self.REJECTED, self.IGNORED)

    def get_delta_arrive_days(self):
        return self.delta_arrive_days

    @property
    def charge_buyer(self):
        charge = SupplierCharge.objects.filter(supplier_id=self.id, status=SupplierCharge.EFFECT).first()
        if charge:
            return charge.employee
        return None

    @property
    def buyer_name(self):
        buyer = self.charge_buyer
        if buyer:
            return buyer.username
        return ''

    @classmethod
    def get_default_unrecord_supplier(cls):
        return SaleSupplier.objects.filter(id=1).first()

    @property
    def zone(self):
        if not hasattr(self, '_supplier_zone_'):
            self._supplier_zone_ = SupplierZone.objects.filter(id=self.supplier_zone).first()
        return self._supplier_zone_

    def get_products(self):
        from shopback.items.models import Product
        sale_products = [sp.id for sp in self.supplier_products.all()]
        return Product.objects.filter(sale_product__in=sale_products)


def update_product_ware_by(sender, instance, created, **kwargs):
    """
    update the warehouse receipt status to opened!
    """
    from shopback.items.tasks import task_supplier_update_product_ware_by
    task_supplier_update_product_ware_by.delay(instance)

post_save.connect(update_product_ware_by, sender=SaleSupplier,
                  dispatch_uid='post_save_update_warehouse_receipt_status')



class SupplierCharge(models.Model):
    """ 供应商接管信息表　"""
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT, u'有效'),
        (INVALID, u'失效'),
    )

    supplier_id = models.IntegerField(default=0, verbose_name=u'供应商ID')
    employee = models.ForeignKey('auth.User', related_name='employee_suppliers', verbose_name=u'接管人')

    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              default=EFFECT, verbose_name=u'状态')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_supply_charge'
        unique_together = ("supplier_id", "employee")
        app_label = 'supplier'
        verbose_name = u'特卖/接管商家'
        verbose_name_plural = u'特卖/接管商家列表'

    def __unicode__(self):
        return '<{0},{1},{2}>'.format(self.supplier_id, self.employee, self.get_status_display())


class SupplierZone(models.Model):
    name = models.CharField(max_length=128, unique=True, verbose_name=u'区域名称')

    class Meta:
        db_table = 'supplychain_supply_supplier_zone'
        app_label = 'supplier'
        verbose_name = u'特卖供应商区域表'
        verbose_name_plural = u'特卖供应商区域列表'

    def __unicode__(self):
        return "{0}".format(self.name)

