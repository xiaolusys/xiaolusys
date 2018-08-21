# -*- coding:utf8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
from django.conf import settings
from shopback.categorys.models import Category, CategorySaleStat
from shopback.monitor.models import SystemConfig
from shopapp.taobao import apis
from shopback.items.models import Product, ProductSku
from django.db.models import Sum

import logging

logger = logging.getLogger('django.request')


@app.task(max_retries=3)
def RecurUpdateCategoreyTask(user_id, cid):
    try:
        response = apis.taobao_itemcats_get(parent_cid=cid, tb_user_id=user_id)
        categories = response['itemcats_get_response'].get('item_cats', None)

        if categories:
            cats = categories.get('item_cat')

            for cat in cats:
                category = Category()
                for k, v in cat.iteritems():
                    hasattr(category, k) and setattr(category, k, v)
                category.save()

                if cat['is_parent']:
                    RecurUpdateCategoreyTask.delay(user_id, cat['cid'])

    except Exception, exc:

        logger.error('RecurUpdateCategoreyTask error:%s' % (exc), exc_info=True)
        if not settings.DEBUG:
            RecurUpdateCategoreyTask.retry(exc=exc, countdown=2)


@app.task(max_retries=3)
def UpdateCategoryIncrementTask():
    """增量更新类目，暂未实现！！"""
    config = SystemConfig.getconfig()
    category_updated = config.category_updated
    today_dt = datetime.datetime.now()

    day_delta = today_dt - category_updated

    response = apis.taobao_itemcats_increment_get(cids=None, type=None, days=None, tb_user_id=None)


from common.modelutils import update_model_fields


@app.task(max_retries=3)
def category_pit_num_stat():
    """
        定时任务　计算保存　分类统计中的产品坑位数量
    """
    pros = Product.objects.filter(sale_time=datetime.date.today(), status="normal").values()
    cgymods = pros.values("category", "model_id").distinct()
    dic_cgy = {}
    for cgy in cgymods:
        if dic_cgy.has_key(cgy['category']):
            dic_cgy[cgy['category']] += 1
        else:
            dic_cgy[cgy['category']] = 1
    for category, pit_num in dic_cgy.items():
        cgysta, state = CategorySaleStat.objects.get_or_create(stat_date=datetime.date.today(), category=category)
        cgysta.pit_num = pit_num
        update_model_fields(cgysta, update_fields=['pit_num'])


@app.task()
def task_category_collect_num(days=15):
    """
        days: 更新的天数
        定时任务　更新产品分类的库存数量　和　库存金额
    """
    sale_time_to = datetime.datetime.today()
    sale_time_from = sale_time_to - datetime.timedelta(days=days)
    pros = Product.objects.filter(sale_time__gte=sale_time_from,
                                  sale_time__lte=sale_time_to, status="normal")
    cgy_collects = pros.values('sale_time', 'category').annotate(total_collect=Sum('collect_num'))
    # a = [{'category': 8L, 'sale_time': datetime.date(2015, 11, 30), 'total_collect': 0},...]
    for collect in cgy_collects:
        cgysta, state = CategorySaleStat.objects.get_or_create(stat_date=collect['sale_time'],
                                                               category=collect['category'])
        cgysta.collect_num = collect['total_collect']
        # 该天该类产品
        collect_amount = 0
        pskus = ProductSku.objects.filter(product__sale_time=collect['sale_time'], product__status="normal",
                                          product__category=collect['category'])
        for psku in pskus:
            collect_amount += psku.collect_amount
        cgysta.collect_amount = collect_amount
        update_model_fields(cgysta, update_fields=['collect_num', "collect_amount"])
