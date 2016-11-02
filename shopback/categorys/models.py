# -*- coding:utf8 -*-
from django.db import models

from shopback import paramconfig as pcfg
from auth import apis

from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)

CAT_STATUS = (
    (pcfg.NORMAL, u'正常'),
    (pcfg.DELETE, u'删除'),
)

class Category(BaseModel):
    NORMAL = pcfg.NORMAL
    DELETE = pcfg.DELETE

    cid = models.IntegerField(primary_key=True, verbose_name=u'类目ID')
    parent_cid = models.IntegerField(null=True, db_index=True , verbose_name=u'父类目ID')

    name = models.CharField(max_length=32, blank=True, verbose_name=u'类目名')
    grade = models.IntegerField(default=0, db_index=True, verbose_name=u'类目等级')

    is_parent = models.BooleanField(default=True, verbose_name=u'父类目')
    status = models.CharField(max_length=7, choices=CAT_STATUS, default=NORMAL, verbose_name=u'状态')
    sort_order = models.IntegerField(null=True, verbose_name=u'权值')

    class Meta:
        db_table = 'shop_categorys_category'
        app_label = 'categorys'
        verbose_name = u'淘宝类目'
        verbose_name_plural = u'淘宝类目列表'

    def __unicode__(self):
        return self.name

    @classmethod
    def get_or_create(cls, user_id, cat_id):
        category, state = Category.objects.get_or_create(cid=cat_id)
        if state:
            try:
                reponse = apis.taobao_itemcats_get(cids=cat_id, tb_user_id=user_id)
                cat_dict = reponse['itemcats_get_response']['item_cats']['item_cat'][0]
                for key, value in cat_dict.iteritems():
                    hasattr(category, key) and setattr(category, key, value)
                category.save()
            except Exception, exc:
                logger.error('淘宝后台更新该类目(cat_id:%s)出错' % str(cat_id), exc_info=True)

        return category


class ProductCategory(BaseModel):

    NORMAL = pcfg.NORMAL
    DELETE = pcfg.DELETE

    cid  = models.AutoField(primary_key=True, verbose_name=u'类目ID')
    # cid = models.IntegerField(unique=True,null=False, verbose_name=u'类目ID')
    parent_cid = models.IntegerField(null=False, verbose_name=u'父类目ID')
    name = models.CharField(max_length=32, blank=True, verbose_name=u'类目名')

    grade = models.IntegerField(default=0, db_index=True, verbose_name=u'类目级别')
    is_parent = models.BooleanField(default=True, verbose_name=u'有子类目')
    status = models.CharField(max_length=7, choices=CAT_STATUS, default=pcfg.NORMAL, verbose_name=u'状态')
    sort_order = models.IntegerField(default=0, db_index=True, verbose_name=u'权值')

    class Meta:
        db_table = 'shop_categorys_productcategory'
        app_label = 'categorys'
        verbose_name = u'产品类目'
        verbose_name_plural = u'产品类目列表'

    def __unicode__(self):

        if not self.parent_cid:
            return unicode(self.name)
        try:
            p_cat = self.__class__.objects.get(cid=self.parent_cid)
        except:
            p_cat = u'--'
        return u'%s / %s' % (p_cat, self.name)


class CategorySaleStat(models.Model):
    """
        销售分类统计
        上架日期: 产品的上架日期
        产品类别: 产品类别中所属类别（类别id）
        销售金额: 上架日期上架对应类别产品的的销售金额（包含退款金额）
        销售数量: 上架日期上架对应类别的产品的销售数量（包含退款数量）
        坑位数量: 上架日期对应类别的坑位数量
        库存数量: 上架日期对应类别的库存数量
        库存金额: 上架日期对应类别的库存金额
        进货数量: 上架日期对应类别的大货进货数量
        进货金额: 上架日期对应类别的大货进货金额
        退款数量: 上架日期对应类别的退款数量
        退款金额: 上架日期对应类别的退款金额
    """
    stat_date = models.DateField(db_index=True, verbose_name="上架日期")
    category = models.IntegerField(default=0, db_index=True, verbose_name="产品类别")
    sale_amount = models.FloatField(default=0.0, verbose_name="销售金额")
    sale_num = models.IntegerField(default=0, verbose_name="销售数量")
    pit_num = models.IntegerField(default=0, verbose_name="坑位数量")
    collect_num = models.IntegerField(default=0, verbose_name="库存数量")
    collect_amount = models.FloatField(default=0.0, verbose_name="库存金额")
    stock_num = models.IntegerField(default=0, verbose_name="进货数量")
    stock_amount = models.FloatField(default=0.0, verbose_name="进货金额")
    refund_num = models.IntegerField(default=0, verbose_name="退款数量")
    refund_amount = models.FloatField(default=0.0, verbose_name="退款金额")
    created = models.DateTimeField(db_index=True, auto_now_add=True, verbose_name="创建时间")
    modified = models.DateTimeField(auto_now=True, verbose_name="修改时间")

    class Meta:
        db_table = "shop_category_stat"
        app_label = 'categorys'
        verbose_name = "产品分类统计"
        verbose_name_plural = "产品分类统计列表"
        permissions = [("shop_category_stat", "产品分类统计"), ]

    def __unicode__(self):
        try:
            category = ProductCategory.objects.get(cid=self.category)
            category_full_name = category.__unicode__()
        except ProductCategory.DoesNotExist:
            category_full_name = "NoCategory"
        return "%s_%s" % (self.stat_date, category_full_name)

    @property
    def category_display(self):
        try:
            category = ProductCategory.objects.get(cid=self.category)
            category_full_name = category.__unicode__()
        except ProductCategory.DoesNotExist:
            category_full_name = "NoCategory"
        return "%s" % category_full_name
