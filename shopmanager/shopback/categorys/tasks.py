from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from shopback.categorys.models import Category
from shopback.monitor.models import SystemConfig
from auth import apis

import logging

logger = logging.getLogger('categoreys.handler')

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
    
    config = SystemConfig.getconfig()
    
    category_updated = config.category_updated
    