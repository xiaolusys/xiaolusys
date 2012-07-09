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
    'runs-every-hours-wait-post-orders':{
        'task':'shopback.orders.tasks.updateAllUserDuringOrdersTask',
        'schedule':crontab(minute="0,30"),
        'args':(None,None,'WAIT_SELLER_SEND_GOODS')
    },
    'runs-every-hours-wait-post-purchase_orders':{
        'task':'shopback.fenxiao.tasks.updateAllUserPurchaseOrderTask',
        'schedule':crontab(minute="0,30"),
        'args':(None,None,'WAIT_SELLER_SEND_GOODS'),
    },
    'runs-every-day-orders':{
        'task':'shopback.orders.tasks.updateAllUserIncrementOrdersTask',
        'schedule':crontab(minute="0",hour="1"),
        'args':(None,None),
    },
    'runs-every-day-logistics':{
        'task':'shopback.logistics.tasks.updateAllUserOrdersLogisticsTask',
        'schedule':crontab(minute="0",hour="2"),
        'args':(None,None)
    },
    'runs-every-day-purchase-orders':{
        'task':'shopback.fenxiao.tasks.updateAllUserIncrementPurchaseOrderTask',
        'schedule':crontab(minute="30",hour="1"),
        'args':(None,None),
    },                   
    'runs-every-weeks-order-amount':{
        'task':'shopback.amounts.tasks.updateAllUserOrdersAmountTask',
        'schedule':crontab(minute="*/10",), #crontab(minute="0",hour="2",day_of_week="mon")
        'args':(7,None,None)
    },
    'runs-every-weeks-purchase-order-amount':{
        'task':'shopback.amounts.tasks.updateAllUserPurchaseOrdersAmountTask',
        'schedule':crontab(minute="*/10",), #crontab(minute="30",hour="2",day_of_week='mon')
        'args':(7,None,None)
    },
    'runs-every-weeks-item-entity':{
        'task':'shopback.items.tasks.updateAllUserItemsEntityTask',
        'schedule':crontab(minute="*/10"),#crontab(minute="0",hour="3",day_of_week='tue')
        'args':()
    },
    'runs-every-weeks-purchase-product':{
        'task':'shopback.fenxiao.tasks.updateAllUserFenxiaoProductTask',
        'schedule':crontab(minute="*/10"),#crontab(minute="30",hour="3",day_of_week='tue')
        'args':()
    },                   
}


SHOP_APP_SCHEDULE = {
    'runs-every-5-minutes-item-list':{
        'task':'shopapp.autolist.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/5',hour=','.join([str(i) for i in range(7,24)])),
        'args':(),
    },
    'runs-every-30-minutes-keyword-pagerank':{
        'task':'shopapp.collector.tasks.updateItemKeywordsPageRank',
        'schedule':crontab(minute="0,30",hour=','.join([str(i) for i in range(7,24)])),
        'args':()
    },
    'runs-every-day-delete_keyword':{
        'task':'shopapp.collector.tasks.deletePageRankRecordTask',
        'schedule':crontab(minute="0",hour="1"),
        'args':(30,)
    },
    'runs-every-day-trade-report-file':{
        'task':'shopapp.report.tasks.updateMonthTradeXlsFileTask',
        'schedule':crontab(minute="0",hour="4"),
        'args':()
    },
#    'runs-every-day-item-num':{
#        'task':'shopapp.syncnum.tasks.updateAllItemNumTask',
#        'schedule':crontab(minute="0",hour="0"),
#        'args':(),
#    },
#    'runs-every-day-product-trade':{
#        'task':'shopapp.collector.tasks.updateProductTradeBySellerTask',
#        'schedule':crontab(minute="0",hour="1"),
#        'args':()
#    },
}


CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE.update(SYNC_MODEL_SCHEDULE)

CELERYBEAT_SCHEDULE.update(SHOP_APP_SCHEDULE)

