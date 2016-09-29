# coding: utf-8

import hashlib

from django.db import models
from django.db.models.signals import pre_save, post_save
from django.forms.models import model_to_dict
from django.core.cache import cache

from shopback.archives.models import DepositeDistrict

import logging
logger = logging.getLogger(__name__)


class ProductLocation(models.Model):
    """ 库存商品库位信息 """
    product_id = models.IntegerField(db_index=True, verbose_name='商品ID')
    sku_id = models.IntegerField(db_index=True, blank=True, null=True, verbose_name='规格ID')

    outer_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='商品编码')
    name = models.CharField(max_length=64, null=False, blank=True, verbose_name='商品名称')

    outer_sku_id = models.CharField(max_length=32, null=False, blank=True, verbose_name='规格编码')
    properties_name = models.CharField(max_length=64, null=False, blank=True, verbose_name='规格属性')

    district = models.ForeignKey(DepositeDistrict,
                                 related_name='product_locations',
                                 verbose_name='关联库位')

    @staticmethod
    def set_product_district(product, district):
        ProductLocation.objects.filter(product_id=product.id).exclude(district=district).delete()
        res = []
        for sku in product.prod_skus.all():
            p, state = ProductLocation.objects.get_or_create(product_id=product.id,
                            sku_id=sku.id,
                            outer_id=product.outer_id,
                            outer_sku_id=product.outer_id,
                            name=product.title(),
                            properties_name=sku.properties_name,
                            district=district)
            res.append(p)
        return res

    class Meta:
        db_table = 'shop_items_productlocation'
        unique_together = ("product_id", "sku_id", "district")
        app_label = 'items'
        verbose_name = u'商品库位'
        verbose_name_plural = u'商品库位列表'



class ProductScanStorage(models.Model):
    DELETE = -1
    PASS = 1
    WAIT = 0
    SCAN_STATUS = (
        (DELETE, u'已删除'),
        (WAIT, u'未入库'),
        (PASS, u'已入库'),
    )

    product_id = models.IntegerField(null=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(null=True, verbose_name=u'规格ID')

    qc_code = models.CharField(max_length=32, blank=True, verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32, blank=True, verbose_name=u'规格编码')
    barcode = models.CharField(max_length=32, blank=True, verbose_name=u'商品条码')

    product_name = models.CharField(max_length=32, blank=True, verbose_name=u'商品名称')
    sku_name = models.CharField(max_length=32, blank=True, verbose_name=u'规格名称')

    scan_num = models.IntegerField(null=False, default=0, verbose_name=u'扫描次数')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    wave_no = models.CharField(max_length=32, blank=True, verbose_name=u'批次号')
    status = models.IntegerField(null=False, default=WAIT, choices=SCAN_STATUS, verbose_name=u'状态')

    class Meta:
        db_table = 'shop_items_scan'
        unique_together = ("wave_no", "product_id", "sku_id")
        app_label = 'items'
        verbose_name = u'扫描入库商品'
        verbose_name_plural = u'扫描入库商品列表'

    def __unicode__(self):
        return '<%s,%s,%d>' % (self.id,
                               self.barcode,
                               self.scan_num)


from core.fields import JSONCharMyField

SKU_DEFAULT = {
    "L": {
        "1": 1,
        "2": "2",
        "3": "3"
    },
    "M": {
        "1": 1,
        "2": "2",
        "3": "3"
    }
}


class ProductSkuContrast(models.Model):
    """ 商品规格尺寸参数 """
    product = models.OneToOneField('items.Product', primary_key=True, related_name='contrast',
                                   verbose_name=u'商品ID')
    contrast_detail = JSONCharMyField(max_length=10240, blank=True, default=SKU_DEFAULT, verbose_name=u'对照表详情')
    created = models.DateTimeField(null=True, auto_now_add=True, blank=True, verbose_name=u'生成日期')
    modified = models.DateTimeField(null=True, auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_items_productskucontrast'
        app_label = 'items'
        verbose_name = u'对照内容表'
        verbose_name_plural = u'对照内容表'

    @classmethod
    def format_contrast(cls, origin_contrast):
        result_data = {}
        constants_maps = ContrastContent.contrast_maps()
        for k1, v1 in origin_contrast.items():
            temp_dict = {}
            for k2, v2 in v1.items():
                content = constants_maps.get(k2, k2)
                temp_dict[content] = v2
            result_data[k1] = temp_dict
        return result_data

    @property
    def get_correspond_content(self):
        return ProductSkuContrast.format_contrast(self.contrast_detail)

    def __unicode__(self):
        return '<%s,%s>' % (self.product_id, self.contrast_detail)


def invalid_productsku_contrast_cache(sender, instance, created, **kwargs):
    from flashsale.pay.models import ModelProduct
    if hasattr(ModelProduct, 'API_CACHE_KEY_TPL'):
        logger.info('invalid_productsku_contrast_cache invalid: %s'% instance.product.model_id)
        cache.delete(ModelProduct.API_CACHE_KEY_TPL.format(instance.product.model_id))

post_save.connect(invalid_productsku_contrast_cache,
                  sender=ProductSkuContrast,
                  dispatch_uid='post_save_invalid_productsku_contrast_cache')

def default_contrast_cid():
    max_constrast = ContrastContent.objects.order_by('-id').first()
    if max_constrast:
        return str( max_constrast.id + 1)
    return '1'

def gen_contrast_cache_key(key_name):
    return hashlib.sha1('%s.%s'%(__name__, key_name)).hexdigest()

class ContrastContent(models.Model):
    NORMAL = 'normal'
    DELETE = 'delete'
    PRODUCT_CONTRAST_STATUS = (
        (NORMAL, u'使用'),
        (DELETE, u'作废')
    )
    cid = models.CharField(max_length=32, default=default_contrast_cid, db_index=True, verbose_name=u'对照表内容ID')
    name = models.CharField(max_length=32, unique=True, verbose_name=u'对照表内容')
    sid = models.IntegerField(default=0, verbose_name=u'排列顺序')
    status = models.CharField(max_length=32, choices=PRODUCT_CONTRAST_STATUS,
                              db_index=True, default=NORMAL, verbose_name=u'状态')
    created = models.DateTimeField(null=True, auto_now_add=True, blank=True, verbose_name=u'生成日期')
    modified = models.DateTimeField(null=True, auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_items_contrastcontent'
        unique_together = ("cid", "name")
        app_label = 'items'
        verbose_name = u'对照内容字典'
        verbose_name_plural = u'对照内容字典'

    def __unicode__(self):
        return '<%s,%s>' % (self.cid, self.name)

    @classmethod
    def contrast_maps(cls):
        cache_key  = gen_contrast_cache_key(cls.__name__)
        cache_contrast = cache.get(cache_key)
        if not cache_contrast:
            contrasts = cls.objects.filter(status=cls.NORMAL).values_list('cid', 'name')
            cache_contrast = dict(contrasts)
            cache.set(cache_key, cache_contrast, 7 * 24 * 3600)
            logger.warn('contrast dictionary cache not hit: key=%s'% cache_key)
        return cache_contrast


def invalid_contrast_maps_cache(sender, instance, created, **kwargs):
    cache_key = gen_contrast_cache_key(instance.__class__.__name__)
    cache.delete(cache_key)

post_save.connect(invalid_contrast_maps_cache,
                  sender=ContrastContent,
                  dispatch_uid='post_save_invalid_contrast_maps_cache')


class ImageWaterMark(models.Model):

    NORMAL   = 1
    CANCELED = 0
    STATUSES = (
        (NORMAL, u'使用'),
        (CANCELED, u'作废')
    )
    url = models.CharField(max_length=128, verbose_name=u'图片链接')
    remark = models.TextField(blank=True, default='', verbose_name=u'备注')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(choices=STATUSES, verbose_name=u'状态')

    class Meta:
        db_table = u'image_watermark'
        app_label = 'items'
        verbose_name = u'图片水印'
        verbose_name_plural = u'图片水印'
