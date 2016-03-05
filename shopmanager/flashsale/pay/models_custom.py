#-*- coding:utf-8 -*-
import json
from django.db import models
from django.db.models import F

from common.utils import update_model_fields
from core.fields import JSONCharMyField
from .base import PayBaseModel

from shopback.items.models import Product
from . signals import signal_record_supplier_models
from shopback import paramconfig as pcfg

class Productdetail(PayBaseModel):

    WASH_INSTRUCTION = '''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''
    OUT_PERCENT  = 0 #未设置代理返利比例
    ZERO_PERCENT = -1
    THREE_PERCENT = 3
    FIVE_PERCENT  = 5
    TEN_PERCENT  = 10
    TWENTY_PERCENT = 20
    THIRTY_PERCENT = 30

    WEIGHT_CHOICE = ((i,i) for i in range(1,101)[::-1])
    DISCOUNT_CHOICE = ((i,i) for i in range(1,101)[::-1])
    BUY_LIMIT_CHOICE = ((i,i) for i in range(1,21))

    REBETA_CHOICES = ((OUT_PERCENT,u'未设置返利'),
                     (ZERO_PERCENT,u'该商品不返利'),
                     (THREE_PERCENT,u'返利百分之3'),
                     (FIVE_PERCENT,u'返利百分之5'),
                     (TEN_PERCENT,u'返利百分之10'),
                     (TWENTY_PERCENT,u'返利百分之20'),
                     (THIRTY_PERCENT,u'返利百分之30'),)

    product  = models.OneToOneField(Product, primary_key=True,
                                    related_name='details',verbose_name=u'库存商品')

    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')

    mama_discount  = models.IntegerField(default=100, choices=DISCOUNT_CHOICE, verbose_name=u'妈妈折扣')
    is_recommend = models.BooleanField(db_index=True,default=False,verbose_name=u'专区推荐')
    is_seckill   = models.BooleanField(db_index=True,default=False, verbose_name=u'是否秒杀')
    is_sale      = models.BooleanField(db_index=True,default=False,verbose_name=u'特价商品')
    order_weight = models.IntegerField(db_index=True,default=8,choices=WEIGHT_CHOICE,verbose_name=u'权值')
    buy_limit    = models.BooleanField(db_index=True,default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,choices=BUY_LIMIT_CHOICE,verbose_name=u'限购数量')

    material = models.CharField(max_length=64, blank=True, verbose_name=u'商品材质')
    color    = models.CharField(max_length=64, blank=True, verbose_name=u'可选颜色')
    wash_instructions = models.TextField(default=WASH_INSTRUCTION, blank=True, verbose_name=u'洗涤说明')
    note = models.CharField(max_length=256, blank=True, verbose_name=u'备注')
    mama_rebeta = models.IntegerField(default=OUT_PERCENT, choices=REBETA_CHOICES, db_index=True, verbose_name=u'代理返利')

    rebeta_scheme_id = models.IntegerField(default=0,verbose_name=u'返利计划')

    class Meta:
        db_table = 'flashsale_productdetail'
        verbose_name=u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'

    def __unicode__(self):
        return '<%s,%s>'%(self.product.outer_id,self.product.name)

    def mama_rebeta_rate(self):
        if self.mama_rebeta == self.ZERO_PERCENT:
            return 0.0
        if self.mama_rebeta == self.OUT_PERCENT:
            return None
        rate = self.mama_rebeta / 100.0
        assert rate >= 0 and rate <=1
        return rate

    def head_images(self):
        return self.head_imgs.split()

    def content_images(self):
        return self.content_imgs.split()


class ModelProduct(PayBaseModel):

    NORMAL = '0'
    DELETE = '1'
    STATUS_CHOICES = ((NORMAL,u'正常'),
                      (DELETE,u'作废'))

    name       = models.CharField(max_length=64,db_index=True,verbose_name=u'款式名称')

    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')

    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')

    buy_limit    = models.BooleanField(default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,verbose_name=u'限购数量')

    sale_time    = models.DateField(null=True,blank=True,db_index=True,verbose_name=u'上架日期')

    status       = models.CharField(max_length=16,db_index=True,
                                    choices=STATUS_CHOICES,
                                    default=NORMAL,verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_modelproduct'
        unique_together = ("id", "name")
        verbose_name=u'特卖商品/款式'
        verbose_name_plural = u'特卖商品/款式列表'
        permissions = [
            ("change_name_permission", u"修改名字"),
        ]

    def __unicode__(self):
        return '<%s,%s>'%(self.id,self.name)

    def head_img(self):
        return self.head_imgs and self.head_imgs.split()[0] or ''

    head_img_url = property(head_img)

    def is_single_spec(self):
        if self.id <= 0:
            return True
        products = Product.objects.filter(model_id=self.id,status=Product.NORMAL)
        if products.count() > 1:
            return False
        return True

    def is_sale_out(self):
        all_sale_out = True
        products = Product.objects.filter(model_id=self.id,status=Product.NORMAL)
        for product in products:
            all_sale_out &= product.is_sale_out()
        return all_sale_out

    def item_product(self):
        pros = Product.objects.filter(model_id=self.id, status=pcfg.NORMAL)
        if pros.exists():
            pro = pros[0]
            return pro
        else:
            return None

    def content_images(self):
        return self.content_imgs.split()

def create_Model_Product(sender, obj, **kwargs):
    pro = obj.item_product()
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(create_Model_Product, sender=ModelProduct)


class GoodShelf(PayBaseModel):

    DEFAULT_WEN_POSTER = [
      {
        "subject":['2折起', '小鹿美美  女装专场'],
        "item_link":"http://m.xiaolumeimei.com/nvzhuang.html",
        "app_link":"app:/",
        "pic_link":""
      }
    ]


    DEFAULT_CHD_POSTER = [
      {
        "subject":['2折起', '小鹿美美  童装专场'],
        "item_link":"http://m.xiaolumeimei.com/chaotong.html",
        "app_link":"app:/",
        "pic_link":""
      }
    ]

    title = models.CharField(max_length=32,db_index=True,blank=True, verbose_name=u'海报名称')

    wem_posters   = JSONCharMyField(max_length=10240, blank=True,
                                    default=json.dumps(DEFAULT_WEN_POSTER,indent=2),
                                    verbose_name=u'女装海报')
    chd_posters   = JSONCharMyField(max_length=10240, blank=True,
                                    default=json.dumps(DEFAULT_CHD_POSTER,indent=2),
                                    verbose_name=u'童装海报')

    is_active    = models.BooleanField(default=True,verbose_name=u'上线')
    active_time  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'上线日期')


    class Meta:
        db_table = 'flashsale_goodshelf'
        verbose_name=u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'

    def __unicode__(self):
        return u'<%s,%s>'%(self.id, self.title)

    def get_activity(self):
        return ActivityEntry.get_default_activity()


class ActivityEntry(PayBaseModel):
    """ 商城活动入口 """
    title = models.CharField(max_length=32,db_index=True,blank=True, verbose_name=u'活动名称')

    act_desc = models.TextField(max_length=512, blank=True, verbose_name=u'活动描述')
    act_img  = models.CharField(max_length=256, blank=True, verbose_name=u'活动图片')
    act_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动网页链接')
    mask_link = models.CharField(max_length=256, blank=True, verbose_name=u'遮罩图片')
    act_applink = models.CharField(max_length=256, blank=True, verbose_name=u'活动APP协议')

    login_required = models.BooleanField(default=False,verbose_name=u'需要登陆')
    start_time  = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time    = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    is_active   = models.BooleanField(default=True,verbose_name=u'上线')

    class Meta:
        db_table = 'flashsale_activity_entry'
        verbose_name=u'特卖/商城活动入口'
        verbose_name_plural = u'特卖/商城活动入口'

    def __unicode__(self):
        return u'<%s,%s>'%(self.id, self.title)

    @classmethod
    def get_default_activity(cls):
        acts = cls.objects.filter(is_active=True).order_by('-modified')
        if acts.exists():
            return acts[0]
        return None
