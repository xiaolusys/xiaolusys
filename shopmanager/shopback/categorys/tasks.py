from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from shopback.categorys.models import Category
from auth import apis

import logging

logger = logging.getLogger('recurupdate.categorey')

@task(max_retry=3)
def RecurUpdateCategoreyTask(top_session,cid):
    try:
        response = apis.taobao_itemcats_get(parent_cid=cid,session=top_session)

        categories = response['itemcats_get_response'].get('item_cats',None)

        if categories:

            cats = categories.get('item_cat')
            category = Category()
            print len(cats)
            for cat in cats:

                for k,v in cat.iteritems():
                    hasattr(category,k) and setattr(category,k,v)
                category.save()

                if cat['is_parent']:
                    subtask(RecurUpdateCategoreyTask).delay(top_session,cat['cid'])
    except Exception,exc:

        logger.error('RecurUpdateCategoreyTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            saveUserHourlyOrders.retry(exc=exc,countdown=2)