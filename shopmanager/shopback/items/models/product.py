# coding: utf-8

import collections
import datetime
import json
import urlparse
import re
import hashlib

from django.db import models
from django.db.models import Sum, Avg, F
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.forms.models import model_to_dict
from django.core.cache import cache

from auth import apis
from common.modelutils import update_model_fields
from core.models import AdminModel
from flashsale.restpro.local_cache import image_watermark_cache

from shopback import paramconfig as pcfg
from shopback.categorys.models import Category, ProductCategory
from shopback.archives.models import Deposite, DepositeDistrict
from shopback.users.models import DjangoUser, User
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES

from supplychain.supplier.models import SaleProduct

from .. import constants, managers

import logging
logger = logging.getLogger(__name__)


class ProductDefectException(Exception):
    pass


class ProductStock(object):
    @staticmethod
    def add_order_detail(orderdetail, num):
        Product.objects.filter(id=orderdetail.product_id).update(collect_num=F('collect_num') + num)
        # ProductSku.objects.filter(id=orderdetail.chichu_id).update(quantity=F('quantity') + num)
        product_sku = ProductSku.objects.get(id=orderdetail.chichu_id)
        product_sku.quantity += num
        product_sku.save()
        from flashsale.dinghuo.models import OrderDetail
        OrderDetail.objects.get(id=orderdetail.id).save()
        # p = ProductSku.objects.get(id=orderdetail.chichu_id)
        # p.quantity =


class Product(models.Model):
    """ 记录库存属性及加上排期信息的商品类 """

    class Meta:
        db_table = 'shop_items_product'
        app_label = 'items'
        verbose_name = u'库存商品'
        verbose_name_plural = u'库存商品列表'
        permissions = [
            ("change_product_skunum", u"修改库存信息"),
            ("change_product_shelf", u"特卖商品上架/下架"),
            ("sync_product_stock", u"商品库存同步/取消"),
            ("regular_product_order", u"商品订单定时/释放"),
            ("create_product_purchase", u"创建商品订货单"),
            ("export_product_info", u"导出库存商品信息"),
            ("invalid_product_info", u"作废库存商品信息")
        ]

    objects = managers.ProductManager()
    cache_enabled = True

    NORMAL = pcfg.NORMAL
    REMAIN = pcfg.REMAIN
    DELETE = pcfg.DELETE
    STATUS_CHOICES = (
        (pcfg.NORMAL, u'使用'),
        (pcfg.REMAIN, u'待用'),
        (pcfg.DELETE, u'作废'),
    )

    UP_SHELF = 1
    DOWN_SHELF = 0
    SHELF_CHOICES = ((UP_SHELF, u'已上架'),
                     (DOWN_SHELF, u'未上架'))

    ProductCodeDefect = ProductDefectException
    DIPOSITE_CODE_PREFIX = 'RMB'  # 押金商品编码前缀
    PRODUCT_CODE_DELIMITER = '.'
    MALL_PRODUCT_TEMPLATE_URL = constants.MALL_PRODUCT_TEMPLATE_URL
    NO_PIC_PATH = '/static/img/nopic.jpg'

    outer_id = models.CharField(max_length=32, unique=True, null=False,
                                blank=True, verbose_name=u'外部编码')
    name = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'商品名称')
    model_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品款式ID')

    barcode = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'条码')
    category = models.ForeignKey(ProductCategory, null=True, blank=True,
                                 related_name='products', verbose_name=u'内部分类')
    pic_path = models.CharField(max_length=256, blank=True, verbose_name=u'商品主图')

    collect_num = models.IntegerField(default=0, verbose_name=u'库存数')  # 库存数
    warn_num = models.IntegerField(default=0, verbose_name=u'警告数')  # 警戒库位
    remain_num = models.IntegerField(default=0, verbose_name=u'预留数')  # 预留库存
    wait_post_num = models.IntegerField(default=0, verbose_name=u'待发数')  # 待发数
    sale_num = models.IntegerField(default=0, verbose_name=u'日出库数')  # 日出库
    reduce_num = models.IntegerField(default=0, verbose_name=u'预减数')  # 下次入库减掉这部分库存
    lock_num = models.IntegerField(default=0, verbose_name=u'锁定数')  # 特卖待发货，待付款数量
    inferior_num = models.IntegerField(default=0, verbose_name=u"次品数")  # 保存对应sku的次品数量

    cost = models.FloatField(default=0, verbose_name=u'成本价')
    std_purchase_price = models.FloatField(default=0, verbose_name=u'标准进价')
    std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    agent_price = models.FloatField(default=0, verbose_name=u'出售价')
    staff_price = models.FloatField(default=0, verbose_name=u'员工价')

    weight = models.CharField(max_length=10, blank=True, verbose_name=u'重量(g)')
    created = models.DateTimeField(null=True, blank=True,
                                   auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(null=True, blank=True, db_index=True,
                                    auto_now=True, verbose_name=u'修改时间')
    sale_time = models.DateField(null=True, blank=True, db_index=True, verbose_name=u'上架日期')
    upshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'上架时间')
    offshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'下架时间')

    is_split = models.BooleanField(default=False, verbose_name=u'需拆分')
    is_match = models.BooleanField(default=False, verbose_name=u'有匹配')
    sync_stock = models.BooleanField(default=True, verbose_name=u'库存同步')
    is_assign = models.BooleanField(default=False, verbose_name=u'取消警告')
    post_check = models.BooleanField(default=False, verbose_name=u'需扫描')
    is_flatten = models.BooleanField(default=False, db_index=True, verbose_name=u'平铺显示')
    is_watermark = models.BooleanField(default=False, verbose_name=u'图片水印')
    status = models.CharField(max_length=16, db_index=True,
                              choices=STATUS_CHOICES,
                              default=pcfg.NORMAL, verbose_name=u'商品状态')

    match_reason = models.CharField(max_length=80, blank=True, verbose_name=u'匹配原因')
    buyer_prompt = models.CharField(max_length=60, blank=True, verbose_name=u'客户提示')
    memo = models.TextField(max_length=1000, blank=True, verbose_name=u'备注')

    sale_charger = models.CharField(max_length=32, db_index=True, blank=True,
                                    verbose_name=u'归属采购员')
    storage_charger = models.CharField(max_length=32, db_index=True, blank=True,
                                       verbose_name=u'归属仓管员')
    sale_product = models.BigIntegerField(db_index=True, default=0, verbose_name=u'选品ID')
    is_verify = models.BooleanField(default=False, verbose_name=u'是否校对')
    shelf_status = models.IntegerField(choices=SHELF_CHOICES, db_index=True,
                                       default=DOWN_SHELF, verbose_name=u'上架状态')
    ware_by = models.IntegerField(default=WARE_SH, choices=WARE_CHOICES,
                                  db_index=True, verbose_name=u'所属仓库')

    def __unicode__(self):
        return '%s' % self.id
        # return '<%s,%s>'%(self.outer_id,self.name)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    def save(self, *args, **kwargs):
        # 设置商品下架时间，默认时两天后下架
        if not self.offshelf_time and self.sale_time:
            if isinstance(self.sale_time, basestring):
                sale_time = datetime.datetime.strptime(self.sale_time, '%Y-%m-%d')
            else:
                sale_time = datetime.datetime.combine(self.sale_time, datetime.time.min)
            self.offshelf_time = sale_time + datetime.timedelta(days=2)
        if isinstance(self.upshelf_time, datetime.datetime):
            if self.sale_time != self.upshelf_time.date():
                self.sale_time = self.upshelf_time.date()
        return super(Product, self).save(*args, **kwargs)

    def get_product_model(self):
        """ 获取商品款式 """
        if self.model_id == 0:
            return None
        if not hasattr(self, '_model_product_'):
            from flashsale.pay.models import ModelProduct

            self._model_product_ = ModelProduct.objects.filter(id=self.model_id).first()
        return self._model_product_

    product_model = property(get_product_model)

    def get_product_detail(self):
        try:
            return self.details
        except:
            return None

    detail = product_detail = property(get_product_detail)

    @property
    def sale_group(self):
        from flashsale.dinghuo.models_user import MyUser
        myuser = MyUser.objects.filter(user__username=self.sale_charger)
        return myuser[0].group if myuser.count() > 0 else "None"

    @property
    def eskus(self):
        return self.prod_skus.filter(status=pcfg.NORMAL)

    @property
    def normal_skus(self):
        return self.eskus

    @property
    def pskus(self):
        return self.prod_skus.filter(status__in=(pcfg.NORMAL, pcfg.REMAIN))

    @property
    def BARCODE(self):
        return self.barcode.strip() or self.outer_id.strip()

    @property
    def realnum(self):
        if self.collect_num >= self.sale_num:
            return self.collect_num - self.sale_num
        return 0

    @property
    def sale_out(self):
        sale_out = True
        for sku in self.pskus:
            sale_out &= sku.sale_out
        return sale_out

    def get_product_link(self):
        return SaleProduct.objects.get(id=self.sale_product).product_link

    def has_quantity(self):
        return self.collect_num > 0

    def sale_open(self):
        """ 返回特卖商品是否开售 """
        return self.shelf_status == self.UP_SHELF

    def new_good(self):
        """ 返回特卖商品是否即将开售 """
        return self.sale_time and self.sale_time >= datetime.date.today()

    def is_sale_out(self):
        return self.sale_out

    def is_deposite(self):
        return self.outer_id.startswith(Product.DIPOSITE_CODE_PREFIX)

    def is_onshelf(self):
        return self.shelf_status == self.UP_SHELF

    @property
    def sale_product_item(self):
        return SaleProduct.objects.filter(id=self.sale_product).first()

    @property
    def is_out_stock(self):
        if self.collect_num < 0 or self.wait_post_num < 0:
            self.collect_num = self.collect_num > 0 and self.collect_num or 0
            self.wait_post_num = self.wait_post_num > 0 and self.wait_post_num or 0
            self.save()
        return self.collect_num - self.wait_post_num <= 0

    @property
    def PIC_PATH(self):
        return self.pic_path.strip() or self.NO_PIC_PATH

    @property
    def thumbnail(self):
        url = self.pic_path.strip()
        if url:
            return '%s?%s' % (url, 'imageMogr2/thumbnail/289/format/jpg/quality/90')
        else:
            return self.NO_PIC_PATH

    @property
    def watermark_op(self):
        if not self.is_watermark:
            return ''
        return image_watermark_cache.latest_qs or ''

    def get_weburl(self):
        return urlparse.urljoin(settings.M_SITE_URL,
                                self.MALL_PRODUCT_TEMPLATE_URL.format(self.model_id))

    def head_img(self):
        """ 获取商品款式 """
        if self.model_id == 0:
            self.model_id = None
        from flashsale.pay.models import ModelProduct
        try:
            pmodel = ModelProduct.objects.get(id=self.model_id)
        except:
            try:
                return self.details.head_imgs.split()[0]
            except:
                return self.PIC_PATH
        return pmodel and pmodel.head_imgs.split()[0] or self.PIC_PATH

    head_img_url = property(head_img)

    @property
    def json(self):
        skus_json = []
        for sku in self.pskus:
            skus_json.append(sku.json)
        model_dict = model_to_dict(self)
        model_dict.update({'category': self.category or {},
                           'status': self.get_status_display(),
                           'districts': self.get_district_list(),
                           'barcode': self.BARCODE,
                           'skus': skus_json
                           })
        return model_dict

    def title(self):
        return self.name

    @property
    def property_name(self):
        keys = self.name.split('/')
        return len(keys) > 1 and keys[1] or keys[0]

    @property
    def stats(self):
        return self.productskustats_set.all()

    @property
    def realtime_quantity(self):
        return sum(self.productskustats_set.all().values_list('realtime_quantity', flat=True))

    def pro_sale_supplier(self):
        """ 返回产品的选品和供应商　"""
        try:
            sal_p = SaleProduct.objects.get(pk=self.sale_product)
            supplier = sal_p.sale_supplier
            return sal_p, supplier
        except SaleProduct.DoesNotExist:
            return None, None

    def get_supplier_contactor(self):
        sal_p, supplier = self.pro_sale_supplier()
        if sal_p is not None:
            if sal_p.contactor.first_name and sal_p.contactor.last_name:
                return sal_p.contactor.last_name + sal_p.contactor.first_name
            return sal_p.contactor  # 返回接洽人
        else:
            return self.sale_charger + "未关联"

    def get_sale_product(self):
        """ 返回产品的选品"""
        try:
            return SaleProduct.objects.get(pk=self.sale_product)
        except SaleProduct.DoesNotExist:
            return None

    def get_supplier(self):
        sp = SaleProduct.objects.filter(id=self.sale_product).first()
        if sp:
            return sp.sale_supplier

    @staticmethod
    def get_by_supplier(supplier_id):
        sale_procuct_ids = [s['id'] for s in SaleProduct.objects.filter(sale_supplier_id=supplier_id).values("id")]
        return Product.objects.filter(sale_product__in=sale_procuct_ids).exclude(status=pcfg.DELETE)

    def update_collect_num(self, num, full_update=False, dec_update=False):
        """
            更新商品库存:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.collect_num = num
        elif dec_update:
            self.collect_num = F('collect_num') - num
        else:
            self.collect_num = F('collect_num') + num
        update_model_fields(self, update_fields=['collect_num'])

        self.collect_num = self.__class__.objects.get(id=self.id).collect_num

    def update_wait_post_num(self, num, full_update=False, dec_update=False):
        """
            更新商品待发数:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = F('wait_post_num') - num
        else:
            self.wait_post_num = F('wait_post_num') + num
        update_model_fields(self, update_fields=['wait_post_num'])

        self.wait_post_num = self.__class__.objects.get(id=self.id).wait_post_num

    def update_reduce_num(self, num, full_update=False, dec_update=False):
        """
            更新商品库存:
                full_update:是否全量更新
                dec_update:是否减库存
        """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self, update_fields=['reduce_num'])

        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num

    def update_quantity_by_storage_num(self, num):

        if num < 0:
            raise Exception(u'入库更新商品库存数不能小于0')

        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num

        self.update_collect_num(real_update_num)
        self.update_reduce_num(real_reduct_num, full_update=True)

    @property
    def is_stock_warn(self):
        """
        库存是否警告
        """
        for sku in self.eskus:
            if sku.is_stock_warn and not sku.is_assign:
                return True

        collect_num = self.collect_num > 0 and self.collect_num or 0
        remain_num = self.remain_num > 0 and self.remain_num or 0
        wait_post_num = self.wait_post_num > 0 and self.wait_post_num or 0

        sync_num = collect_num - remain_num - wait_post_num
        return sync_num <= 0

    @property
    def is_warning(self):
        """
        库存预警,昨天的销售大今天能同步的库存
        """
        for sku in self.eskus:
            if sku.is_warning:
                return True

        collect_num = self.collect_num > 0 and self.collect_num or 0
        remain_num = self.remain_num > 0 and self.remain_num or 0
        wait_post_num = self.wait_post_num > 0 and self.wait_post_num or 0
        sync_num = collect_num - remain_num - wait_post_num
        return self.warn_num > 0 and self.warn_num >= sync_num

    def get_district_list(self):
        from .storage import ProductLocation
        locations = ProductLocation.objects.filter(product_id=self.id)
        return list(set([(l.district.parent_no, l.district.district_no) for l in locations]))

    def get_district_info(self):
        if not hasattr(self, '_district_info_'):
            from .storage import ProductLocation
            locations = ProductLocation.objects.filter(product_id=self.id).values('district').distinct()
            district_ids = [i['district'] for i in locations]
            if district_ids:
                deposites = DepositeDistrict.objects.filter(id__in=district_ids)
                self._district_info_ = ','.join([str(d) for d in deposites])
            else:
                self._district_info_ = ''
        return self._district_info_

    def get_districts_code(self):
        """ 商品库中区位 """
        locations = self.get_district_list()

        sdict = {}
        for d in locations:
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])

        dc_list = sorted(sdict.items(), key=lambda d: d[0])
        ds = []
        for k, v in dc_list:
            ds.append(len(v) > 1 and '%s-[%s]' % (k, ','.join(list(v))) or '%s-%s' % (k, v.pop()))

        return ','.join(ds)

    def lowest_price(self):
        """同款最低价格"""
        prcs = []
        if self.model_id == 0 or self.model_id == None:
            skus = self.normal_skus.all()
        else:
            skus = ProductSku.objects.filter(product__model_id=self.model_id,
                                             product__status=Product.NORMAL,
                                             status=ProductSku.NORMAL)
        for sku in skus:
            prcs.append(sku.agent_price)
        return min(prcs) if prcs else 0

    def product_lowest_price(self):
        """同个商品最低价格"""
        prcs = []
        skus = self.normal_skus.all()
        for sku in skus:
            prcs.append(sku.agent_price)
        return min(prcs) if prcs else 0

    def calc_discount_fee(self, xlmm=None):
        """ 优惠折扣 """
        if not xlmm or xlmm.agencylevel < 2:
            return 0

        try:
            discount = int(self.product.details.mama_discount)
            if discount > 100:
                discount = 100

            if discount < 0:
                discount = 0
            return float('%.2f' % ((100 - discount) / 100.0 * float(self.agent_price)))
        except:
            return 0

    def same_model_pros(self):
        """ 同款产品　"""
        if self.model_id == 0 or self.model_id is None:
            return None
        pros = self.__class__.objects.filter(model_id=self.model_id)
        return pros

    def in_customer_shop(self, customer):
        """在用户我的店铺中有本产品则返回true否则返回false"""
        from flashsale.pay.models import CuShopPros, CustomerShops
        try:
            customer_shop = CustomerShops.objects.get(customer=customer)
            cps = CuShopPros.objects.filter(product=self.id, shop=customer_shop.id)
            if cps.exists():
                return cps[0].pro_status
            return 0
        except:
            return 0

    def shop_product_num(self):
        """
        bypass ProductSimpleSerializer check
        """
        return None

    def rebet_amount(self):
        """
        bypass ProductSimpleSerializer check
        """
        return None

    def sale_num_des(self):
        """
        bypass ProductSimpleSerializer check
        """
        return None

    def rebet_amount_des(self):
        """
        bypass ProductSimpleSerializer check
        """
        return None

    @classmethod
    def items_by_sale_product_id(cls, sale_product_id):
        """ 选品id对应的产品 """
        return cls.objects.filter(sale_product=sale_product_id, status=cls.NORMAL)

    @classmethod
    def upshelf_right_now_products(cls):
        """需要立即上架的产品"""
        now = datetime.datetime.now()  # 现在时间在上架时间和下架时间之间　状态为正常 处于下架状态 并且审核通过的产品
        return cls.objects.filter(
            upshelf_time__lte=now, offshelf_time__gt=now,
            status=cls.NORMAL,
            # is_verify=True,
            shelf_status=cls.DOWN_SHELF,
            upshelf_time__isnull=False,
            offshelf_time__isnull=False)

    @classmethod
    def offshelf_right_now_products(cls):
        now = datetime.datetime.now()  # 下架时间小于现在（在这之前就应该下架）　　状态正常　且处于　上架状态　的　产品
        return cls.objects.filter(
            offshelf_time__lte=now,
            status=cls.NORMAL,
            shelf_status=cls.UP_SHELF
        )

    def upshelf_product(self):
        """ 上架产品 """
        # if not self.is_verify:
        #     return False
        if self.shelf_status != Product.UP_SHELF:
            self.shelf_status = Product.UP_SHELF
            self.save(update_fields=['shelf_status'])
            return True
        return False

    def offshelf_product(self):
        """ 下架产品 """
        update_fields = []
        if self.shelf_status != Product.DOWN_SHELF:
            self.shelf_status = Product.DOWN_SHELF
            update_fields.append('shelf_status')
        if self.is_verify:  # 下架过程要将审核重置为未审核
            self.is_verify = False
            update_fields.append('is_verify')
        if update_fields:
            self.save(update_fields=update_fields)
            return True
        return False

    def update_shelf_time(self, upshelf_time, offshelf_time):
        """ 更新上下架时间 """
        if self.shelf_status == Product.UP_SHELF:  # 正在上架的产品不去　更新　上下架时间
            return False
        update_fields = []
        if not (upshelf_time and offshelf_time):
            return
        if self.upshelf_time != upshelf_time:
            self.upshelf_time = upshelf_time
            update_fields.append('upshelf_time')
        if self.sale_time != upshelf_time.date():
            self.sale_time = upshelf_time.date()
            update_fields.append('sale_time')
        if self.offshelf_time != offshelf_time:
            self.offshelf_time = offshelf_time
            update_fields.append('offshelf_time')
        if update_fields:
            self.save(update_fields=update_fields)
            return True

    def set_remain_num(self):
        """ 设置预留数:sku 预留数的总和 """
        remain_nums = self.normal_skus.values('remain_num')
        total_remain_num = sum([i['remain_num'] for i in remain_nums])
        if self.remain_num != total_remain_num:
            self.remain_num = total_remain_num
            self.save(update_fields=['remain_num'])
            return True
        return False

    def set_price(self):
        """ 设置: 成本 吊牌价 售价 """
        prices = self.normal_skus.values('cost', 'std_sale_price', 'agent_price')
        count = len(prices)
        if count <= 0:
            self.cost = 0
            self.std_sale_price = 0
            self.agent_price = 0
            self.save(update_fields=['cost', 'std_sale_price', 'agent_price'])
            return
        self.cost = round(sum([i['cost'] for i in prices]) / count, 2)
        self.std_sale_price = round(sum([i['std_sale_price'] for i in prices]) / count, 2)
        self.agent_price = round(sum([i['agent_price'] for i in prices]) / count, 2)
        self.save(update_fields=['cost', 'std_sale_price', 'agent_price'])

    def update_name(self, name):
        if self.name != name and name.strip():
            self.name = name
            self.save(update_fields=['name'])


def delete_pro_record_supplier(sender, instance, created, **kwargs):
    """ 当作废产品的时候　检查　同款是否 全部  作废　如果是　则　将对应供应商的选款数量减去１
        这里有多处可以作废产品　所以使用了　post_save
    """
    if instance.status != Product.DELETE:
        return
    pros = instance.same_model_pros()
    if pros is not None:
        sta = pros.values('status').distinct()
        if len(sta) != 1:
            return
        if sta[0]['status'] == Product.DELETE:
            sal_p, supplier = instance.pro_sale_supplier()
            if supplier is not None and supplier.total_select_num > 0:
                supplier.total_select_num = F('total_select_num') - 1
                update_model_fields(supplier, update_fields=['total_select_num'])


post_save.connect(delete_pro_record_supplier, Product)


from shopback.signals import signal_product_upshelf,signal_product_downshelf

def change_obj_state_by_pre_save(sender, instance, raw, *args, **kwargs):
    if not raw and instance and instance.id :
        product = Product.objects.get(id=instance.id)
        # 如果上架时间修改，则重置is_verify
        if product.sale_time != instance.sale_time:
            instance.is_verify = False

        #商品上下架状态变更
        if (product.shelf_status != instance.shelf_status):
            if instance.shelf_status == Product.UP_SHELF:

                # 商品上架信号
                from shopback.items.tasks_stats import \
                    task_product_upshelf_update_productskusalestats
                product_skus = product.normal_skus
                for sku in product_skus:
                    task_product_upshelf_update_productskusalestats.delay(sku.id)

            elif instance.shelf_status == Product.DOWN_SHELF:

                # 商品下架信号
                from shopback.items.tasks_stats import \
                    task_product_downshelf_update_productskusalestats
                sale_end_time = product.offshelf_time or datetime.datetime.now()
                product_skus = product.normal_skus
                for sku in product_skus:
                    task_product_downshelf_update_productskusalestats.delay(sku.id, sale_end_time)

pre_save.connect(change_obj_state_by_pre_save, sender=Product, dispatch_uid='post_save_change_obj_state_by_pre_saves')


def update_mama_shop_down_shelf(sender, instance, raw, *args, **kwargs):
    """ 如果商品是下架状态则更新妈妈店铺的商品到下架状态 """
    if instance.shelf_status != Product.DOWN_SHELF:
        return
    from flashsale.pay.models import CuShopPros
    CuShopPros.update_down_shelf(instance.id)  # 更新所有店铺的　该产品　到　下架状态


pre_save.connect(update_mama_shop_down_shelf, sender=Product, dispatch_uid='post_save_update_mama_shop_down_shelf')


class ProductSku(models.Model):
    """ 记录库存商品规格属性类 """

    class Meta:
        db_table = 'shop_items_productsku'
        unique_together = ("outer_id", "product")
        app_label = 'items'
        verbose_name = u'库存商品规格'
        verbose_name_plural = u'库存商品规格列表'

    cache_enabled = True
    objects = managers.CacheManager()

    NORMAL = pcfg.NORMAL
    REMAIN = pcfg.REMAIN
    DELETE = pcfg.DELETE
    STATUS_CHOICES = (
        (pcfg.NORMAL, u'使用'),
        (pcfg.REMAIN, u'待用'),
        (pcfg.DELETE, u'作废'),
    )

    outer_id = models.CharField(max_length=32, blank=False, verbose_name=u'编码')
    barcode = models.CharField(max_length=64, blank=True, db_index=True, verbose_name='条码')
    product = models.ForeignKey(Product, null=True, related_name='prod_skus', verbose_name='商品')

    quantity = models.IntegerField(default=0, verbose_name='库存数')
    warn_num = models.IntegerField(default=0, verbose_name='警戒数')  # 警戒库位
    remain_num = models.IntegerField(default=0, verbose_name='预留数')  # 预留库存
    wait_post_num = models.IntegerField(default=0, verbose_name='待发数')  # 待发数
    sale_num = models.IntegerField(default=0, verbose_name=u'日出库数')  # 日出库
    reduce_num = models.IntegerField(default=0, verbose_name='预减数')  # 下次入库减掉这部分库存
    lock_num = models.IntegerField(default=0, verbose_name='锁定数')  # 特卖待发货，待付款数量
    # assign_num = models.IntegerField(default=0, verbose_name='分配数')  # 未出库包裹单中已分配的sku数量
    sku_inferior_num = models.IntegerField(default=0, verbose_name=u"次品数")  # 保存对应sku的次品数量

    #history_quantity = models.IntegerField(default=0, verbose_name='历史库存数')  #
    #inbound_quantity = models.IntegerField(default=0, verbose_name='入仓库存数')  #
    #post_num = models.IntegerField(default=0, verbose_name='已发货数')  #
    #sold_num = models.IntegerField(default=0, verbose_name='已被购买数')  #
    #realtime_lock_num = models.IntegerField(default=0, verbose_name='实时f锁定数')  #

    cost = models.FloatField(default=0, verbose_name='成本价')
    std_purchase_price = models.FloatField(default=0, verbose_name='标准进价')
    std_sale_price = models.FloatField(default=0, verbose_name='吊牌价')
    agent_price = models.FloatField(default=0, verbose_name='出售价')
    staff_price = models.FloatField(default=0, verbose_name='员工价')

    weight = models.CharField(max_length=10, blank=True, verbose_name='重量(g)')

    properties_name = models.TextField(max_length=200, blank=True, verbose_name='线上规格名称')
    properties_alias = models.TextField(max_length=200, blank=True, verbose_name='系统规格名称')

    is_split = models.BooleanField(default=False, verbose_name='需拆分')
    is_match = models.BooleanField(default=False, verbose_name='有匹配')

    sync_stock = models.BooleanField(default=True, verbose_name='库存同步')
    # 是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    is_assign = models.BooleanField(default=False, verbose_name='手动分配')

    post_check = models.BooleanField(default=False, verbose_name='需扫描')
    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')
    status = models.CharField(max_length=10, db_index=True, choices=STATUS_CHOICES,
                              default=pcfg.NORMAL, verbose_name='规格状态')  # normal,delete

    match_reason = models.CharField(max_length=80, blank=True, verbose_name='匹配原因')
    buyer_prompt = models.CharField(max_length=60, blank=True, verbose_name='客户提示')
    memo = models.TextField(max_length=1000, blank=True, verbose_name='备注')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.outer_id, self.properties_alias or self.properties_name)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @property
    def stat(self):
        if not hasattr(self, '_stat_'):
            from .stats import ProductSkuStats
            self._stat_ = ProductSkuStats.get_by_sku(self.id)
        return self._stat_

    @property
    def obj_active_sku_salestats(self):
        from .stats import ProductSkuSaleStats
        sku_stats = ProductSkuSaleStats.objects.filter(sku_id=self.id,status=ProductSkuSaleStats.ST_EFFECT).first()
        return sku_stats

    @property
    def realtime_quantity(self):
        """
        This tells how many quantity in store.
        """
        sku_stats = self.stat
        if sku_stats:
            return self.stat.realtime_quantity
        return 0

    @property
    def real_inferior_quantity(self):
        return self.stats.inferior_num

    @property
    def excess_quantity(self):
        """ 多余未售库存数 """
        sku_stats = self.stat
        if sku_stats:
            return max(0, sku_stats.realtime_quantity - sku_stats.wait_post_num)
        return 0

    @property
    def aggregate_quantity(self):
        """
        This tells how many quantity we have in total since we introduced inbound_quantity.
        """
        raise NotImplementedError

    @property
    def name(self):
        return self.properties_alias or self.properties_name

    @property
    def BARCODE(self):
        return self.barcode.strip() or '%s%s' % (self.product.outer_id.strip(),
                                                 self.outer_id.strip())

    def get_supplier_outerid(self):
        return re.sub('-[0-9]$', '', self.outer_id)

    @property
    def realnum(self):
        if self.remain_num >= self.sale_num:
            return self.remain_num - self.sale_num
        return 0

    @property
    def real_remainnum(self):
        """ 实际剩余库存 """
        wait_post_num = max(self.wait_post_num, 0)
        if self.remain_num > 0 and self.remain_num >= wait_post_num:
            return self.remain_num - wait_post_num
        return 0

    @property
    def free_num(self):
        """ 可售库存数 """
        sku_stats = self.stat
        if sku_stats:
            self.lock_num = sku_stats.lock_num
        return max(self.remain_num - max(self.lock_num, 0), 0)


    @property
    def sale_out(self):
        if self.free_num > 0:
            return False
        if self.quantity > self.wait_post_num > 0:
            return False
        return True

    @property
    def ware_by(self):
        return self.product.ware_by

    @property
    def size_of_sku(self):
        try:
            display_num = ""
            if self.free_num > 3:
                display_num = "NO"
            else:
                display_num = self.free_num
            contrast = self.product.contrast.get_correspond_content
            sku_name = self.properties_alias or self.properties_name
            display_sku = contrast[sku_name]
            display_sku = display_sku.items()
            result_data = collections.OrderedDict()
            for p in display_sku:
                result_data[p[0]] = p[1]
            return {"result": result_data, "free_num": display_num}
        except:
            return {"result": {}, "free_num": display_num}

    @property
    def not_assign_num(self):
        return self.stat.not_assign_num

    def calc_discount_fee(self, xlmm=None):
        """ 优惠折扣 """
        if not xlmm or xlmm.agencylevel < 2:
            return 0

        try:
            discount = int(self.product.details.mama_discount)
            if discount > 100:
                discount = 100

            if discount < 0:
                discount = 0
            return float('%.2f' % ((100 - discount) / 100.0 * float(self.agent_price)))
        except:
            return 0

    @property
    def is_out_stock(self):
        quantity = max(self.quantity, 0)
        wait_post_num = max(self.wait_post_num, 0)
        return quantity - wait_post_num <= 0

    @property
    def json(self):
        model_dict = model_to_dict(self)
        model_dict.update({
            'districts': self.get_district_list(),
            'barcode': self.BARCODE,
            'name': self.name
        })
        return model_dict

    def update_quantity(self, num, full_update=False, dec_update=False):
        """ 更新规格库存 """
        if full_update:
            self.quantity = num
        elif dec_update:
            self.quantity = F('quantity') - num
        else:
            self.quantity = F('quantity') + num
        update_model_fields(self, update_fields=['quantity'])

        psku = self.__class__.objects.get(id=self.id)
        self.quantity = psku.quantity

        post_save.send(sender=self.__class__, instance=self, created=False)

    def update_wait_post_num(self, num, full_update=False, dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = models.F('wait_post_num') - num
        else:
            self.wait_post_num = models.F('wait_post_num') + num
        update_model_fields(self, update_fields=['wait_post_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.wait_post_num = psku.wait_post_num

        post_save.send(sender=self.__class__, instance=self, created=False)

    def update_lock_num(self, num, full_update=False, dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.lock_num = num
        elif dec_update:
            self.lock_num = models.F('lock_num') - num
        else:
            self.lock_num = models.F('lock_num') + num
        update_model_fields(self, update_fields=['lock_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.lock_num = psku.lock_num

    def update_reduce_num(self, num, full_update=False, dec_update=False):
        """ 更新商品库存: full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self, update_fields=['reduce_num'])

        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num
        post_save.send(sender=self.__class__, instance=self, created=False)

    def update_quantity_by_storage_num(self, num):
        if num < 0:
            raise Exception(u'入库更新商品库存数不能小于0')

        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num

        self.update_quantity(real_update_num)
        self.update_reduce_num(real_reduct_num, full_update=True)

    @property
    def is_stock_warn(self):
        """
        库存是否警告:
        1，如果当前库存小于0；
        2，同步库存（当前库存-预留库存-待发数）小于警告库位 且没有设置警告取消；
        """
        quantity = max(self.quantity, 0)
        remain_num = max(self.remain_num, 0)
        wait_post_num = max(self.wait_post_num, 0)
        return quantity - remain_num - wait_post_num <= 0

    @property
    def is_warning(self):
        """
        库存预警:
        1，如果当前能同步的库存小昨日销量；
        """
        quantity = max(self.quantity, 0)
        remain_num = max(self.remain_num, 0)
        wait_post_num = max(self.wait_post_num, 0)
        sync_num = quantity - remain_num - wait_post_num
        return self.warn_num > 0 and self.warn_num >= sync_num

    @property
    def district(self):
        from .storage import ProductLocation
        location = ProductLocation.objects.filter(product_id=self.product.id, sku_id=self.id).first()
        if location:
            return location.district

    def get_district_list(self):
        from .storage import ProductLocation
        locations = ProductLocation.objects.filter(product_id=self.product.id, sku_id=self.id)
        return [(l.district.parent_no, l.district.district_no) for l in locations]

    def get_districts_code(self):
        """ 商品库中区位,ret_type :c,返回组合后的字符串；o,返回[父编号]-[子编号],... """
        locations = self.get_district_list()
        sdict = {}
        for d in locations:
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])
        dc_list = sorted(sdict.items(), key=lambda d: d[0])
        ds = []
        for k, v in dc_list:
            ds.append('%s-[%s]' % (k, ','.join(v)))
        return ','.join(ds)

    def get_sum_sku_inferior_num(self):
        same_pro_skus = ProductSku.objects.filter(product_id=self.product_id)
        sum_inferior_num = same_pro_skus.aggregate(total_inferior=Sum("sku_inferior_num")).get("total_inferior") or 0
        return sum_inferior_num

    @property
    def collect_amount(self):
        return self.cost * self.quantity

    @staticmethod
    def get_by_outer_id(outer_id, outer_sku_id):
        product = Product.objects.get(outer_id=outer_id)
        # return ProductSku.objects.filter(outer_id=outer_sku_id, product_id=product.id).first()
        return ProductSku.objects.get(outer_id=outer_sku_id, product_id=product.id)

    def is_deposite(self):
        return self.product.outer_id.startswith(Product.DIPOSITE_CODE_PREFIX)

def calculate_product_stock_num(sender, instance, *args, **kwargs):
    """修改SKU库存后，更新库存商品的总库存 """
    product = instance.product
    if not product:
        return

    product_skus = product.pskus
    if product_skus.exists():
        product_dict = product_skus.aggregate(total_collect_num=Sum('quantity'),
                                              total_warn_num=Sum('warn_num'),
                                              total_remain_num=Sum('remain_num'),
                                              total_post_num=Sum('wait_post_num'),
                                              total_reduce_num=Sum('reduce_num'),
                                              total_lock_num=Sum('lock_num'),
                                              total_inferior_num=Sum('sku_inferior_num'),
                                              avg_cost=Avg('cost'),
                                              avg_purchase_price=Avg('std_purchase_price'),
                                              avg_sale_price=Avg('std_sale_price'),
                                              avg_agent_price=Avg('agent_price'),
                                              avg_staff_price=Avg('staff_price'))

        product.collect_num = product_dict.get('total_collect_num') or 0
        product.warn_num = product_dict.get('total_warn_num') or 0
        product.remain_num = product_dict.get('total_remain_num') or 0
        product.wait_post_num = product_dict.get('total_post_num') or 0
        product.reduce_num = product_dict.get('reduce_num') or 0
        product.lock_num = product_dict.get('total_lock_num') or 0
        product.inferior_num = product_dict.get('total_inferior_num') or 0

        product.cost = "{0:.2f}".format(product_dict.get('avg_cost') or 0)
        product.std_purchase_price = "{0:.2f}".format(product_dict.get('avg_purchase_price') or 0)
        product.std_sale_price = "{0:.2f}".format(product_dict.get('avg_sale_price') or 0)
        product.agent_price = "{0:.2f}".format(product_dict.get('avg_agent_price') or 0)
        product.staff_price = "{0:.2f}".format(product_dict.get('avg_staff_price') or 0)

        update_model_fields(product, ["collect_num", "warn_num", "remain_num", "wait_post_num",
                                      "lock_num", "inferior_num", "reduce_num", "std_purchase_price",
                                      "cost", "std_sale_price", "agent_price", "staff_price"])
        # product.save()


post_save.connect(calculate_product_stock_num, sender=ProductSku, dispatch_uid='calculate_product_num')


def create_product_skustats(sender, instance, created, **kwargs):
    """
    Whenever ProductSku gets created, we create ProductSkuStats
    """
    if created:
        from shopback.items.tasks import task_productsku_update_productskustats
        task_productsku_update_productskustats.delay(instance.id, instance.product.id)

post_save.connect(create_product_skustats, sender=ProductSku, dispatch_uid='post_save_create_productskustats')


def upshelf_product_clear_locknum(sender, product_list, *args, **kwargs):
    """ 商品上架时将商品规格待发数更新为锁定库存数 """
    for product in product_list:
        product.prod_skus.update(lock_num=F('wait_post_num'))


signal_product_upshelf.connect(upshelf_product_clear_locknum, sender=Product)
