#-*- encoding:utf-8 -*-
import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

#BROKER_HOST = "localhost"
#BROKER_PORT = 5672
#BROKER_USER = "guest"
#BROKER_PASSWORD = "guest"
#BROKER_VHOST = "/"

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
GEN_AMOUNT_FILE_MIN_DAYS = 20


from celery.schedules import crontab
from django.core.cache import cache
try:
    cache.delete('celery-single-instance-updateAllUserIncrementTradesTask')
except:
    print 'no cache' 
try:
    cache.delete('celery-single-instance-updateAllUserIncrementPurchasesTask')
except:
    print 'no cache'
try:
    cache.delete('celery-single-instance-updateMonthTradeXlsFileTask')
except:
    print 'no cache'
    

SYNC_MODEL_SCHEDULE = {
    'runs-every-hours-wait-post-orders':{    #增量更新商城订单
        'task':'shopback.orders.tasks.updateAllUserIncrementTradesTask',
        'schedule':crontab(minute="*/5"),
        'args':()
    },
    'runs-every-day-increment-orders':{    #更新昨天一整天的商城增量订单
        'task':'shopback.orders.tasks.updateAllUserIncrementOrdersTask',
        'schedule':crontab(minute="30",hour="2"),
        'args':()
    },
    'runs-every-hours-wait-post-purchase_orders':{   #增量更新分销订单
        'task':'shopback.fenxiao.tasks.updateAllUserIncrementPurchasesTask',
        'schedule':crontab(minute="*/10"),
        'args':(),
    },
    'runs-every-day-increment-purchase-orders':{   #更新昨天一整天的分销增量订单
        'task':'shopback.fenxiao.tasks.updateAllUserIncrementPurchaseOrderTask',
        'schedule':crontab(minute="45",hour="2"),
        'args':()
    },
    'runs-every-day-logistics':{     #更新订单物流信息
        'task':'shopback.logistics.tasks.updateAllUserOrdersLogisticsTask',
        'schedule':crontab(minute="0",hour="2"),
        'args':(None,None)
    },
    'runs-every-weeks-order-amount':{   #更新用户商城订单结算，按周
        'task':'shopback.amounts.tasks.updateAllUserOrdersAmountTask',
        'schedule':crontab(minute="0",hour="2",day_of_week="mon"), #
        'args':(7,None,None)
    },
    'runs-every-weeks-purchase-order-amount':{  #更新用户分销订单结算 按周
        'task':'shopback.amounts.tasks.updateAllUserPurchaseOrdersAmountTask',
        'schedule':crontab(minute="30",hour="2",day_of_week='mon'), #
        'args':(7,None,None)
    },
    'runs-every-weeks-item-entity':{     #更新用户商城商品信息
        'task':'shopback.items.tasks.updateAllUserItemsEntityTask',
        'schedule':crontab(minute="0",hour="3",day_of_week='tue'),#
        'args':()
    },
    'runs-every-weeks-purchase-product':{    #更新用户分销商品
        'task':'shopback.fenxiao.tasks.updateAllUserFenxiaoProductTask',
        'schedule':crontab(minute="30",hour="3",day_of_week='tue'),#
        'args':()
    },
    'runs-every-10-minutes-confirm-delivery-send':{   #更新淘宝发货状态
        'task':'shopback.trades.tasks.syncConfirmDeliveryTradeTask',
        'schedule':crontab(minute="*/5"),
        'args':()
    },
    'runs-every-day-regular-remaind-order':{     #更新定时提醒订单
         'task':'shopback.trades.tasks.regularRemainOrderTask',
         'schedule':crontab(minute="10",hour='0'),
         'args':()
     },
    'runs-every-quarter-taobao-async-handle':{     #淘宝异步任务执行主任务
         'task':'shopback.asynctask.tasks.taobaoAsyncHandleTask',
         'schedule':crontab(minute="*/30"),
         'args':()
     },
}


SHOP_APP_SCHEDULE = {
#    'runs-every-5-minutes-item-list':{  #定时上架任务
#        'task':'shopapp.autolist.tasks.updateAllItemListTask',
#        'schedule':crontab(minute='*/10',hour=','.join([str(i) for i in range(7,24)])),
#        'args':(),
#    },
#    'runs-every-30-minutes-keyword-pagerank':{  
#        'task':'shopapp.collector.tasks.updateItemKeywordsPageRank',
#        'schedule':crontab(minute="0,30",hour=','.join([str(i) for i in range(7,24)])),
#        'args':()
#    },
#    'runs-every-day-delete_keyword':{
#        'task':'shopapp.collector.tasks.deletePageRankRecordTask',
#        'schedule':crontab(minute="0",hour="1"),
#        'args':(30,)
#    },
#    'runs-every-day-trade-report-file':{
#        'task':'shopapp.report.tasks.updateMonthTradeXlsFileTask',
#        'schedule':crontab(minute="0",hour="4"),
#        'args':()
#    },
#    'runs-every-10-minutes-update-rule-memo':{
#        'task':'shopapp.memorule.tasks.updateTradeAndOrderByRuleMemo',
#        'schedule':crontab(minute="*/10"),
#        'args':()
#    },
#    'runs-every-10-minutes-update-seller-flag':{
#        'task':'shopapp.memorule.tasks.updateTradeSellerFlagTask',
#        'schedule':crontab(minute="*/10"),
#        'args':()
#    },                 
                     
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

