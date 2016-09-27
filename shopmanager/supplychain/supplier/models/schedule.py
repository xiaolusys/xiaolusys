# -*- coding:utf-8 -*-
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from core.options import get_systemoa_user, log_action, CHANGE
from core.utils import update_model_fields
from .. import constants
from .product import SaleProduct


class SaleProductManage(models.Model):
    SP_BRAND = constants.SP_BRAND
    SP_TOP = constants.SP_TOP
    SP_TOPIC = constants.SP_TOPIC
    SP_SALE = constants.SP_SALE
    SP_TYPE_CHOICES = (
        (SP_BRAND, u'品牌'),
        (SP_TOP, u'TOP榜'),
        (SP_TOPIC, u'专题'),
        (SP_SALE, u'特卖'),
    )

    schedule_type = models.CharField(max_length=16, default=SP_SALE,
                                     choices=SP_TYPE_CHOICES, db_index=True, verbose_name=u'排期类型')
    sale_suppliers = models.ManyToManyField('supplier.SaleSupplier', blank=True, verbose_name=u'排期供应商')
    sale_time = models.DateField(db_index=True, verbose_name=u'排期日期')
    upshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'上架时间')
    offshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'下架时间')
    product_num = models.IntegerField(default=0, verbose_name=u'商品数量')
    responsible_people_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'负责人ID')
    responsible_person_name = models.CharField(max_length=64, verbose_name=u'负责人名字')
    lock_status = models.BooleanField(default=False, verbose_name=u'锁定')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_supply_schedule_manage'
        app_label = 'supplier'
        verbose_name = u'排期管理'
        verbose_name_plural = u'排期管理列表'

    @property
    def sale_supplier_num(self):
        return self.sale_suppliers.count()

    @property
    def normal_detail(self):
        return self.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL)

    @property
    def nv_detail(self):
        return self.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL,
                                           sale_category__contains=u'女装')

    @property
    def child_detail(self):
        return self.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL,
                                           sale_category__contains=u'童装')

    def __unicode__(self):
        return '<%s,%s>' % (self.sale_time, self.responsible_person_name)

    def save(self, *args, **kwargs):
        detail_count = self.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL).count()
        if self.product_num != detail_count:
            self.product_num = detail_count
        return super(SaleProductManage, self).save(*args, **kwargs)

    def get_sale_product_ids(self):
        if not hasattr(self, '_sale_product_ids_'):
            self._sale_product_ids_ = [i['sale_product_id'] for i in self.manage_schedule.values('sale_product_id')]
        return self._sale_product_ids_

    def resort_schedule(self):
        """
        功能: 重新按照　排期明细的　权重字段排序
        """
        details = self.manage_schedule.all().order_by('order_weight')
        count = 1
        for detail in details:
            detail.order_weight = count
            detail.save(update_fields=['order_weight'])
            count += 1
        return

    def clean_deleted_supplier_manager_details(self):
        """
        功能：　清理删除了的供应商的排期明细
        """
        current_sale_product_ids = [c['sale_product_id'] for c in self.manage_schedule.values('sale_product_id')]
        sale_supplier_ids = [supplier.id for supplier in self.sale_suppliers.all()]
        target_sale_product_ids = [x['id'] for x in
                                   SaleProduct.objects.filter(id__in=current_sale_product_ids,
                                                              sale_supplier_id__in=sale_supplier_ids).values('id')]
        will_delete_sale_product_ids = [i for i in current_sale_product_ids if i not in target_sale_product_ids]
        if will_delete_sale_product_ids:
            self.manage_schedule.filter(sale_product_id__in=will_delete_sale_product_ids).delete()
            self.save()  # 同步产品数量
            self.resort_schedule()  # 重新排序
            return True
        return False


def update_model_product_shelf_time(sender, instance, raw, *args, **kwargs):
    from flashsale.pay.models import ModelProduct

    if not instance.lock_status:  # do not sync shelf time and schedule type if this instance not locked
        return
    action_user = get_systemoa_user()
    sale_product_ids = instance.manage_schedule.values('sale_product_id')
    is_topic = False if instance.schedule_type == SaleProductManage.SP_SALE else True
    ModelProduct.update_schedule_manager_info(action_user,
                                              sale_product_ids,
                                              instance.upshelf_time,
                                              instance.offshelf_time,
                                              is_topic)


post_save.connect(update_model_product_shelf_time,
                  sender=SaleProductManage,
                  dispatch_uid=u'post_save_update_model_product_shelf_time')


class SaleProductManageDetail(models.Model):
    COMPLETE = u'complete'
    WORKING = u'working'
    NORMAL = u'normal'
    DELETE = u'delete'
    use = u'working'
    TAKEOVER = u'takeover'
    NOTTAKEOVER = u'nottakeover'
    MATERIAL_STATUS = (
        (COMPLETE, u'全部完成'),
        (WORKING, u'进行中')
    )
    USE_STATUS = (
        (NORMAL, u'使用'),
        (DELETE, u'作废')
    )
    DESIGN_TAKE_STATUS = (
        (TAKEOVER, u'接管'),
        (NOTTAKEOVER, u'未接管')
    )
    SP_BRAND = constants.SP_BRAND
    SP_TOP = constants.SP_TOP
    SP_TOPIC = constants.SP_TOPIC
    SP_SALE = constants.SP_SALE
    SP_TYPE_CHOICES = (
        (SP_BRAND, u'品牌'),
        (SP_TOP, u'TOP榜'),
        (SP_TOPIC, u'专题'),
        (SP_SALE, u'特卖'),
    )

    WEIGHT_CHOICE = ((i, i) for i in range(1, 101)[::-1])

    schedule_type = models.CharField(max_length=16, default=SP_SALE,
                                     choices=SP_TYPE_CHOICES, db_index=True, verbose_name=u'排期类型')
    schedule_manage = models.ForeignKey(SaleProductManage, related_name='manage_schedule', verbose_name=u'排期管理')
    sale_product_id = models.BigIntegerField(default=0, verbose_name=u"选品ID")
    name = models.CharField(max_length=64, verbose_name=u'选品名称')
    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    sale_category = models.CharField(max_length=32, blank=True, verbose_name=u'商品分类')
    product_link = models.CharField(max_length=512, blank=True, verbose_name=u'商品外部链接')
    material_status = models.CharField(max_length=64, blank=True, default=WORKING, choices=MATERIAL_STATUS,
                                       verbose_name=u"资料状态")
    design_take_over = models.CharField(max_length=32, blank=True, default=NOTTAKEOVER, choices=DESIGN_TAKE_STATUS,
                                        verbose_name=u"平面资料接管状态")
    today_use_status = models.CharField(max_length=64, db_index=True, default=NORMAL, choices=USE_STATUS,
                                        verbose_name=u"使用状态")
    design_person = models.CharField(max_length=32, blank=True, verbose_name=u'设计负责人')
    design_complete = models.BooleanField(default=False, verbose_name=u'设计完成')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    pic_rating = models.FloatField(blank=True, null=True, verbose_name=u'作图评分')
    is_approved = models.SmallIntegerField(default=0, verbose_name=u'审核通过')
    is_promotion = models.BooleanField(default=False, verbose_name=u'推广商品')
    reference_user = models.BigIntegerField(default=0, db_index=True, verbose_name=u"资料录入人")
    photo_user = models.BigIntegerField(default=0, db_index=True, verbose_name=u"平面制作人")
    order_weight = models.IntegerField(db_index=True, default=8, choices=WEIGHT_CHOICE, verbose_name=u'权值')

    class Meta:
        db_table = 'supplychain_supply_schedule_manage_detail'
        unique_together = ("schedule_manage", "sale_product_id")
        app_label = 'supplier'
        verbose_name = u'排期管理明细'
        verbose_name_plural = u'排期管理明细列表'
        permissions = [
            ("revert_done", u"反完成"),
            ('pic_rating', u'作图评分'),
            ('add_product', u'加入库存商品'),
            ('eliminate_product', u'淘汰排期商品'),
            ('reset_head_img', u'重置头图'),
            ('delete_schedule_detail', u'删除排期明细记录'),
            ('distribute_schedule_detail', u'排期管理任务分配'),
        ]

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.sale_product_id)

    @property
    def status(self):
        return self.today_use_status

    @property
    def status_name(self):
        return self.get_today_use_status_display()

    @property
    def sale_product(self):
        if not hasattr(self, '_sale_product_'):
            self._sale_product_ = SaleProduct.objects.filter(id=self.sale_product_id).first()
        return self._sale_product_

    @property
    def item_products(self):
        if not hasattr(self, '_item_products_'):
            from shopback.items.models import Product

            self._item_products_ = Product.objects.filter(sale_product=self.sale_product_id, status=Product.NORMAL)
        return self._item_products_

    @property
    def product_model_id(self):
        if not hasattr(self, '_model_id_'):
            self._model_id_ = self.item_products.first()
        return self._model_id_.model_id if self._model_id_ else 0

    @property
    def sale_memo(self):
        if self.sale_product:
            return self.sale_product.memo
        return u""

    @property
    def std_purchase_price(self):
        if self.sale_product:
            return self.sale_product.sale_price
        return 0.0

    @property
    def pic_rating_memos(self):
        return self._pic_rating_memos.all().order_by('created')

    @property
    def is_top_type(self):
        return self.schedule_type == self.SP_TOP

    @property
    def is_brand_type(self):
        return self.schedule_type == self.SP_BRAND

    @property
    def modelproducts(self):
        if not hasattr(self, '_model_products_'):
            from flashsale.pay.models import ModelProduct
            self._model_products_ = ModelProduct.objects.filter(saleproduct_id=self.sale_product_id)
        return self._model_products_

    @property
    def nomal_modelproducts(self):
        """ 正常状态的款式 """
        from flashsale.pay.models import ModelProduct
        return self.modelproducts.filter(status=ModelProduct.NORMAL)

    @property
    def modeproduct(self):
        return self.nomal_modelproducts.first()


def sync_md_weight(sender, instance, raw, *args, **kwargs):
    """
    sync ModelProduct order_weight
    """
    from flashsale.pay.models import ModelProduct

    md = ModelProduct.objects.filter(saleproduct=instance.sale_product_id).first()
    if not md:
        return
    md.update_schedule_detail_info(instance.order_weight)


post_save.connect(sync_md_weight, SaleProductManageDetail,
                  dispatch_uid='post_save_sync_md_weight')


def update_saleproduct_supplier(sender, instance, **kwargs):
    """
        如果选品录入，则更新供应商品最后选品日期,最后上架日期
    """

    if sender == SaleProduct:
        sale_supplier = instance.sale_supplier
        if (not sale_supplier or (sale_supplier.last_select_time and
                                          instance.created < sale_supplier.last_select_time)):
            return
        sale_supplier.last_select_time = instance.created
        update_model_fields(sale_supplier, update_fields=['last_select_time'])
    elif sender == SaleProductManageDetail:
        sale_products = SaleProduct.objects.filter(id=instance.sale_product_id)
        if not sale_products.exists():
            return
        sale_supplier = sale_products[0].sale_supplier
        sale_manage = instance.schedule_manage
        if (not sale_supplier or (sale_supplier.last_schedule_time and
                                          sale_manage.sale_time < sale_supplier.last_schedule_time.date())):
            return
        sale_supplier.last_schedule_time = sale_manage.sale_time
        update_model_fields(sale_supplier, update_fields=['last_schedule_time'])


post_save.connect(update_saleproduct_supplier, SaleProduct,
                  dispatch_uid='post_save_product_update_saleproduct_supplier')

post_save.connect(update_saleproduct_supplier, SaleProductManageDetail,
                  dispatch_uid='post_save_manage_update_saleproduct_supplier')


def sync_product_detail_count(sender, instance, raw, *args, **kwargs):
    """ 同步：　Productdetail　的　数量　字段
    """
    manager = instance.schedule_manage
    detail_count = manager.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL)
    if manager.product_num != detail_count:
        manager.product_num = detail_count
        manager.save(update_fields=['product_num'])


post_save.connect(sync_product_detail_count, SaleProductManageDetail,
                  dispatch_uid='post_save_sync_product_detail_count')


def sync_model_product_delete(sender, instance, *args, **kwargs):
    """
    当删除排期中的明细的时候　需要将　对应ModelProduct的上下架时间置为 None
    防止录入资料后有排期明细的改动　导致　按照日期的错误上架
    """
    # 对应上架时间的款式
    modelproducts = instance.modelproducts.filter(onshelf_time=instance.schedule_manage.upshelf_time)
    for modelproduct in modelproducts:
        modelproduct.set_shelftime_none()


post_delete.connect(sync_model_product_delete, SaleProductManageDetail,
                    dispatch_uid=u'post_delete_sync_model_product_delete')


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
        app_label = 'supplier'
        verbose_name = u'特卖/选品规格'
        verbose_name_plural = u'特卖/选品规格列表'

    def __unicode__(self):
        return self.properties_name


class SaleProductPicRatingMemo(models.Model):
    schedule_detail = models.ForeignKey(SaleProductManageDetail, related_name='_pic_rating_memos',
                                        verbose_name=u'作图评分备注')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注', default='[]')
    user = models.ForeignKey('auth.User', related_name='pic_rating_admin', verbose_name=u'评分人')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    def __unicode__(self):
        return '%s: %s [%s]' % (self.user.username, self.memo)

    class Meta:
        db_table = 'supplychain_supply_schedule_pic_rating_memo'
        app_label = 'supplier'
        verbose_name = u'排期作图评分'
        verbose_name_plural = u'排期作图评分'
