# -*- coding:utf-8 -*-
import time
from django.db import models
from django.contrib.auth.models import User
from .managers import SaleSupplierManager
from .models_buyer_group import BuyerGroup
from shopback.base.fields import BigIntegerForeignKey


class SaleCategory(models.Model):
    NORMAL = 'normal'
    DELETE = 'delete'

    CAT_STATUS = ((NORMAL, u'正常'),
                  (DELETE, u'删除'))

    name = models.CharField(max_length=64, blank=True, verbose_name=u'类别名')

    parent_cid = models.IntegerField(null=False, db_index=True, verbose_name=u'父类目ID')

    is_parent = models.BooleanField(default=True, verbose_name=u'父类目')
    status = models.CharField(max_length=7, choices=CAT_STATUS, default=NORMAL, verbose_name=u'状态')
    sort_order = models.IntegerField(default=0, verbose_name=u'优先级')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_sale_category'
        verbose_name = u'特卖/选品类目'
        verbose_name_plural = u'特卖/选品类目列表'

    def __unicode__(self):

        if not self.parent_cid:
            return self.name
        try:
            p_cat = self.__class__.objects.get(id=self.parent_cid)
        except:
            p_cat = u'--'
        return '%s / %s' % (p_cat, self.name)

    @property
    def full_name(self):
        return self.__unicode__()


class SaleSupplier(models.Model):
    CHARGED = 'charged'
    UNCHARGE = 'uncharge'
    FROZEN = 'frozen'
    STATUS_CHOICES = (
        (UNCHARGE, u'待接管'),
        (CHARGED, u'已接管'),
        (FROZEN, u'已冻结'),
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

    supplier_name = models.CharField(max_length=64, unique=True, blank=False, verbose_name=u'店铺名称')
    supplier_code = models.CharField(max_length=64, blank=True, verbose_name=u'品牌缩写')

    description = models.CharField(max_length=1024, blank=True, verbose_name=u'品牌简介')
    brand_url = models.CharField(max_length=512, blank=True, verbose_name=u'商标图片')
    main_page = models.CharField(max_length=256, blank=True, verbose_name=u'品牌主页')

    platform = models.CharField(max_length=16, blank=True, choices=PLATFORM_CHOICE,
                                default=MANUAL, verbose_name=u'来自平台')

    category = BigIntegerForeignKey(SaleCategory, null=True,
                                    related_name='category_suppliers', verbose_name=u'类别')

    contact = models.CharField(max_length=32, blank=False, verbose_name=u'联系人')
    phone = models.CharField(max_length=32, blank=True, verbose_name=u'电话')
    mobile = models.CharField(max_length=16, blank=False, verbose_name=u'手机')
    fax = models.CharField(max_length=16, blank=True, verbose_name=u'传真')
    zip_code = models.CharField(max_length=16, blank=True, verbose_name=u'邮编')
    email = models.CharField(max_length=64, blank=True, verbose_name=u'邮箱')

    address = models.CharField(max_length=64, blank=False, verbose_name=u'地址')
    account_bank = models.CharField(max_length=32, blank=True, verbose_name=u'汇款银行')
    account_no = models.CharField(max_length=32, blank=True, verbose_name=u'汇款帐号')

    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              db_index=True, default=UNCHARGE, verbose_name=u'状态')

    progress = models.CharField(max_length=16, blank=True, choices=PROGRESS_CHOICES,
                                default=SELECTED, verbose_name=u'进度')

    objects = SaleSupplierManager()

    class Meta:
        db_table = 'supplychain_supply_supplier'
        verbose_name = u'特卖/供应商'
        verbose_name_plural = u'特卖/供应商列表'
        permissions = [
            ("sale_supplier_mgr", u"特卖供应商管理"),
        ]

    def __unicode__(self):
        return self.supplier_name


class SupplierCharge(models.Model):
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT, u'有效'),
        (INVALID, u'失效'),
    )

    supplier_id = models.IntegerField(default=0, verbose_name=u'供应商ID')
    employee = BigIntegerForeignKey(User,
                                    related_name='employee_suppliers', verbose_name=u'接管人')

    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              default=EFFECT, verbose_name=u'状态')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_supply_charge'
        unique_together = ( "supplier_id", "employee")
        verbose_name = u'特卖/接管商家'
        verbose_name_plural = u'特卖/接管商家列表'

    def __unicode__(self):
        return '<{0},{1},{2}>'.format(self.supplier_id, self.employee, self.get_status_display())


class SaleProduct(models.Model):
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
        (MANUAL, u'手工录入'),
        (MANUALINPUT, u'线下店'),
        (TAOBAO, u'淘宝'),
        (TMALL, u'天猫'),
        (ZHEBABAI, u'折800'),
        (XIAOHER, u'小荷特卖'),
        (VIP, u'唯品会'),
        (JHS, u'聚划算'),
        (BBW, u'贝贝网'),)

    WAIT = 'wait'
    SELECTED = 'selected'
    PURCHASE = 'purchase'
    PASSED = 'passed'
    SCHEDULE = 'scheduling'
    IGNORED = 'ignored'
    REJECTED = 'rejected'
    STATUS_CHOICES = ((WAIT, u'待选'),
                      (SELECTED, u'入围'),
                      (PURCHASE, u'取样'),
                      (PASSED, u'通过'),
                      (SCHEDULE, u'排期'),
                      (REJECTED, u'淘汰'),
                      (IGNORED, u'忽略'),)

    outer_id = models.CharField(max_length=64, blank=True,
                                default=lambda: 'OO%s' % int(time.time() * 10 ** 3),
                                verbose_name=u'外部ID')
    title = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'标题')
    price = models.FloatField(default=0, verbose_name=u'价格')
    pic_url = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    product_link = models.CharField(max_length=512, blank=True, verbose_name=u'商品外部链接')

    sale_supplier = BigIntegerForeignKey(SaleSupplier, null=True, related_name='supplier_products', verbose_name=u'供货商')
    sale_category = BigIntegerForeignKey(SaleCategory, null=True, related_name='category_products', verbose_name=u'类别')
    platform = models.CharField(max_length=16, blank=True, default=MANUAL,
                                choices=PLATFORM_CHOICE, verbose_name=u'来自平台')

    hot_value = models.IntegerField(default=0, verbose_name=u'热度值')
    sale_price = models.FloatField(default=0, verbose_name=u'采购价')
    on_sale_price = models.FloatField(default=0, verbose_name=u'售价')
    std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    product_material = models.CharField(max_length=16, blank=True, verbose_name=u'商品材质')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    is_changed = models.BooleanField(default=False,db_index=True, verbose_name=u'排期改动')
    
    status = models.CharField(max_length=16, blank=True,
                              choices=STATUS_CHOICES, default=WAIT, verbose_name=u'状态')

    contactor = BigIntegerForeignKey(User, null=True, related_name='sale_products', verbose_name=u'接洽人')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    sale_time = models.DateTimeField(null=True, blank=True, verbose_name=u'上架日期')
    reserve_time = models.DateTimeField(null=True, blank=True, verbose_name=u'预留时间')

    class Meta:
        db_table = 'supplychain_supply_product'
        unique_together = ("outer_id", "platform")
        verbose_name = u'特卖/选品'
        verbose_name_plural = u'特卖/选品列表'
        permissions = [
            ("sale_product_mgr", u"特卖商品管理"),
        ]

    def __unicode__(self):
        return self.title
    
from django.db.models.signals import pre_save
from common.modelutils import update_model_fields
def change_saleprodut_by_pre_save(sender, instance, raw, *args, **kwargs):
    try:
        product = SaleProduct.objects.get(id=instance.id)
        #如果上架时间修改，则重置is_verify
        if (product.status == SaleProduct.SCHEDULE and 
            (product.sale_time != instance.sale_time or product.status != instance.status)):
            instance.is_changed = True
            update_model_fields(instance,update_fields=['is_changed'])
    except SaleProduct.DoesNotExist:
        pass
    
pre_save.connect(change_saleprodut_by_pre_save, sender=SaleProduct)


class SaleProductSku(models.Model):
    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'外部ID')

    product_color = models.CharField(max_length=64, blank=True, verbose_name=u'颜色')
    pic_url = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    properties_name = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'规格')
    price = models.FloatField(default=0, verbose_name=u'价格')

    sale_product = models.ForeignKey(SaleProduct, null=True, related_name='product_skus', verbose_name=u'商品规格')
    sale_price = models.FloatField(default=0, verbose_name=u'采购价')
    spot_num = models.IntegerField(default=0, verbose_name=u'现货数量')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_supply_productsku'
        unique_together = ("outer_id", "sale_product")
        verbose_name = u'特卖/选品规格'
        verbose_name_plural = u'特卖/选品规格列表'

    def __unicode__(self):
        return self.properties_name

