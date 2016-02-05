# coding: utf-8

"""
淘宝普通平台模型:
Product:系统内部商品，唯一对应多家店铺的商品外部编码,
ProductSku:淘宝平台商品sku，
Item:淘宝平台商品，
"""

import collections
import datetime
import json
import logging
import re

from django.db import models
from django.db.models import Sum,Avg,F
from django.db.models.signals import pre_save,post_save
from django.core.urlresolvers import reverse

from auth import apis
from common.modelutils import update_model_fields
from core.models import AdminModel
from flashsale.dinghuo.models_user import MyUser
from flashsale.restpro.local_cache import image_watermark_cache
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField
from shopback.categorys.models import Category,ProductCategory
from shopback.archives.models import Deposite,DepositeDistrict
from shopback import paramconfig as pcfg
from shopback.users.models import DjangoUser,User
from supplychain.supplier.models import SaleProduct

from . import constants, manager
logger = logging.getLogger('django.request')


APPROVE_STATUS  = (
    (pcfg.ONSALE_STATUS,u'在售'),
    (pcfg.INSTOCK_STATUS,u'库中'),
)

ONLINE_PRODUCT_STATUS = (
    (pcfg.NORMAL,u'使用'),
    (pcfg.REMAIN,u'待用'),
    (pcfg.DELETE,u'作废'),
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,u'使用'),
    (pcfg.DELETE,u'作废'),
)
#押金编码前缀
DIPOSITE_CODE_PREFIX = 'RMB'

class ProductDefectException(Exception):
    pass


class Product(models.Model):
    """ 记录库存属性及加上排期信息的商品类 """

    class Meta:
        db_table = 'shop_items_product'
        verbose_name = u'库存商品'
        verbose_name_plural = u'库存商品列表'
        permissions = [
            ("change_product_skunum", u"修改库存信息"),
            ("change_product_shelf",  u"特卖商品上架/下架"),
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

    UP_SHELF = 1
    DOWN_SHELF = 0
    SHELF_CHOICES = ((UP_SHELF,u'已上架'),
                     (DOWN_SHELF,u'未上架'))

    WARE_NONE  = 0
    WARE_SH    = 1
    WARE_GZ    = 2
    WARE_CHOICES = ((WARE_NONE,u'未选仓'),
                    (WARE_SH,u'上海仓'),
                    (WARE_GZ,u'广州仓'))

    ProductCodeDefect = ProductDefectException
    PRODUCT_CODE_DELIMITER = '.'
    NO_PIC_PATH = '/media/img/nopic.jpg'

    outer_id     = models.CharField(max_length=64,unique=True,null=False,
                                    blank=True,verbose_name=u'外部编码')
    name         = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'商品名称')
    model_id     = models.BigIntegerField(db_index=True,default=0,verbose_name='商品款式ID')

    barcode      = models.CharField(max_length=64,blank=True,db_index=True,verbose_name=u'条码')
    category     = models.ForeignKey(ProductCategory,null=True,blank=True,
                                     related_name='products',verbose_name=u'内部分类')
    pic_path     = models.CharField(max_length=256,blank=True,verbose_name=u'商品主图')

    collect_num  = models.IntegerField(default=0,verbose_name=u'库存数')  #库存数
    warn_num     = models.IntegerField(default=0,verbose_name=u'警告数')  #警戒库位
    remain_num   = models.IntegerField(default=0,verbose_name=u'预留数')  #预留库存
    wait_post_num   = models.IntegerField(default=0,verbose_name=u'待发数')  #待发数
    sale_num     = models.IntegerField(default=0,verbose_name=u'日出库数')  #日出库
    reduce_num   = models.IntegerField(default=0,verbose_name=u'预减数')  #下次入库减掉这部分库存
    lock_num      = models.IntegerField(default=0,verbose_name='锁定数')    #特卖待发货，待付款数量
    inferior_num  = models.IntegerField(default=0, verbose_name=u"次品数")  #保存对应sku的次品数量

    cost         = models.FloatField(default=0,verbose_name=u'成本价')
    std_purchase_price = models.FloatField(default=0,verbose_name=u'标准进价')
    std_sale_price     = models.FloatField(default=0,verbose_name=u'吊牌价')
    agent_price        = models.FloatField(default=0,verbose_name=u'出售价')
    staff_price        = models.FloatField(default=0,verbose_name=u'员工价')

    weight       = models.CharField(max_length=10,blank=True,verbose_name=u'重量(g)')
    created      = models.DateTimeField(null=True,blank=True,
                                        auto_now_add=True,verbose_name=u'创建时间')
    modified     = models.DateTimeField(null=True,blank=True,db_index=True,
                                        auto_now=True,verbose_name=u'修改时间')
    sale_time    = models.DateField(null=True,blank=True,db_index=True,verbose_name=u'上架日期')
    offshelf_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'下架时间')

    is_split   = models.BooleanField(default=False,verbose_name=u'需拆分')
    is_match   = models.BooleanField(default=False,verbose_name=u'有匹配')
    sync_stock   = models.BooleanField(default=True,verbose_name=u'库存同步')
    is_assign    = models.BooleanField(default=False,verbose_name=u'取消警告')
    post_check   = models.BooleanField(default=False,verbose_name=u'需扫描')
    is_watermark = models.BooleanField(default=False, verbose_name=u'图片水印')
    is_seckill = models.BooleanField(default=False, verbose_name=u'是否秒杀')
    status       = models.CharField(max_length=16,db_index=True,
                                    choices=ONLINE_PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name=u'商品状态')

    match_reason = models.CharField(max_length=80,blank=True,verbose_name=u'匹配原因')
    buyer_prompt = models.CharField(max_length=60,blank=True,verbose_name=u'客户提示')
    memo         = models.TextField(max_length=1000,blank=True,verbose_name=u'备注')

    sale_charger = models.CharField(max_length=32,db_index=True,blank=True,
                                    verbose_name=u'归属采购员')
    storage_charger = models.CharField(max_length=32,db_index=True,blank=True,
                                    verbose_name=u'归属仓管员')
    sale_product = models.BigIntegerField(db_index=True, default=0, verbose_name='选品ID')
    is_verify    = models.BooleanField(default=False,verbose_name=u'是否校对')
    shelf_status = models.IntegerField(choices=SHELF_CHOICES,db_index=True,
                                       default=DOWN_SHELF,verbose_name=u'上架状态')
    ware_by        = models.IntegerField(default=WARE_SH,choices=WARE_CHOICES,
                                         db_index=True,verbose_name=u'所属仓库')

    def __unicode__(self):
        return '%s'%self.id
        #return '<%s,%s>'%(self.outer_id,self.name)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())


    def get_product_model(self):
        """ 获取商品款式 """
        if self.model_id == 0:
            return None
        from flashsale.pay.models_custom import ModelProduct
        try:
            pmodel = ModelProduct.objects.get(id=self.model_id)
        except:
            return None
        return pmodel

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
        return self.prod_skus.filter(status__in=(pcfg.NORMAL,pcfg.REMAIN))

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

    def has_quantity(self):
        return self.collect_num > 0

    def sale_open(self):
        """ 返回特卖商品是否开售 """
        return self.shelf_status == self.UP_SHELF

    def new_good(self):
        """ 返回特卖商品是否新品 """
        return self.sale_time and self.sale_time >= datetime.date.today()

    def is_sale_out(self):
        return self.sale_out

    def is_deposite(self):
        return self.outer_id.startswith(DIPOSITE_CODE_PREFIX)

    def is_onshelf(self):
        return self.shelf_status == self.UP_SHELF

    @property
    def is_out_stock(self):
        if self.collect_num<0 or self.wait_post_num <0 :
            self.collect_num = self.collect_num >0 and self.collect_num or 0
            self.wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0
            self.save()
        return self.collect_num-self.wait_post_num <= 0

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

    def head_img(self):
        """ 获取商品款式 """
        if self.model_id == 0:
            self.model_id = None
        from flashsale.pay.models_custom import ModelProduct
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

        return {
                'id':self.id,
                'outer_id':self.outer_id,
                'name':self.name,
                'category':self.category or {},
                'collect_num':self.collect_num,
                'remain_num':self.remain_num,
                'warn_num':self.warn_num,
                'wait_post_num':self.wait_post_num,
                'cost':self.cost,
                'std_purchase_price':self.std_purchase_price,
                'std_sale_price':self.std_sale_price,
                'agent_price':self.agent_price,
                'staff_price':self.staff_price,
                'weight':self.weight,
                'sync_stock':self.sync_stock,
                'is_split':self.is_split,
                'is_match':self.is_match,
                'is_assign':self.is_assign,
                'is_stock_warn':self.is_stock_warn,
                'is_warning':self.is_warning,
                'post_check':self.post_check,
                'status':dict(ONLINE_PRODUCT_STATUS).get(self.status,''),
                'buyer_prompt':self.buyer_prompt,
                'memo':self.memo,
                'districts':self.get_district_list(),
                'barcode':self.BARCODE,
                'match_reason':self.match_reason,
                'skus':skus_json
                }

    def title(self):
        return self.name

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
        update_model_fields(self,update_fields=['collect_num'])

        self.collect_num = self.__class__.objects.get(id=self.id).collect_num


    def update_wait_post_num(self,num,full_update=False,dec_update=False):
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
        update_model_fields(self,update_fields=['wait_post_num'])

        self.wait_post_num = self.__class__.objects.get(id=self.id).wait_post_num

    def update_reduce_num(self,num,full_update=False,dec_update=False):
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
        update_model_fields(self,update_fields=['reduce_num'])

        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num


    def update_quantity_by_storage_num(self,num):

        if num < 0 :
            raise Exception(u'入库更新商品库存数不能小于0')

        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num

        self.update_collect_num(real_update_num)
        self.update_reduce_num(real_reduct_num,full_update=True)

    @property
    def is_stock_warn(self):
        """
        库存是否警告
        """
        for sku in self.eskus:
            if sku.is_stock_warn and not sku.is_assign:
                return True

        collect_num = self.collect_num >0 and self.collect_num or 0
        remain_num = self.remain_num >0 and self.remain_num or 0
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0

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

        collect_num = self.collect_num >0 and self.collect_num or 0
        remain_num = self.remain_num >0 and self.remain_num or 0
        wait_post_num = self.wait_post_num >0 and self.wait_post_num or 0
        sync_num = collect_num - remain_num - wait_post_num
        return self.warn_num >0 and self.warn_num >= sync_num

    def get_district_list(self):
        locations = ProductLocation.objects.filter(product_id=self.id)
        return [(l.district.parent_no,l.district.district_no) for l in locations]

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

        dc_list = sorted(sdict.items(),key=lambda d:d[0])
        ds = []
        for k,v in dc_list:
            ds.append(len(v)>1 and '%s-[%s]'%(k,','.join(list(v))) or '%s-%s'%(k,v.pop()))

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

    def same_model_pros(self):
        """ 同款产品　"""
        if self.model_id == 0 or self.model_id is None:
            return None
        pros = self.__class__.objects.filter(model_id=self.model_id)
        return pros

    def in_customer_shop(self, customer):
        """在用户我的店铺中有本产品则返回true否则返回false"""
        try:
            customer_shop = CustomerShops.objects.get(customer=customer)
            cps = CuShopPros.objects.filter(product=self.id, shop=customer_shop.id)
            if cps.exists():
                return cps[0].pro_status
            return 0
        except:
            return 0
from flashsale.pay.models_shops import CuShopPros, CustomerShops


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


from shopback.signals import signal_product_upshelf


def change_obj_state_by_pre_save(sender, instance, raw, *args, **kwargs):

    products = Product.objects.filter(id=instance.id)
    if products.count() > 0:
        product = products[0]
        #如果上架时间修改，则重置is_verify
        if product.sale_time != instance.sale_time:
            instance.is_verify = False
        if (product.shelf_status != instance.shelf_status and
            instance.shelf_status == Product.UP_SHELF):
            #通知其它程序商品上架状态发生变化
            signal_product_upshelf.send(sender=Product, product_list=[product])


pre_save.connect(change_obj_state_by_pre_save, sender=Product)


def custom_sort(a, b):
    c = ContrastContent.objects.get(name=a[0])
    d = ContrastContent.objects.get(name=b[0])
    return int(c.sid) - int(d.sid)


class ProductSku(models.Model):
    """ 记录库存商品规格属性类 """

    class Meta:
        db_table = 'shop_items_productsku'
        unique_together = ("outer_id", "product")
        verbose_name=u'库存商品规格'
        verbose_name_plural = u'库存商品规格列表'

    cache_enabled = True
    objects = managers.CacheManager()

    NORMAL = pcfg.NORMAL
    REMAIN = pcfg.REMAIN
    DELETE = pcfg.DELETE

    outer_id = models.CharField(max_length=64,blank=False,verbose_name=u'供应商货号/编码')

    barcode  = models.CharField(max_length=64,blank=True,db_index=True,verbose_name='条码')
    product  = models.ForeignKey(Product,null=True,related_name='prod_skus',verbose_name='商品')

    quantity     = models.IntegerField(default=0,verbose_name='库存数')
    warn_num     = models.IntegerField(default=0,verbose_name='警戒数')    #警戒库位
    remain_num   = models.IntegerField(default=0,verbose_name='预留数')    #预留库存
    wait_post_num = models.IntegerField(default=0,verbose_name='待发数')    #待发数
    sale_num      = models.IntegerField(default=0,verbose_name=u'日出库数') #日出库
    reduce_num    = models.IntegerField(default=0,verbose_name='预减数')    #下次入库减掉这部分库存
    lock_num      = models.IntegerField(default=0,verbose_name='锁定数')    #特卖待发货，待付款数量
    sku_inferior_num = models.IntegerField(default=0, verbose_name=u"次品数") #　保存对应sku的次品数量

    cost          = models.FloatField(default=0,verbose_name='成本价')
    std_purchase_price = models.FloatField(default=0,verbose_name='标准进价')
    std_sale_price     = models.FloatField(default=0,verbose_name='吊牌价')
    agent_price        = models.FloatField(default=0,verbose_name='出售价')
    staff_price        = models.FloatField(default=0,verbose_name='员工价')

    weight             = models.CharField(max_length=10,blank=True,verbose_name='重量(g)')

    properties_name    = models.TextField(max_length=200,blank=True,verbose_name='线上规格名称')
    properties_alias   = models.TextField(max_length=200,blank=True,verbose_name='系统规格名称')

    is_split   = models.BooleanField(default=False,verbose_name='需拆分')
    is_match   = models.BooleanField(default=False,verbose_name='有匹配')

    sync_stock   = models.BooleanField(default=True,verbose_name='库存同步')
    #是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    is_assign    = models.BooleanField(default=False,verbose_name='手动分配')

    post_check   = models.BooleanField(default=False,verbose_name='需扫描')
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建时间')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    status       = models.CharField(max_length=10,db_index=True,choices=ONLINE_PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name='规格状态')  #normal,delete

    match_reason = models.CharField(max_length=80,blank=True,verbose_name='匹配原因')
    buyer_prompt = models.CharField(max_length=60,blank=True,verbose_name='客户提示')
    memo         = models.TextField(max_length=1000,blank=True,verbose_name='备注')

    def __unicode__(self):
        return '<%s,%s:%s>'%(self.id,self.outer_id,self.properties_alias or self.properties_name)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @property
    def name(self):
        return self.properties_alias or self.properties_name

    @property
    def BARCODE(self):
        return self.barcode.strip() or '%s%s'%(self.product.outer_id.strip(),
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
        lock_num = max(self.lock_num,0)
        rnum = self.remain_num - lock_num
        if rnum < 0:
            return 0
        return rnum

    @property
    def sale_out(self):
        if self.free_num > 0:
            return False
        if self.quantity > self.wait_post_num > 0:
            return False
        return True

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
            display_sku.sort(cmp=custom_sort)
            result_data = collections.OrderedDict()
            for p in display_sku:
                result_data[p[0]] = p[1]
            return {"result": result_data, "free_num": display_num}
        except:
            return {"result": {}, "free_num": display_num}

    def calc_discount_fee(self,xlmm=None):
        """ 优惠折扣 """
        if not xlmm or xlmm.agencylevel != 2:
            return 0

        try:
            discount = int(self.product.details.mama_discount)
            if discount > 100:
                discount = 100

            if discount < 0:
                discount = 0
            return float('%.2f'%((100 - discount) / 100.0 * float(self.agent_price)))
        except:
            return 0

    @property
    def is_out_stock(self):
        quantity      = max(self.quantity, 0)
        wait_post_num = max(self.wait_post_num, 0)
        return quantity - wait_post_num <= 0

    @property
    def json(self):
        sku = self
        return {'id':sku.id,
                'outer_id':sku.outer_id,
                'properties_name':sku.properties_name,
                'properties_alias':sku.properties_alias,
                'name':sku.name,
                'cost':sku.cost,
                'std_purchase_price':sku.std_purchase_price,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
                'staff_price':sku.staff_price,
                'weight':sku.weight,
                'quantity':sku.quantity,
                'warn_num':sku.warn_num,
                'wait_post_num':sku.wait_post_num,
                'remain_num':sku.remain_num,
                'sync_stock':sku.sync_stock,
                'is_split':sku.is_split,
                'is_match':sku.is_match,
                'post_check':sku.post_check,
                'status':sku.status,
                'is_stock_warn':sku.is_stock_warn,
                'is_assign':sku.is_assign,
                'is_warning':sku.is_warning,
                'status':sku.status,
                'buyer_prompt':sku.buyer_prompt,
                'memo':sku.memo,
                'match_reason':sku.match_reason,
                'districts':sku.get_district_list(),
                'barcode':sku.BARCODE}


    def update_quantity(self,num,full_update=False,dec_update=False):
        """ 更新规格库存 """
        if full_update:
            self.quantity = num
        elif dec_update:
            self.quantity = F('quantity') - num
        else:
            self.quantity = F('quantity') + num
        update_model_fields(self,update_fields=['quantity'])

        psku = self.__class__.objects.get(id=self.id)
        self.quantity = psku.quantity

        post_save.send(sender=self.__class__,instance=self,created=False)


    def update_wait_post_num(self,num,full_update=False,dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = models.F('wait_post_num') - num
        else:
            self.wait_post_num = models.F('wait_post_num') + num
        update_model_fields(self,update_fields=['wait_post_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.wait_post_num = psku.wait_post_num

        post_save.send(sender=self.__class__,instance=self,created=False)

    def update_lock_num(self,num,full_update=False,dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.lock_num = num
        elif dec_update:
            self.lock_num = models.F('lock_num') - num
        else:
            self.lock_num = models.F('lock_num') + num
        update_model_fields(self,update_fields=['lock_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.lock_num = psku.lock_num


    def update_reduce_num(self,num,full_update=False,dec_update=False):
        """ 更新商品库存: full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self,update_fields=['reduce_num'])

        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num
        post_save.send(sender=self.__class__,instance=self,created=False)


    def update_quantity_by_storage_num(self,num):

        if num < 0 :
            raise Exception(u'入库更新商品库存数不能小于0')

        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num

        self.update_quantity(real_update_num)
        self.update_reduce_num(real_reduct_num,full_update=True)


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
        quantity      = max(self.quantity, 0)
        remain_num    = max(self.remain_num, 0)
        wait_post_num = max(self.wait_post_num, 0)
        sync_num      = quantity - remain_num - wait_post_num
        return self.warn_num >0 and self.warn_num >= sync_num

    def get_district_list(self):
        locations = ProductLocation.objects.filter(product_id=self.product.id,sku_id=self.id)
        return [(l.district.parent_no,l.district.district_no) for l in locations]

    def get_districts_code(self):
        """ 商品库中区位,ret_type :c,返回组合后的字符串；o,返回[父编号]-[子编号],... """
        locations = self.get_district_list()
        sdict     = {}
        for d in locations:
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])
        dc_list = sorted(sdict.items(),key=lambda d:d[0])
        ds = []
        for k,v in dc_list:
            ds.append('%s-[%s]'%(k,','.join(v)))
        return ','.join(ds)

    def get_sum_sku_inferior_num(self):
        same_pro_skus = ProductSku.objects.filter(product_id=self.product_id)
        sum_inferior_num = same_pro_skus.aggregate(total_inferior=Sum("sku_inferior_num")).get("total_inferior") or 0
        return sum_inferior_num

    @property
    def collect_amount(self):
        return self.cost * self.quantity


def calculate_product_stock_num(sender, instance, *args, **kwargs):
    """修改SKU库存后，更新库存商品的总库存 """
    product = instance.product
    if not product:
        return

    product_skus = product.pskus
    if product_skus.exists():
        product_dict  = product_skus.aggregate(total_collect_num=Sum('quantity'),
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

        product.collect_num  =  product_dict.get('total_collect_num') or 0
        product.warn_num     =  product_dict.get('total_warn_num') or 0
        product.remain_num   =  product_dict.get('total_remain_num') or 0
        product.wait_post_num  =  product_dict.get('total_post_num') or 0
        product.reduce_num     =  product_dict.get('reduce_num') or 0
        product.lock_num       =  product_dict.get('total_lock_num') or 0
        product.inferior_num   =  product_dict.get('total_inferior_num') or 0

        product.cost               = "{0:.2f}".format(product_dict.get('avg_cost') or 0)
        product.std_purchase_price = "{0:.2f}".format(product_dict.get('avg_purchase_price') or 0)
        product.std_sale_price     = "{0:.2f}".format(product_dict.get('avg_sale_price') or 0)
        product.agent_price        = "{0:.2f}".format(product_dict.get('avg_agent_price') or 0)
        product.staff_price        = "{0:.2f}".format(product_dict.get('avg_staff_price') or 0)

        update_model_fields(product, ["collect_num", "warn_num", "remain_num", "wait_post_num",
                                      "lock_num","inferior_num","reduce_num", "std_purchase_price",
                                      "cost", "std_sale_price", "agent_price", "staff_price"])
        # product.save()

post_save.connect(calculate_product_stock_num, sender=ProductSku, dispatch_uid='calculate_product_num')


def upshelf_product_clear_locknum(sender, product_list, *args, **kwargs):
    """ 商品上架时将商品规格待发数更新为锁定库存数 """
    for product in product_list:
        product.prod_skus.update(lock_num=F('wait_post_num'))

signal_product_upshelf.connect(upshelf_product_clear_locknum, sender=Product)

class Item(models.Model):
    """ 淘宝线上商品 """

    num_iid  = models.CharField(primary_key=True,max_length=64,verbose_name='商品ID')

    user     = models.ForeignKey(User,null=True,related_name='items',verbose_name='店铺')
    category = models.ForeignKey(Category,null=True,related_name='items',verbose_name='淘宝分类')
    product  = models.ForeignKey(Product,null=True,related_name='items',verbose_name='关联库存商品')

    outer_id = models.CharField(max_length=64,blank=True,verbose_name='外部编码')
    num      = models.IntegerField(null=True,verbose_name='数量')
    sync_stock = models.BooleanField(default=True,verbose_name='库存同步')

    seller_cids = models.CharField(max_length=126,blank=True,verbose_name='卖家分类')
    approve_status = models.CharField(max_length=20,choices=APPROVE_STATUS,blank=True,verbose_name='在售状态')  # onsale,instock
    type       = models.CharField(max_length=12,blank=True,verbose_name='商品类型')
    valid_thru = models.IntegerField(null=True,verbose_name='有效期')

    with_hold_quantity = models.IntegerField(default=0,verbose_name='拍下未付款数')
    delivery_time  = models.DateTimeField(null=True,blank=True,verbose_name='发货时间')

    price      = models.CharField(max_length=12,blank=True,verbose_name='价格')
    postage_id = models.BigIntegerField(null=True,verbose_name='运费模板ID')

    has_showcase = models.BooleanField(default=False,verbose_name='橱窗推荐')
    modified     = models.DateTimeField(null=True,blank=True,verbose_name='修改时间')

    list_time   = models.DateTimeField(null=True,blank=True,verbose_name='上架时间')
    delist_time = models.DateTimeField(null=True,blank=True,verbose_name='下架时间')

    has_discount = models.BooleanField(default=False,verbose_name='有折扣')

    props = models.TextField(blank=True,verbose_name='商品属性')
    title = models.CharField(max_length=148,blank=True,verbose_name='商品标题')
    property_alias = models.TextField(blank=True,verbose_name='自定义属性')

    has_invoice = models.BooleanField(default=False,verbose_name='有发票')
    pic_url     = models.URLField(verify_exists=False,blank=True,verbose_name='商品图片')
    detail_url  = models.URLField(verify_exists=False,blank=True,verbose_name='详情链接')

    last_num_updated = models.DateTimeField(null=True,blank=True,verbose_name='最后库存同步日期')  #该件商品最后库存同步日期

    desc = models.TextField(blank=True,verbose_name='商品描述')
    skus = models.TextField(blank=True,verbose_name='规格')

    status = models.BooleanField(default=True,verbose_name='使用')
    class Meta:
        db_table = 'shop_items_item'
        verbose_name = u'线上商品'
        verbose_name_plural = u'线上商品列表'


    def __unicode__(self):
        return '<%s,%s,%s>'%(self.num_iid,self.outer_id,self.title)

    @property
    def sku_list(self):
        try:
            return json.loads(self.skus)
        except:
            return {}

    @property
    def property_alias_dict(self):
        property_list = self.property_alias.split(';')
        property_dict = {}
        for p in property_list:
            if p:
                r = p.split(':')
                property_dict['%s:%s'%(r[0],r[1])]=r[2]
        return property_dict

    @classmethod
    def get_or_create(cls,user_id,num_iid,force_update=False):
        item,state = Item.objects.get_or_create(num_iid=num_iid)
        if state or force_update:
            try:
                response  = apis.taobao_item_get(num_iid=num_iid,tb_user_id=user_id)
                item_dict = response['item_get_response']['item']
                item      = Item.save_item_through_dict(user_id,item_dict)

            except Exception,exc:
                logger.error('商品更新出错(num_iid:%s)'%str(num_iid),exc_info=True)
        return item

    @classmethod
    def save_item_through_dict(cls,user_id,item_dict):

        category = Category.get_or_create(user_id,item_dict['cid'])
        if item_dict.has_key('outer_id') and item_dict['outer_id']:
            products = Product.objects.filter(outer_id=item_dict['outer_id'])
            product = None
            if products.count() > 0:
                product = products[0]
                product.name        = product.name or item_dict['title']
                product.pic_path    = product.pic_path or item_dict['pic_url']
                product.save()
        else:
            #logger.warn('item has no outer_id(num_iid:%s)'%str(item_dict['num_iid']))
            product = None

        item,state    = cls.objects.get_or_create(num_iid = item_dict['num_iid'])
        skus = item_dict.get('skus',None)
        item_dict['skus'] = skus and skus or item.skus
        for k,v in item_dict.iteritems():
            hasattr(item,k) and setattr(item,k,v)

        if not item.last_num_updated:
            item.last_num_updated = datetime.datetime.now()

        item.user     = User.objects.get(visitor_id=user_id)
        item.product  = product
        item.category = category
        item.status   = True
        item.save()
        return item

class SkuProperty(models.Model):
    """
        规格属性
    """

    num_iid          = models.BigIntegerField(verbose_name='商品ID')
    sku_id           = models.BigIntegerField(verbose_name='规格ID')
    outer_id         = models.CharField(max_length=32,null=True,blank=True,verbose_name='编码')

    properties_name  = models.CharField(max_length=512,null=True,blank=True,verbose_name='规格名称')
    properties       = models.CharField(max_length=512,null=True,blank=True,verbose_name='规格')
    created          = models.DateTimeField(null=True,blank=True,verbose_name='创建日期')

    with_hold_quantity = models.IntegerField(default=0,verbose_name='拍下未付款数')
    sku_delivery_time  = models.DateTimeField(null=True,blank=True,verbose_name='发货时间')

    modified         = models.DateTimeField(null=True,blank=True,verbose_name='修改日期')
    price            = models.FloatField(default=0.0,verbose_name='价格')

    quantity         = models.IntegerField(default=0,verbose_name='数量')
    status           = models.CharField(max_length=10,blank=True,choices=PRODUCT_STATUS,verbose_name='状态')

    class Meta:
        db_table = 'shop_items_skuproperty'
        unique_together = ("num_iid", "sku_id")
        verbose_name = u'线上商品规格'
        verbose_name_plural = u'线上商品规格列表'

    @property
    def properties_alias(self):
        return ''.join([p.split(':')[3] for p in self.properties_name.split(';') if p])

    @classmethod
    def save_or_update(cls,sku_dict):

        sku,state = cls.objects.get_or_create(num_iid=sku_dict.pop('num_iid'),
                                              sku_id=sku_dict.pop('sku_id'))
        for k,v in sku_dict.iteritems():
            if k == 'outer_id' and not v :continue
            hasattr(sku,k) and setattr(sku,k,v)
        sku.save()
        return sku


class ProductLocation(models.Model):
    """ 库存商品库位信息 """

    product_id   = models.IntegerField(db_index=True,verbose_name='商品ID')
    sku_id       = models.IntegerField(db_index=True,blank=True,null=True,verbose_name='规格ID')

    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')

    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')

    district     = models.ForeignKey(DepositeDistrict,
                                     related_name='product_locations',
                                     verbose_name='关联库位')

    class Meta:
        db_table = 'shop_items_productlocation'
        unique_together = ("product_id", "sku_id", "district")
        verbose_name = u'商品库位'
        verbose_name_plural = u'商品库位列表'


class ItemNumTaskLog(models.Model):

    id = BigIntegerAutoField(primary_key=True)

    user_id  = models.CharField(max_length=64,blank=True,verbose_name='店铺ID')
    outer_id = models.CharField(max_length=64,blank=True,verbose_name='商品编码')
    sku_outer_id = models.CharField(max_length=64,blank=True,verbose_name='规格编码')

    num = models.IntegerField(verbose_name='同步数量')

    start_at   = models.DateTimeField(null=True,blank=True,verbose_name='同步期始')
    end_at     = models.DateTimeField(null=True,blank=True,verbose_name='同步期末')

    class Meta:
        db_table = 'shop_items_itemnumtasklog'
        verbose_name=u'库存同步日志'
        verbose_name_plural = u'库存同步日志'

    def __unicode__(self):
        return '<%s,%s,%d>'%(self.outer_id,
                             self.sku_outer_id,
                             self.num)


class ProductDaySale(models.Model):

    id       = BigIntegerAutoField(primary_key=True)

    day_date = models.DateField(verbose_name=u'销售日期')
    sale_time = models.DateField(null=True,verbose_name=u'上架日期')

    user_id  = models.BigIntegerField(null=False,verbose_name=u'店铺用户ID')
    product_id  = models.IntegerField(null=False,verbose_name='商品ID')
    sku_id      = models.IntegerField(null=True,verbose_name='规格ID')
    outer_id    = models.CharField(max_length=64,blank=True,db_index=True,verbose_name='商品编码')

    sale_num     = models.IntegerField(default=0,verbose_name='销售数量')
    sale_payment = models.FloatField(default=0.0,verbose_name='销售金额')
    sale_refund  = models.FloatField(default=0.0,verbose_name='退款金额')

    confirm_num  = models.IntegerField(default=0,verbose_name='成交数量')
    confirm_payment  = models.FloatField(default=0.0,verbose_name='成交金额')

    class Meta:
        db_table = 'shop_items_daysale'
        unique_together = ("day_date","user_id","product_id","sku_id")
        verbose_name    = u'商品销量统计'
        verbose_name_plural = u'商品销量统计'

    def __unicode__(self):
        return '<%s,%s,%d,%d,%s>'%(self.id,
                                   self.day_date,
                                   self.user_id,
                                   self.product_id,
                                   str(self.sku_id))

class ProductScanStorage(models.Model):

    DELETE = -1
    PASS = 1
    WAIT = 0
    SCAN_STATUS = ((DELETE,u'已删除'),
                   (WAIT,u'未入库'),
                   (PASS,u'已入库'))

    product_id = models.IntegerField(null=True,verbose_name=u'商品ID')
    sku_id     = models.IntegerField(null=True,verbose_name=u'规格ID')

    qc_code    = models.CharField(max_length=32,blank=True,verbose_name=u'商品编码')
    sku_code   = models.CharField(max_length=32,blank=True,verbose_name=u'规格编码')
    barcode    = models.CharField(max_length=32,blank=True,verbose_name=u'商品条码')

    product_name   = models.CharField(max_length=32,blank=True,verbose_name=u'商品名称')
    sku_name       = models.CharField(max_length=32,blank=True,verbose_name=u'规格名称')

    scan_num   = models.IntegerField(null=False,default=0,verbose_name=u'扫描次数')

    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')

    wave_no    = models.CharField(max_length=32,blank=True,verbose_name=u'批次号')

    status     = models.IntegerField(null=False,default=WAIT,choices=SCAN_STATUS,verbose_name=u'状态')

    class Meta:
        db_table = 'shop_items_scan'
        unique_together = ("wave_no","product_id","sku_id")
        verbose_name    = u'扫描入库商品'
        verbose_name_plural = u'扫描入库商品列表'

    def __unicode__(self):
        return '<%s,%s,%d>'%(self.id,
                             self.barcode,
                             self.scan_num)


from shopback.base.models import JSONCharMyField

SKU_DEFAULT = (
    '''
      {
        "L":{
            "1":1,
            "2":"2",
            "3":"3"
            },
        "M":{
            "1":1,
            "2":"2",
            "3":"3"
            }
    }
    ''')


class ProductSkuContrast(models.Model):
    product = models.OneToOneField(Product, primary_key=True, related_name='contrast',
                                      verbose_name=u'商品ID')
    contrast_detail = JSONCharMyField(max_length=10240, blank=True, default=SKU_DEFAULT, verbose_name=u'对照表详情')
    created = models.DateTimeField(null=True, auto_now_add=True, blank=True, verbose_name=u'生成日期')
    modified = models.DateTimeField(null=True, auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_items_productskucontrast'
        verbose_name = u'对照内容表'
        verbose_name_plural = u'对照内容表'

    @property
    def get_correspond_content(self):
        result_data = {}
        for k1, v1 in self.contrast_detail.items():
            temp_dict = {}
            for k2, v2 in v1.items():
                content = ContrastContent.objects.get(cid=k2)
                temp_dict[content.name] = v2
            result_data[k1] = temp_dict
        return result_data

    def __unicode__(self):
        return '<%s,%s>' % (self.product_id, self.contrast_detail)


class ContrastContent(models.Model):
    NORMAL = 'normal'
    DELETE = 'delete'
    PRODUCT_CONTRAST_STATUS = (
        (NORMAL, u'使用'),
        (DELETE, u'作废')
    )
    cid = models.CharField(max_length=32, db_index=True, verbose_name=u'对照表内容ID')
    name = models.CharField(max_length=32, verbose_name=u'对照表内容')
    sid = models.IntegerField(default=0, verbose_name=u'排列顺序')
    status = models.CharField(max_length=32, choices=PRODUCT_CONTRAST_STATUS,
                              db_index=True, default=NORMAL, verbose_name=u'状态')
    created = models.DateTimeField(null=True, auto_now_add=True, blank=True, verbose_name=u'生成日期')
    modified = models.DateTimeField(null=True, auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_items_contrastcontent'
        unique_together = ("cid", "name")
        verbose_name = u'对照内容字典'
        verbose_name_plural = u'对照内容字典'

    def __unicode__(self):
        return '<%s,%s>' % (self.cid, self.name)


class ImageWaterMark(models.Model):
    STATUSES = (
        (1, u'使用'),
        (0, u'作废')
    )
    url = models.CharField(max_length=128, verbose_name=u'图片链接')
    remark = models.TextField(blank=True, default='', verbose_name=u'备注')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(choices=STATUSES, verbose_name=u'状态')

    class Meta:
        db_table = u'image_watermark'
        verbose_name = u'图片水印'
        verbose_name_plural = u'图片水印'



class ProductSchedule(AdminModel):
    r"""
    商品排期
    """
    SCHEDULE_TYPE_CHOICES = [
        (1, u'原始排期'),
        (2, u'秒杀排期')
    ]

    STATUS_CHOICES = [
        (0, u'无效'),
        (1, u'有效')
    ]

    product = models.ForeignKey('Product', related_name='schedules', verbose_name=u'关联商品')
    onshelf_datetime = models.DateTimeField(verbose_name=u'上架时间')
    onshelf_date = models.DateField(verbose_name=u'上架日期')
    onshelf_hour = models.IntegerField(verbose_name=u'上架时间')
    offshelf_datetime = models.DateTimeField(verbose_name=u'下架时间')
    offshelf_date = models.DateField(verbose_name=u'下架日期')
    offshelf_hour = models.IntegerField(verbose_name=u'下架时间')
    schedule_type = models.SmallIntegerField(choices=SCHEDULE_TYPE_CHOICES, default=1, verbose_name=u'排期类型')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')
    sale_type = models.SmallIntegerField(choices=constants.SALE_TYPES, default=1, verbose_name=u'促销类型')

    class Meta:
        db_table = 'shop_items_schedule'
        verbose_name = u'商品上下架排期管理'
        verbose_name_plural = u'商品上下架排期管理列表'
