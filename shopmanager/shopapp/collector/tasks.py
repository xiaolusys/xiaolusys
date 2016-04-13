__author__ = 'meixqhi'
import time
import datetime
from celery.task import task
from shopapp.collector.crawurldata import getTaoBaoPageRank, getTaoBaoPageRank
from shopapp.collector.models import ProductTrade, ProductPageRank
from shopback.users.models import User
from common.utils import format_time, parse_datetime, format_datetime, format_date
import logging

logger = logging.getLogger('collector.handler')

####################################### Keyword Page Rank ############################################
page_nums = 6
PRODUCT_TRADE_RANK_BELOW = 10


def saveKeywordPageRank(keyword, month, day, time, created):
    try:
        results = getTaoBaoPageRank(keyword, page_nums)
    except Exception, exc:
        logger.error('getCustomShopsPageRank record error:%s' % exc, exc_info=True)
        return

    for value in results:
        try:
            ProductPageRank.objects.create(
                keyword=keyword, item_id=value['item_id'], title=value['title'], user_id=value['user_id']
                , nick=value['nick'], month=month, day=day, time=time, created=created, rank=value['rank'])

        except Exception, exc:
            logger.error('Create ProductPageRank or Item record error:%s' % exc, exc_info=True)


@task()
def updateItemKeywordsPageRank():
    users = User.objects.all()

    keywords = set()
    for user in users:
        keys = user.craw_keywords
        keys_tmp = keys.split(',') if keys else []
        keywords = keywords.union(keys_tmp)

    created_at = datetime.datetime.now()
    month = created_at.month
    day = created_at.day
    time = format_time(created_at)

    created = created_at.strftime("%Y-%m-%d %H:%M")  # +":00"

    for keyword in keywords:
        saveKeywordPageRank(keyword, month, day, time, created)


@task()
def deletePageRankRecordTask(remain_days):
    remain_days = remain_days if remain_days > 7 else 7

    remain_days_before = format_date(datetime.datetime.now() - datetime.timedelta(remain_days, 0, 0))

    ProductPageRank.objects.filter(created__lt=remain_days_before).delete()


#################################### Trade Rank Task ############################################



@task()
def updateSellerAllTradesTask(seller_id, seller_nick, item_ids, s_dt_f, s_dt_t):
    items = ProductPageRank.objects.filter \
        (user_id=seller_id, created__gte=s_dt_f, created__lte=s_dt_t).values('item_id').distinct('item_id')

    if not seller_nick:
        seller = ProductPageRank.objects.filter(user_id=seller_id)
        if seller.count() == 0:
            logger.error('the seller id %s is not in the product_pagerank table.' % seller_id)
            return None
        seller_nick = seller[0].nick

    if item_ids:
        item_ids = item_ids.union([i['item_id'] for i in items])
    else:
        item_ids = [i['item_id'] for i in items]

    for item_id in item_ids:
        try:
            trades = crawTaoBaoTradePage(item_id, seller_id, s_dt_f, s_dt_t)
            prod_trade = ProductTrade()
            prod_trade.item_id = item_id
            prod_trade.user_id = seller_id

            for trade in trades:
                try:
                    ProductTrade.objects.get(item_id=item_id, trade_id=trade['trade_id'], user_id=seller_id)
                except ProductTrade.DoesNotExist:
                    prod_trade.id = None

                    prod_trade.nick = seller_nick
                    prod_trade.trade_id = trade['trade_id']
                    prod_trade.num = trade['num']
                    prod_trade.trade_at = trade['trade_at']
                    prod_trade.state = trade['state']
                    prod_trade.price = int(trade['num']) * float(trade['price'])
                    dt = parse_datetime(trade['trade_at'])
                    prod_trade.year = dt.year
                    prod_trade.month = dt.month
                    prod_trade.day = dt.day
                    prod_trade.hour = dt.strftime("%H")
                    prod_trade.week = time.gmtime(time.mktime(dt.timetuple()))[7] / 7 + 1

                    prod_trade.save()
        except Exception, exc:
            logger.error('updateSellerAllTradesTask  error:%s' % exc, exc_info=True)


@task()
def updateProductTradeBySellerTask():
    t = time.time() - 24 * 60 * 60
    dt = datetime.datetime.fromtimestamp(t)

    year = dt.year
    month = dt.month
    day = dt.day

    s_dt_f = format_datetime(datetime.datetime(year, month, day, 0, 0, 0))
    s_dt_t = format_datetime(datetime.datetime(year, month, day, 23, 59, 59))

    users = User.objects.all()
    seller_map_item = {}
    seller_map_nick = {}
    rex = re.compile('(?P<user_nick>\W+)(-(?P<user_id>\w*))?(\((?P<item_ids>[\w,]*)\))?$')

    for user in users:
        seller_nicks = user.craw_trade_seller_nicks
        seller_nicks = seller_nicks.split('|') if seller_nicks else []

        for nick_item in seller_nicks:

            if not nick_item:
                continue

            m = rex.search(nick_item)
            user_nick = m.group('user_nick')
            user_id = m.group('user_id')
            item_ids = m.group('item_ids')

            if not user_id and user_nick:
                prodrank = ProductPageRank.objects.filter(nick=user_nick)
                if prodrank.count() > 0:
                    user_id = prodrank[0].user_id

            if not user_id:
                continue

            user_id = str(user_id)
            item_ids = item_ids.split(',') if item_ids else []

            s_set = seller_map_item.get(user_id, set())
            seller_map_item[user_id] = s_set.union(item_ids)
            seller_map_nick[user_id] = user_nick

    rankset = ProductPageRank.objects.filter(rank__lte=PRODUCT_TRADE_RANK_BELOW
                                             , created__gte=s_dt_f, created__lte=s_dt_t).values('user_id').distinct(
        'user_id')

    for userid in rankset:
        user_id = str(userid['user_id'])
        if not seller_map_item.has_key(user_id):
            seller_map_item[user_id] = None

    for seller_id, item_ids in seller_map_item.iteritems():
        item_ids = item_ids.discard('') if item_ids else None
        seller_nick = seller_map_nick.get(seller_id, None)
        subtask(updateSellerAllTradesTask).delay(seller_id, seller_nick, item_ids, s_dt_f, s_dt_t)
