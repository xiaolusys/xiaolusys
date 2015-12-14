#-*- coding:utf8 -*-
import datetime
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from shopback.categorys.models import Category, CategorySaleStat
from shopback.monitor.models import SystemConfig
from auth import apis
from shopback.items.models import Product

import logging

logger = logging.getLogger('django.request')

@task(max_retry=3)
def RecurUpdateCategoreyTask(user_id,cid):
    try:
        response = apis.taobao_itemcats_get(parent_cid=cid,tb_user_id=user_id)
        categories = response['itemcats_get_response'].get('item_cats',None)
        
        if categories:
            cats = categories.get('item_cat')

            for cat in cats:
                category = Category()
                for k,v in cat.iteritems():
                    hasattr(category,k) and setattr(category,k,v)
                category.save()

                if cat['is_parent']:
                    subtask(RecurUpdateCategoreyTask).delay(user_id,cat['cid'])
                
    except Exception,exc:

        logger.error('RecurUpdateCategoreyTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            RecurUpdateCategoreyTask.retry(exc=exc,countdown=2)
            

@task(max_retry=3)
def UpdateCategoryIncrementTask():
    """增量更新类目，暂未实现！！"""
    config    = SystemConfig.getconfig()
    category_updated = config.category_updated
    today_dt  = datetime.datetime.now()
    
    day_delta = today_dt - category_updated
    
    response = apis.taobao_itemcats_increment_get(cids=None,type=None,days=None,tb_user_id=None)


from common.modelutils import update_model_fields


@task(max_retry=3)
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
