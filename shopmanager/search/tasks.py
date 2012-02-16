import datetime
from celery.task import task
from celery.task.sets import subtask
from search.scrawurldata import getCustomShopsPageRank
from search.models import ProductPageRank
import logging

logger = logging.get_Logger('period.search')

nicks = ['\xe4\xbc\x98\xe5\xb0\xbc\xe4\xb8\x96\xe7\x95\x8c\xe6\x97\x97\xe8\x88\xb0\xe5\xba\x97'
         ,'\xe4\xbc\x98\xe5\xb0\xbc\xe5\xb0\x8f\xe5\xb0\x8f\xe4\xb8\x96\xe7\x95\x8c']
keywords = ['\xe7\x9d\xa1\xe8\xa2\x8b \xe5\x84\xbf\xe7\xab\xa5 \xe9\x98\xb2\xe8\xb8\xa2\xe8\xa2\xab',]
page_nums = 6

@task()
def updateItemKeywordsPageRank():

    try:
        results = getCustomShopsPageRank(nicks,keywords,page_nums)
    except Exception,exc:
        logger.error('getCustomShopsPageRank record error', exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=1)

    search_datetime = datetime.datetime.now()

    for keyword,nicks_result in  results.iteritems():

        for nick,values in nicks_result.iteritems():
            try:
                ProductPageRank.objects.create(
                    keyword=keyword,item_id=values['item_id'],title=values['title'],user_id=values['user_id']
                    ,nick=values['nick'],search_datetime=search_datetime,rank=values['rank'])

            except Exception,exc:
                logger.error('Create ProductPageRank record error.',exc_info=True)




  