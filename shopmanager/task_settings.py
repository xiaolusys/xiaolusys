# encoding:utf-8
import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

EXECUTE_INTERVAL_TIME = 5*60

EXECUTE_RANGE_TIME = 3*60

UPDATE_ITEM_NUM_INTERVAL = 2*60

UPDATE_UNPAY_ORDER_INTERVAL = 3*60

TAOBAO_PAGE_SIZE = 100              #the page_size of  per request

PRODUCT_TRADE_RANK_BELOW = 10

MAX_REQUEST_ERROR_TIMES = 15

API_REQUEST_INTERVAL_TIME = 10      #(seconds)
API_TIME_OUT_SLEEP = 60             #(seconds)
API_OVER_LIMIT_SLEEP = 180          #(seconds)

####### gen trade amount file config #######
GEN_AMOUNT_FILE_MIN_DAYS = 8

from celery.schedules import crontab


SYNC_MODEL_SCHEDULE = {
    'runs-every-hours':{
        'task':'shopback.orders.tasks.updateAllUserDuringOrders',
        'schedule':crontab(minute="0,30"),
        'args':(0,)
    },
    'runs-every-day-b':{
        'task':'shopback.orders.tasks.updateAllUserDailyIncrementOrders',
        'schedule':crontab(minute="0",hour="0"),
        'args':(),
    },
    'runs-every-day-e':{
        'task':'shopback.orders.tasks.updateMonthTradeXlsFileTask',
        'schedule':crontab(minute="0",hour="1"),
        'args':()
    },

    'runs-every-weeks-b':{
        'task':'shopback.orders.tasks.updateAllUserOrdersAmountTask',
        'schedule':crontab(minute="0",hour="1",day_of_week="mon"),
        'args':(7,)
    },
    'runs-every-weeks-c':{
        'task':'shopback.items.tasks.updateUserItemsTask',
        'schedule':crontab(minute="0",hour="1",day_of_week='tue'),
        'args':()
    },
    'runs-every-weeks-d':{
        'task':'shopback.items.tasks.updateAllUserItemsEntityTask',
        'schedule':crontab(minute="0",hour="2",day_of_week='tue'),
        'args':()
    }, #
}


SHOP_APP_SCHEDULE = {
    'runs-every-10-minutes':{
        'task':'shopapp.autolist.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/5'),
        'args':(),
    },
    'runs-every-30-minutes-a':{
        'task':'shopapp.search.tasks.updateItemKeywordsPageRank',
        'schedule':crontab(minute="0,30",hour=','.join([str(i) for i in range(7,24)])),
        'args':()
    },
    'runs-every-day-a':{
        'task':'shopapp.syncnum.tasks.updateAllItemNumTask',
        'schedule':crontab(minute="0",hour="0"),
        'args':(),
    },
    'runs-every-day-d':{
        'task':'shopapp.search.tasks.deletePageRankRecordTask',
        'schedule':crontab(minute="0",hour="1"),
        'args':(30,)
    },

#    'runs-every-day-e':{
#        'task':'search.tasks.updateProductTradeBySellerTask',
#        'schedule':crontab(minute="0",hour="1"),
#        'args':()
#    },
}


CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE.update(SYNC_MODEL_SCHEDULE)

CELERYBEAT_SCHEDULE.update(SHOP_APP_SCHEDULE)

