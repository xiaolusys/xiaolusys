import datetime
from celery.task import task
from celery.task.sets import subtask
from search.scrawurldata import getCustomShopsPageRank
from search.models import ProductPageRank
from auth.utils import format_time
import logging

logger = logging.getLogger('period.search')

nicks = [u'\u4f18\u5c3c\u4e16\u754c\u65d7\u8230\u5e97',u'\u4f18\u5c3c\u5c0f\u5c0f\u4e16\u754c']
keywords = [u'\u7761\u888b \u513f\u7ae5 \u9632\u8e22\u88ab',u'\u5a74\u513f\u5e8a\u54c1',
           u'\u5a74\u513f\u5e8a\u4e0a\u7528\u54c1',u'\u7761\u888b \u51ac \u52a0\u539a',
           u'\u7761\u888b \u5a74\u513f \u79cb\u51ac',u'\u7761\u888b \u5927\u7ae5 \u653e\u8e22\u88ab',
           u'\u5a74\u513f \u5e8a\u54c1 \u5957',u'\u5a74\u513f\u5e8a\u56f4',
           u'\u5a74\u513f\u5e8a\u4e0a\u7528\u54c1\u5957\u4ef6',u'\u5a74\u513f\u5e8a\u54c1\u5957\u4ef6',
           u'\u5a74\u513f\u7761\u888b',u'\u5a74\u513f\u7761\u888b \u6625\u79cb',
           u'\u5a74\u513f\u7761\u888b \u51ac\u6b3e',u'\u5b9d\u5b9d\u7761\u888b']
page_nums = 6

@task()
def updateItemKeywordsPageRank():

    try:
        results = getCustomShopsPageRank(nicks,keywords,page_nums)
    except Exception,exc:
        logger.error('getCustomShopsPageRank record error', exc_info=True)
        from django.conf import settings
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=1)
        return 'scraw taobao url data error'

    created_at = datetime.datetime.now()
    month = created_at.month
    day = created_at.day
    time = format_time(created_at)

    for keyword,nicks_result in  results.iteritems():

        for nick,values in nicks_result.iteritems():

            for value in values:
                try:
                    ProductPageRank.objects.create(
                        keyword=keyword,item_id=value['item_id'],title=value['title'],user_id=value['user_id']
                        ,nick=value['nick'],month=month,day=day,time=time,rank=value['rank'])

                except Exception,exc:
                    logger.error('Create ProductPageRank record error.',exc_info=True)




  