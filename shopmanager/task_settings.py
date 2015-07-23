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
CELERYD_CONCURRENCY = 16 # 16 processes in parallel

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
        'flashsale.pay.tasks.notifyTradePayTask': {
            'queue': 'trade_notify',
            'routing_key': 'trade.pingpp_paycallback',
        },
        'flashsale.pay.tasks.notifyTradeRefundTask': {
            'queue': 'trade_notify',
            'routing_key': 'trade.ping_refundcallback',
        },
        'flashsale.pay.tasks.pushTradeRefundTask': {
            'queue': 'trade_notify',
            'routing_key': 'trade.push_refund',
        },
        'flashsale.xiaolumm.tasks.task_Push_Pending_Carry_Cash': {
            'queue': 'default',
            'routing_key': 'tasks.push_xlmm_pending_cash',
        },
        'flashsale.pay.tasks.task_Update_Sale_Customer': {
            'queue': 'default',
            'routing_key': 'tasks.update_sale_customer',
        },
        'shopapp.weixin.tasks.task_Update_Weixin_UserInfo': {
            'queue': 'default',
            'routing_key': 'tasks.update_weixin_userinfo',
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
    u'定时淘宝分销订单增量下载任务':{    #增量更新分销部分订单
        'task':'shopback.fenxiao.tasks.updateAllUserIncrementPurchasesTask',
        'schedule':crontab(minute="*/15"),
        'args':()
    },
    u'定时淘宝商城订单增量下载任务':{
        'task':'shopback.orders.tasks.updateAllUserIncrementTradesTask',
        'schedule':crontab(minute="0",hour="*/12"),
        'args':()
    },
    u'定时淘宝商城待发货订单下载任务':{
        'task':'shopback.orders.tasks.updateAllUserWaitPostOrderTask',
        'schedule':crontab(minute="30",hour="23"),
        'args':()
    },
    u'分段日期统计商品销售数据':{     #将昨日的订单数更新为商品的警告库位
         'task':'shopback.items.tasks.gradCalcProductSaleTask',
         'schedule':crontab(minute="30",hour='3'),
         'args':()
     },
#     u'定时淘宝退款订单下载任务':{     #更新昨日退货退款单
#          'task':'shopback.refunds.tasks.updateAllUserRefundOrderTask',
#          'schedule':crontab(minute="0",hour='2'),
#          'args':(1,None,None,)
#      },
    u'定时更新设置提醒的订单入问题单':{     #更新定时提醒订单
         'task':'shopback.trades.tasks.regularRemainOrderTask',
         'schedule':crontab(minute="0",hour='0,12,17'),
         'args':()
     },
     u'定时更新商品待发数':{     #更新库存
        'task':'shopback.items.tasks.updateProductWaitPostNumTask',
        'schedule':crontab(minute="0",hour="5"),#
        'args':()
     },
     u'定时更新淘宝商品库存':{     #更新库存
        'task':'shopback.items.tasks.updateAllUserItemNumTask',
        'schedule':crontab(minute="0",hour="*/7"),#
        'args':()
    },
    u'定时更新分销商品库存':{     #更新库存
        'task':'shopback.items.tasks.updateAllUserPurchaseItemNumTask',
        'schedule':crontab(minute="0",hour="*/7"),#
        'args':()
    },
    u'定时生成每月物流信息报表':{     #更新库存
        'task':'shopback.trades.tasks.task_Gen_Logistic_Report_File_By_Month',
        'schedule':crontab(minute="0",hour="4", day_of_month='10'),#
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
#    'runs-every-day-update-jushita-trade-task':{
#         'task':'tools.top_updatedb_task.pull_taobao_trade_task',
#         'schedule':crontab(minute="0",hour='*/4'),
#         'args':()
#    }
}


SHOP_APP_SCHEDULE = {
    u'定时抓取商品评价':{
        'task':'shopapp.comments.tasks.crawAllUserOnsaleItemComment',
        'schedule':crontab(minute="0",hour="8,10,12,14,16,18,20,22"),
        'args':()
    },
    u'定时上架任务':{  #定时上架任务
        'task':'shopapp.autolist.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/10',hour=','.join([str(i) for i in range(7,24)])),
        'args':(),
    },
    u'定时生成月销售报表':{
        'task':'shopapp.report.tasks.updateMonthTradeXlsFileTask',
        'schedule':crontab(minute="0",hour="3"),
        'args':()
    },
    u'淘宝异步任务结果自动处理':{     #淘宝异步任务执行主任务
         'task':'shopapp.asynctask.tasks.taobaoAsyncHandleTask',
         'schedule':crontab(minute="*/30"),
         'args':()
    },           
    u'定时发货短信通知客户':{     #更新库存
        'task':'shopapp.smsmgr.tasks.notifyPacketPostTask',
        'schedule':crontab(minute="30",hour="9,19"),#
        'args':(1,)
    },
    u'定时韵达录单任务':{
        'task':'shopapp.yunda.tasks.UpdateYundaOrderAddrTask',
        'schedule':crontab(minute="0",hour="10,13"),
        'args':()
    },
    u'定时取消二维码未揽件单号':{
        'task':'shopapp.yunda.tasks.CancelUnsedYundaSidTask',
        'schedule':crontab(minute="0",hour="4"),
        'args':()
    },
    u'定时系统订单重量更新至韵达对接系统':{
        'task':'shopapp.yunda.tasks.PushYundaPackageWeightTask',
        'schedule':crontab(minute="*/15",hour="17,18,19,20,21,22,23"),
        'args':()
    },
    u'定时增量下载更新微信订单':{
        'task':'shopapp.weixin.tasks.pullWaitPostWXOrderTask',
        'schedule':crontab(minute="0",hour="*/2"),
        'args':(None,None)
    },
    u'定时增量更新微信维权订单':{
        'task':'shopapp.weixin.tasks.pullFeedBackWXOrderTask',
        'schedule':crontab(minute="30",hour="*/2"),
        'args':(None,None)
    },
    u'定时同步微信商品库存':{
        'task':'shopapp.weixin.tasks.syncWXProductNumTask',
        'schedule':crontab(minute="10",hour='1,12'),
        'args':()
    },
    u'定时增量下载京东订单信息':{
        'task':'shopapp.jingdong.tasks.pullAllJDShopOrderByModifiedTask',
        'schedule':crontab(minute="*/15",hour=','.join([str(i) for i in range(9,23)])),
        'args':()
    },
    u'定时同步京东商品库存':{
        'task':'shopapp.jingdong.tasks.syncAllJDUserWareNumTask',
        'schedule':crontab(minute="20",hour='*/6'),
        'args':()
    },
    u'定时更新特卖订单订单列表':{
        'task':'flashsale.pay.tasks.push_SaleTrade_To_MergeTrade',
        'schedule':crontab(minute="0",hour="*/7"),
        'args':()
    },
    u'定时短信通知微信用户':{
        'task':'shopapp.weixin_sales.tasks.NotifyParentAwardTask',
        'schedule':crontab(minute="*/5",),
        'args':()
    },
    u'定时统计昨日小鹿妈妈点击':{
        'task':'flashsale.clickcount.tasks.task_Record_User_Click',
        'schedule':crontab(minute="30",hour='4'),
        'args':(),
#         'kwargs':{'pre_day':1}
    },
    u'定时统计昨日代理的订单':{
        'task':'flashsale.clickrebeta.tasks.task_Tongji_User_Order',
        'schedule':crontab(minute="40",hour='0'),
        'args':()
    },
    u'定时更新代理妈妈佣金提成':{
        'task':'flashsale.xiaolumm.tasks.task_Push_Pending_Carry_Cash',
        'schedule':crontab(minute="40",hour='5'),
        'args':(),
    },
    u'定时统计每日特卖综合数据':{
        'task':'flashsale.daystats.tasks.task_Calc_Sales_Stat_By_Day',
        'schedule':crontab(minute="40",hour='2'),
        'args':(),
    },
    u'定时统计每日二级代理贡献佣金':{
        'task':'flashsale.xiaolumm.tasks.task_Calc_Agency_Rebeta_Pending_And_Cash',
        'schedule':crontab(minute="40",hour='3'),
        'args':(),
    },
    u'定时统计每月妈妈千元提成佣金':{     
        'task':'flashsale.xiaolumm.tasks.task_Calc_Month_ThousRebeta',
        'schedule':crontab(minute="0",hour="4", day_of_month='1'),#
        'args':()
    },
    u'定时统计每组每天销售采购数据':{
        'task':'flashsale.dinghuo.tasks.task_stats_daily_order_by_group',
        'schedule': crontab(minute="0", hour="2"),
        'args': ()
    },
    u'定时统计每天商品数据':{
        'task':'flashsale.dinghuo.tasks.task_stats_daily_product',
        'schedule': crontab(minute="10", hour="2"),
        'args': ()
    },
    u'定时统计妈妈每周点击转化':{
        'task':'flashsale.clickcount.tasks.week_Count_week_Handdle',
        'schedule': crontab(minute="10", hour="5", day_of_week='mon'),
    },
    u'定时统计所有商品数据':{
        'task':'flashsale.dinghuo.tasks.task_stats_product',
        'schedule': crontab(minute="30", hour="2"),
        'args': ()
    },
    u'定时发送每日订货数据':{
        'task':'flashsale.dinghuo.tasks.task_send_daily_message',
        'schedule': crontab(minute="00", hour="23"),
        'args': ()
    },
    u'定时每日更新红包数据':{
        'task':'flashsale.pay.tasks.task_Pull_Red_Envelope',
        'schedule': crontab(minute="10", hour="23"),
        'args': ()
    },
    u'定时统计每天订货的供应商':{
        'task':'flashsale.dinghuo.tasks.task_write_supply_name',
        'schedule': crontab(minute="20", hour="23"),
        'args': ()
    },
    u'定时统计每天推广支出情况':{
        'task':'flashsale.daystats.tasks.task_PopularizeCost_By_Day',
        'schedule': crontab(minute="30", hour="8"),
        'args': ()
    },
    u'统计妈妈两周转化及点击基本价格':{
        'task':'flashsale.xiaolumm.tasks.task_Calc_Mama_Lasttwoweek_Stats',
        'schedule': crontab(minute="30", hour="6"),
        'args': ()
    },
    u'定时统计订货达标情况':{
        'task':'flashsale.dinghuo.tasks.task_daily_stat_ding_huo',
        'schedule': crontab(minute="40", hour="23"),
        'args': ()
    },
    u'定时统计每组得分':{
        'task':'flashsale.dinghuo.tasks.task_daily_stat_group_point',
        'schedule': crontab(minute="45", hour="23"),
        'args': ()
    },
    u'定时生成管理员代理状况汇总csv文件':{
        'task':'flashsale.xiaolumm.tasks_manager_summary.task_make_Manager_Summary_Cvs',
        'schedule': crontab(minute="10", hour="7"),
        'args': ()
    },
#    'runs-every-10-minutes-update-seller-flag':{
#        'task':'shopapp.memorule.tasks.updateTradeSellerFlagTask',
#        'schedule':crontab(minute="*/10"),
#        'args':()
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
#    'runs-every-day-send-yunda-weight':{
#        'task':'shopapp.yunda.tasks.SyncYundaScanWeightTask',
#        'schedule':crontab(minute="0",hour="20,22,0"),
#        'args':()
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

