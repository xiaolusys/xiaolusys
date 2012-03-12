import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from search.crawurldata import getTaoBaoPageRank,crawTaoBaoTradePage
from search.models import ProductPageRank,ProductTrade
from shopback.users.models import User
from auth.utils import format_time,parse_datetime,format_datetime
import logging

logger = logging.getLogger('period.search')


page_nums = 6

#@task()
def saveKeywordPageRank(keyword,month,day,time,created):

    try:
        results = getTaoBaoPageRank(keyword,page_nums)
    except Exception,exc:
        logger.error('getCustomShopsPageRank record error:%s'%exc, exc_info=True)
#        if not settings.DEBUG:
#            create_comment.retry(exc=exc,countdown=1)
        return 'craw taobao url data error'

    for value in results:
        try:
            ProductPageRank.objects.create(
                keyword=keyword,item_id=value['item_id'],title=value['title'],user_id=value['user_id']
                ,nick=value['nick'],month=month,day=day,time=time,created=created,rank=value['rank'])

        except Exception,exc:
            logger.error('Create ProductPageRank record error:%s'%exc,exc_info=True)



@task()
def updateItemKeywordsPageRank():

    users = User.objects.all()

    keywords = set()
    for user in users:
        keys = user.craw_keywords
        keywords.update(keys.split(',') if keys else [])

    created_at = datetime.datetime.now()
    month = created_at.month
    day = created_at.day
    time = format_time(created_at)

    created = created_at.strftime("%Y-%m-%d %H:%M")

    for keyword in keywords:

        saveKeywordPageRank(keyword,month,day,time,created)
        #subtask(saveKeywordPageRank).delay(keyword,month,day,time,created)



@task()
def updateSellerAllTradesTask(seller_id,s_dt_f,s_dt_t):

    items = ProductPageRank.objects.filter\
            (user_id=seller_id,created__gte=s_dt_f,created__lte=s_dt_t).values('item_id').distinct('item_id')
    seller = ProductPageRank.objects.filter(user_id=seller_id)[0]
    for item in items:
        item_id = item['item_id']
        try:
            trades = crawTaoBaoTradePage(item_id,seller_id,s_dt_f,s_dt_t)
            prod_trade = ProductTrade()
            prod_trade.item_id = item_id
            prod_trade.user_id = seller_id

            for trade in trades:
                try:
                    ProductTrade.objects.get(item_id=item_id,trade_id=trade['trade_id'],user_id=seller_id)
                except ProductTrade.DoesNotExist:
                    prod_trade.id = None

                    prod_trade.nick = seller.nick
                    prod_trade.trade_id = trade['trade_id']
                    prod_trade.num = trade['num']
                    prod_trade.trade_at = trade['trade_at']
                    prod_trade.state = trade['state']
                    prod_trade.price = int(trade['num'])*float(trade['price'])
                    dt = parse_datetime(trade['trade_at'])
                    prod_trade.year = dt.year
                    prod_trade.month = dt.month
                    prod_trade.day = dt.day
                    prod_trade.hour = dt.strftime("%H")
                    prod_trade.week = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1

                    prod_trade.save()
        except Exception,exc:
            logger.error('updateSellerAllTradesTask  error:%s'%exc,exc_info=True)




@task()
def updateProductTradeBySellerTask():

    t = time.time()-24*60*60
    dt = datetime.datetime.fromtimestamp(t)

    year = dt.year
    month = dt.month
    day = dt.day

    s_dt_f = format_datetime(datetime.datetime(year,month,day,0,0,0))
    s_dt_t = format_datetime(datetime.datetime(year,month,day,23,59,59))

    users = User.objects.all()
    craw_trade_seller_ids = set()
    craw_trade_nicks      = set()

    for user in users:
        seller_nicks = user.craw_trade_seller_nicks
        seller_nicks = seller_nicks.split(',') if seller_nicks else []
        craw_trade_nicks.update(seller_nicks)

    rank_sellers = ProductPageRank.objects.filter(nick__in=craw_trade_nicks)\
        .values_list('user_id').distinct('user_id')

    craw_trade_seller_ids.update([n[0] for n in rank_sellers])

    rankset = ProductPageRank.objects.filter(rank__lte=settings.PRODUCT_TRADE_RANK_BELOW
            ,created__gte=s_dt_f,created__lte=s_dt_t).values_list('user_id').distinct('user_id')

    craw_trade_seller_ids.update([n[0] for n in rankset])

    for seller_id in craw_trade_seller_ids:

        subtask(updateSellerAllTradesTask).delay(seller_id,s_dt_f,s_dt_t)




  