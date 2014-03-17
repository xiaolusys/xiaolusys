#-*- coding:utf-8 -*-
import djcelery
djcelery.setup_loader()

#CELERY_RESULT_BACKEND = 'database'
#BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

BROKER_URL = 'amqp://user1:passwd1@127.0.0.1:5672/vhost1'
CELERY_RESULT_BACKEND = "amqp"
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.
BROKER_POOL_LIMIT = 10 # 10 connections
CELERYD_CONCURRENCY = 40 # 16 processes in parallel

from kombu import Exchange, Queue
CELERY_DEFAULT_QUEUE = 'peroid'
CELERY_QUEUES = (
    Queue('default', routing_key='tasks.#'),
    Queue('item_notify', routing_key='item.#'),
    Queue('trade_notify', routing_key='trade.#'),
    Queue('refund_notify', routing_key='refund.#'),
    Queue('peroid', routing_key='peroid.#'),
)

CELERY_DEFAULT_EXCHANGE = 'peroid'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'peroid.default'

CELERY_ROUTES = {
        'shopapp.notify.tasks.process_trade_notify_task': {
            'queue': 'trade_notify',
            'routing_key': 'trade.process_trade_notify',
        },
        'shopapp.notify.tasks.process_item_notify_task': {
            'queue': 'item_notify',
            'routing_key': 'item.process_item_notify',
        },
        'shopapp.notify.tasks.process_refund_notify_task': {
            'queue': 'refund_notify',
            'routing_key': 'refund.process_refund_notify',
        },
        'shopapp.notify.tasks.process_discard_notify_task': {
            'queue': 'peroid',
            'routing_key': 'peroid.process_discard_notify',
        },
        'shopapp.notify.tasks.delete_success_notify_record_task': {
            'queue': 'peroid',
            'routing_key': 'peroid.delete_success_notify_record',
        },
        'shopback.fenxiao.tasks.saveUserPurchaseOrderTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.save_purchase_order_task',
        },
        'shopback.orders.tasks.saveUserDuringOrdersTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.save_user_during_orders_task',
        },
        'shopback.items.tasks.updateProductWarnNumTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.update_prod_warn_num_task',
        },
        'shopback.smsmgr.tasks.notifyPacketPostTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.notify_packet_post_task',
        },
        'shopback.trades.tasks.pushBuyerToCustomerTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.push_buyer_to_customer_task',
        },
        'shopapp.yunda.tasks.UpdateYundaOrderAddrTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.update_yunda_order_address_task',
        },
        'shopapp.yunda.tasks.CancelUnsedYundaSidTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.cancel_unused_yunda_sid',
        },
        'shopapp.yunda.tasks.SyncYundaScanWeightTask': {
            'queue': 'peroid',
            'routing_key': 'peroid.sync_yunda_scan_weight',
        },
        'shopapp.comments.tasks.crawAllUserOnsaleItemComment':{
            'queue':'peroid',
            'routing_key':'peroid.craw_onsale_item_comment',
        },
        'top_updatedb_task.pull_taobao_trade_task':{
            'queue':'peroid',
            'routing_key':'peroid.pull_taobao_trade_task',
        },
}


API_REQUEST_INTERVAL_TIME = 10      #(seconds)
API_TIME_OUT_SLEEP = 60             #(seconds)
API_OVER_LIMIT_SLEEP = 180          #(seconds)

####### gen trade amount file config #######
GEN_AMOUNT_FILE_MIN_DAYS = 20

####### schedule task  ########
from celery.schedules import crontab

SYNC_MODEL_SCHEDULE = {
    'runs-every-10-minites-fenxiao-increment-purchases':{    #增量更新分销部分订单
        'task':'shopback.fenxiao.tasks.updateAllUserIncrementPurchasesTask',
        'schedule':crontab(minute="*/15"),
        'args':()
    },
#    'runs-every-weeks-order-amount':{   #更新用户商城订单结算，按周
#        'task':'shopback.amounts.tasks.updateAllUserOrdersAmountTask',
#        'schedule':crontab(minute="0",hour="2"), #
#        'args':(1,None,None)
#    },
#    'runs-every-weeks-purchase-order-amount':{  #更新用户分销订单结算 按周
#        'task':'shopback.amounts.tasks.updateAllUserPurchaseOrdersAmountTask',
#        'schedule':crontab(minute="30",hour="2",day_of_week='mon'), #
#        'args':(7,None,None)
#    },
    'runs-every-half-day-increment-orders':{
        'task':'shopback.orders.tasks.updateAllUserIncrementTradesTask',
        'schedule':crontab(minute="30",hour="7,12,16,23"),
        'args':()
    },
    'runs-every-day-warn-num-update':{     #将昨日的订单数更新为商品的警告库位
         'task':'shopback.items.tasks.updateProductWarnNumTask',
         'schedule':crontab(minute="30",hour='1'),
         'args':()
     },
    'runs-every-day-refund-order-update':{     #更新昨日退货退款单
         'task':'shopback.refunds.tasks.updateAllUserRefundOrderTask',
         'schedule':crontab(minute="0",hour='2'),
         'args':(1,None,None)
     },
    'runs-every-day-regular-remaind-order':{     #更新定时提醒订单
         'task':'shopback.trades.tasks.regularRemainOrderTask',
         'schedule':crontab(minute="0",hour='*/12'),
         'args':()
     },
    'runs-every-week-push-buyer-to-customer':{     #更新客户信息
         'task':'shopback.trades.tasks.pushBuyerToCustomerTask',
         'schedule':crontab(minute="0",hour='2',day_of_week='sun'),
         'args':(21,)
     },
     'runs-every-day-item-num':{     #更新库存
        'task':'shopback.items.tasks.updateAllUserItemNumTask',
        'schedule':crontab(minute="0",hour="*/7"),#
        'args':()
    },
#    'runs-every-day-update-jushita-trade-task':{
#         'task':'tools.top_updatedb_task.pull_taobao_trade_task',
#         'schedule':crontab(minute="0",hour='*/4'),
#         'args':()
#    }
}


SHOP_APP_SCHEDULE = {
    'runs-every-day-craw-onsale-item-comment':{
        'task':'shopapp.comments.tasks.crawAllUserOnsaleItemComment',
        'schedule':crontab(minute="0",hour="*/4"),
        'args':()
    },
    'runs-every-5-minutes-item-list':{  #定时上架任务
        'task':'shopapp.autolist.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/10',hour=','.join([str(i) for i in range(7,24)])),
        'args':(),
    },
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
    'runs-every-day-trade-report-file':{
        'task':'shopapp.report.tasks.updateMonthTradeXlsFileTask',
        'schedule':crontab(minute="0",hour="3"),
        'args':()
    },
#    'runs-every-10-minutes-update-seller-flag':{
#        'task':'shopapp.memorule.tasks.updateTradeSellerFlagTask',
#        'schedule':crontab(minute="*/10"),
#        'args':()
#    },                    
    'runs-every-quarter-taobao-async-handle':{     #淘宝异步任务执行主任务
         'task':'shopapp.asynctask.tasks.taobaoAsyncHandleTask',
         'schedule':crontab(minute="*/30"),
         'args':()
    },           
    'runs-every-day-notify-packet-post':{     #更新库存
        'task':'shopapp.smsmgr.tasks.notifyPacketPostTask',
        'schedule':crontab(minute="30",hour="9,19"),#
        'args':(1,)
    },
    'runs-every-day-sync-yunda-address':{
        'task':'shopapp.yunda.tasks.UpdateYundaOrderAddrTask',
        'schedule':crontab(minute="0",hour="8,12"),
        'args':()
    },
    'runs-every-day-send-yunda-weight':{
        'task':'shopapp.yunda.tasks.SyncYundaScanWeightTask',
        'schedule':crontab(minute="0",hour="20"),
        'args':()
    },
    'runs-every-day-cancel-yunda-sid':{
        'task':'shopapp.yunda.tasks.CancelUnsedYundaSidTask',
        'schedule':crontab(minute="0",hour="4"),
        'args':()
    },
#    'runs-every-day-product-trade':{
#        'task':'shopapp.collector.tasks.updateProductTradeBySellerTask',
#        'schedule':crontab(minute="0",hour="1"),
#        'args':()
#    },
    'runs-every-day-delete-notify-record':{
        'task':'shopapp.notify.tasks.delete_success_notify_record_task',
        'schedule':crontab(minute="30",hour="0"),
        'args':(7,)
    },
}


CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE.update(SYNC_MODEL_SCHEDULE)

CELERYBEAT_SCHEDULE.update(SHOP_APP_SCHEDULE)

