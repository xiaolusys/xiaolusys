#-*- coding:utf-8 -*-
import djcelery
djcelery.setup_loader()

CELERY_IMPORTS = (
    'shopback.trades.tasks_release',
)
#CELERY_RESULT_BACKEND = 'database'
# BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
#BROKER_URL = 'amqp://user1:passwd1@127.0.0.1:5672/vhost1'
BROKER_URL = 'amqp://user1:passwd1@10.132.179.237:5672/vhost1'

CELERY_RESULT_BACKEND = "djcelery.backends.cache:CacheBackend" #"amqp"
# 某个程序中出现的队列，在broker中不存在，则立刻创建它  
#CELERY_CREATE_MISSING_QUEUES = True 
# 每个worker最多执行万100个任务就会被销毁，可防止内存泄露  
#CELERYD_MAX_TASKS_PER_CHILD = 100    
# 单个任务的运行时间不超过此值，否则会被SIGKILL 信号杀死 
# CELERYD_TASK_TIME_LIMIT = 60    
# 非常重要,有些情况下可以防止死锁,如果有数量更时间限制应开启 
#CELERYD_FORCE_EXECV = True    
#WORKER每次取任务数
#CELERYD_PREFETCH_MULTIPLIER = 1
# BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 90}  
# 任务发出后，经过一段时间还未收到acknowledge , 就将任务重新交给其他worker执行  
# CELERY_DISABLE_RATE_LIMITS = True     

CELERY_TIMEZONE = 'Asia/Shanghai'  
CELERY_CHORD_PROPAGATES = True
CELERY_IGNORE_RESULT = False

CELERY_TASK_RESULT_EXPIRES = 5*60  # 5min
#CELERYD_POOL = 'gevent'
BROKER_POOL_LIMIT = 10 # 10 connections
CELERYD_CONCURRENCY = 16 # 16 processes in paralle

from kombu import Exchange, Queue
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default', routing_key='tasks.#'),
    Queue('notify', routing_key='notify.#'),
    Queue('peroid', routing_key='peroid.#'),
    Queue('frency', routing_key='frency.#'),
    Queue('async', routing_key='async.#'),
)

CELERY_DEFAULT_EXCHANGE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'default'

CELERY_ROUTES = {
        'flashsale.xiaolumm.tasks.task_Push_Pending_Carry_Cash': {
            'queue': 'peroid',
            'routing_key': 'peroid.push_xlmm_pending_cash',
        },#结算小鹿妈妈们待确认提成
        #######################################################
        'shopapp.notify.tasks.process_trade_notify_task': {
            'queue': 'notify',
            'routing_key': 'notify.process_trade_notify',
        },#淘宝订单消息处理
        'flashsale.pay.tasks.notifyTradePayTask': {
            'queue': 'notify',
            'routing_key': 'notify.pingpp_paycallback',
        },#小鹿特卖平台订单支付消息处理
        'flashsale.pay.tasks.notifyTradeRefundTask': {
            'queue': 'notify',
            'routing_key': 'notify.ping_refundcallback',
        },#小鹿特卖平台订单退款消息处理
        'flashsale.pay.tasks.pushTradeRefundTask': {
            'queue': 'notify',
            'routing_key': 'noitfy.push_refund',
        },#小鹿特卖平台订单退款更新到仓库订单
         #######################################################
        'flashsale.clickcount.tasks.task_Create_Click_Record': {
            'queue': 'frency',
            'routing_key': 'frency.task_Create_Click_Record',
        },#微信用户点击记录
        'flashsale.clickcount.tasks.task_Update_User_Click': {
            'queue': 'frency',
            'routing_key': 'frency.task_Update_User_Click',
        },#微信用户点击记录
        'flashsale.pay.tasks.task_Update_Sale_Customer': {
            'queue': 'frency',
            'routing_key': 'frency.update_sale_customer',
        },#保存微信用户OPENID信息
        'shopapp.weixin.tasks.task_Update_Weixin_UserInfo': {
            'queue': 'frency',
            'routing_key': 'frency.update_weixin_userinfo',
        }, #更新微信用户信息
        'flashsale.restpro.tasks.SaveWuliu_only': {
            'queue': 'frency',
            'routing_key': 'frency.SaveWuliu_only',
        }, #更新物流信息
        #######################################################
        'shopapp.asynctask.tasks.PrintAsyncTask': {
            'queue': 'async',
            'routing_key': 'async.async_invoice_print',
        },#发货单打印任务
        'shopback.trades.tasks.sendTaobaoTradeTask': {
            'queue': 'async',
            'routing_key': 'async.sendTaobaoTradeTask',
        },#订单发货任务
        'shopback.trades.tasks.sendTradeCallBack': {
            'queue': 'async',
            'routing_key': 'async.sendTradeCallBack',
        },#订单发货回调任务
        'shopback.trades.tasks.uploadTradeLogisticsTask': {
            'queue': 'async',
            'routing_key': 'async.uploadTradeLogisticsTask',
        },#上传订单物流信息任务
        'shopback.trades.tasks.deliveryTradeCallBack': {
            'queue': 'async',
            'routing_key': 'async.deliveryTradeCallBack',
        },#上传订单物流回调任务
        'flashsale.dinghuo.tasks.get_sale_amount_by_product': { 
            'queue': 'async',
            'routing_key': 'async.get_sale_amount_by_product',
        },#获取特卖商品销售统计
        'flashsale.dinghuo.tasks.task_supplier_stat': { 
            'queue': 'async',
            'routing_key': 'async.task_supplier_stat',
        },#获取特卖供应商统计
        'flashsale.dinghuo.tasks.task_ding_huo': { 
            'queue': 'async',
            'routing_key': 'async.task_ding_huo',
        },#大货统计
        'flashsale.dinghuo.tasks.task_ding_huo_optimize': { 
            'queue': 'async',
            'routing_key': 'async.task_ding_huo_optimize',
        },#大货统计优化
        'flashsale.dinghuo.tasks.calcu_refund_info_by_pro_v2': { 
            'queue': 'async',
            'routing_key': 'async.calcu_refund_info_by_pro_v2',
        },#特卖商品退款数统计
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
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时淘宝商城订单增量下载任务':{
        'task':'shopback.orders.tasks.updateAllUserIncrementTradesTask',
        'schedule':crontab(minute="0",hour="*/12"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时淘宝商城待发货订单下载任务':{
        'task':'shopback.orders.tasks.updateAllUserWaitPostOrderTask',
        'schedule':crontab(minute="30",hour="23"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'分段日期统计商品销售数据':{     #将昨日的订单数更新为商品的警告库位
         'task':'shopback.items.tasks.gradCalcProductSaleTask',
         'schedule':crontab(minute="30",hour='3'),
         'args':(),
         'options' : {'queue':'peroid','routing_key':'peroid.task'} 
     },
#     u'定时淘宝退款订单下载任务':{     #更新昨日退货退款单
#          'task':'shopback.refunds.tasks.updateAllUserRefundOrderTask',
#          'schedule':crontab(minute="0",hour='2'),
#          'args':(1,None,None,)
#      },
    u'定时更新设置提醒的订单入问题单':{     #更新定时提醒订单
         'task':'shopback.trades.tasks.regularRemainOrderTask',
         'schedule':crontab(minute="0",hour='0,12,17'),
         'args':(),
         'options' : {'queue':'peroid','routing_key':'peroid.task'} 
     },
     u'定时更新商品待发数':{     #更新库存
        'task':'shopback.items.tasks.updateProductWaitPostNumTask',
        'schedule':crontab(minute="0",hour="5,13"),#
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'}
     },
     u'定时更新淘宝商品库存':{     #更新库存
        'task':'shopback.items.tasks.updateAllUserItemNumTask',
        'schedule':crontab(minute="0",hour="7"),#
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新分销商品库存':{     #更新库存
        'task':'shopback.items.tasks.updateAllUserPurchaseItemNumTask',
        'schedule':crontab(minute="0",hour="7"),#
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时生成每月物流信息报表':{     #更新库存
        'task':'shopback.trades.tasks.task_Gen_Logistic_Report_File_By_Month',
        'schedule':crontab(minute="0",hour="4", day_of_month='10'),#
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时释放定时提醒订单':{
        'task':'shopback.trades.tasks_release.CancelMergeOrderStockOutTask',
        'schedule':crontab(minute="5",hour=','.join([str(i) for i in range(8,22,1)])),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时下载更新小鹿特卖订单':{
        'task':'flashsale.pay.tasks.pull_Paid_SaleTrade',
        'schedule':crontab(minute="20",hour="3"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
#    'runs-every-weeks-order-amount':{   #更新用户商城订单结算，按周
#        'task':'shopback.amounts.tasks.updateAllUserOrdersAmountTask',
#        'schedule':crontab(minute="0",hour="2"), #
#        'args':(1,None,None),
#        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
#    },
#    'runs-every-weeks-purchase-order-amount':{  #更新用户分销订单结算 按周
#        'task':'shopback.amounts.tasks.updateAllUserPurchaseOrdersAmountTask',
#        'schedule':crontab(minute="30",hour="2",day_of_week='mon'), #
#        'args':(7,None,None),
#        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
#    },
#    'runs-every-day-update-jushita-trade-task':{
#         'task':'tools.top_updatedb_task.pull_taobao_trade_task',
#         'schedule':crontab(minute="0",hour='*/4'),
#         'args':(),
#         'options' : {'queue':'peroid','routing_key':'peroid.task'} 
#    }
}


SHOP_APP_SCHEDULE = {
    u'定时抓取商品评价':{
        'task':'shopapp.comments.tasks.crawAllUserOnsaleItemComment',
        'schedule':crontab(minute="0",hour="8,10,12,14,16,18,20,22"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时上架任务':{  #定时上架任务
        'task':'shopapp.autolist.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/10',hour=','.join([str(i) for i in range(7,24)])),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时生成月销售报表':{
        'task':'shopapp.report.tasks.updateMonthTradeXlsFileTask',
        'schedule':crontab(minute="0",hour="3"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'淘宝异步任务结果自动处理':{     #淘宝异步任务执行主任务
         'task':'shopapp.asynctask.tasks.taobaoAsyncHandleTask',
         'schedule':crontab(minute="*/30"),
         'args':(),
         'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },           
    u'定时发货短信通知客户':{     #更新库存
        'task':'shopapp.smsmgr.tasks.notifyPacketPostTask',
        'schedule':crontab(minute="30",hour="9,19"),#
        'args':(1,),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时韵达录单任务':{
        'task':'shopapp.yunda.tasks.UpdateYundaOrderAddrTask',
        'schedule':crontab(minute="0",hour="10,13"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时取消二维码未揽件单号':{
        'task':'shopapp.yunda.tasks.CancelUnsedYundaSidTask',
        'schedule':crontab(minute="0",hour="4"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时系统订单重量更新至韵达对接系统':{
        'task':'shopapp.yunda.tasks.PushYundaPackageWeightTask',
        'schedule':crontab(minute="*/15",hour="17,18,19,20,21,22,23"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时增量下载更新微信订单':{
        'task':'shopapp.weixin.tasks.pullWaitPostWXOrderTask',
        'schedule':crontab(minute="0",hour="*/2"),
        'args':(None,None),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时增量更新微信维权订单':{
        'task':'shopapp.weixin.tasks.pullFeedBackWXOrderTask',
        'schedule':crontab(minute="30",hour="*/2"),
        'args':(None,None),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时同步微信商品库存':{
        'task':'shopapp.weixin.tasks.syncWXProductNumTask',
        'schedule':crontab(minute="10",hour='1,12'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时增量下载京东订单信息':{
        'task':'shopapp.jingdong.tasks.pullAllJDShopOrderByModifiedTask',
        'schedule':crontab(minute="*/15",hour=','.join([str(i) for i in range(9,23)])),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时同步京东商品库存':{
        'task':'shopapp.jingdong.tasks.syncAllJDUserWareNumTask',
        'schedule':crontab(minute="20",hour='6'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新特卖订单订单列表':{
        'task':'flashsale.pay.tasks.push_SaleTrade_To_MergeTrade',
        'schedule':crontab(minute="0",hour="*/7"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新特卖及微信订单状态':{
        'task':'flashsale.xiaolumm.tasks.task_Update_Sale_And_Weixin_Order_Status',
        'schedule':crontab(minute="0",hour="6"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时短信通知微信用户':{
        'task':'shopapp.weixin_sales.tasks.NotifyParentAwardTask',
        'schedule':crontab(minute="*/5",),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计昨日小鹿妈妈点击':{
        'task':'flashsale.clickcount.tasks.task_Record_User_Click',
        'schedule':crontab(minute="30",hour='4'),
        'args':(),
#         'kwargs':{'pre_day':1},
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计昨日代理的订单':{
        'task':'flashsale.clickrebeta.tasks.task_Tongji_User_Order',
        'schedule':crontab(minute="40",hour='0'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新代理妈妈佣金提成':{
        'task':'flashsale.xiaolumm.tasks.task_Push_Pending_Carry_Cash',
        'schedule':crontab(minute="40",hour='5'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计每日特卖综合数据':{
        'task':'flashsale.daystats.tasks.task_Calc_Sales_Stat_By_Day',
        'schedule':crontab(minute="40",hour='2'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计每日二级代理贡献佣金':{
        'task':'flashsale.xiaolumm.tasks.task_Calc_Agency_Rebeta_Pending_And_Cash',
        'schedule':crontab(minute="40",hour='3'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计每月妈妈千元提成佣金':{     
        'task':'flashsale.xiaolumm.tasks.task_Calc_Month_ThousRebeta',
        'schedule':crontab(minute="0",hour="4", day_of_month='1'),#
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计每天商品数据':{
        'task':'flashsale.dinghuo.tasks.task_stats_daily_product',
        'schedule': crontab(minute="10", hour="2"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计妈妈每周点击转化':{
        'task':'flashsale.clickcount.tasks.week_Count_week_Handdle',
        'schedule': crontab(minute="10", hour="5", day_of_week='mon'),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计所有商品数据':{
        'task':'flashsale.dinghuo.tasks.task_stats_product',
        'schedule': crontab(minute="30", hour="2"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新妈妈提成订单状态':{
        'task':'flashsale.clickrebeta.tasks.task_Update_Shoppingorder_Status',
        'schedule':crontab(minute="40",hour='3'),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时发货速度':{
        'task':'flashsale.dinghuo.tasks.task_daily_preview',
        'schedule': crontab(minute="50", hour="2"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时每日更新红包数据':{
        'task':'flashsale.pay.tasks.task_Pull_Red_Envelope',
        'schedule': crontab(minute="10", hour="23"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计每天推广支出情况':{
        'task':'flashsale.daystats.tasks.task_PopularizeCost_By_Day',
        'schedule': crontab(minute="30", hour="8"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'统计妈妈两周转化及点击基本价格':{
        'task':'flashsale.xiaolumm.tasks.task_Calc_Mama_Lasttwoweek_Stats',
        'schedule': crontab(minute="30", hour="6"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时生成管理员代理状况汇总csv文件':{
        'task':'flashsale.xiaolumm.tasks_manager_summary.task_make_Manager_Summary_Cvs',
        'schedule': crontab(minute="45", hour="6"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时升级代理级别为A类到VIP类任务':{
        'task':'flashsale.xiaolumm.tasks.xlmm_upgrade_A_to_VIP',
        'schedule':crontab(minute="50", hour="5"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新用户优惠券状态':{
        'task':'flashsale.pay.tasks.task_Update_CouponPoll_Status',
        'schedule': crontab(minute="15", hour="2"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时更新购物车和订单状态':{
        'task':'flashsale.restpro.tasks.task_off_the_shelf',
        'schedule': crontab(minute="20", hour="2"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时发送发货超过五天订单':{
        'task':'shopapp.smsmgr.tasks.task_deliver_goods_later',
        'schedule': crontab(minute="30", hour="13"),
        'args': (),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时清理购物车和待支付订单任务':{
        'task':'flashsale.restpro.tasks.task_schedule_cart',
        'schedule':crontab(minute="*/5"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计特卖平台退款率任务':{
        'task':'shopback.refunds.tasks.fifDaysRateFlush',
        'schedule':crontab(minute="10", hour="3"),
        'args':(),
        'options' : {'queue':'peroid','routing_key':'peroid.task'} 
    },
    u'定时统计供应商的平均发货速度任务': {
        'task': 'flashsale.dinghuo.tasks.task_supplier_avg_post_time',
        'schedule': crontab(minute="30", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时统计产品分类的坑位数量任务': {
        'task': 'shopback.categorys.tasks.category_pit_num_stat',
        'schedule': crontab(minute="30", hour="11"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时统计产品分类的订货数量和订货金额任务': {
        'task': 'flashsale.dinghuo.tasks.task_category_stock_data',
        'schedule': crontab(minute="50", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时统计产品分类的库存数量和库存金额任务': {
        'task': 'shopback.categorys.tasks.task_category_collect_num',
        'schedule': crontab(minute="10", hour="4"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时上架库存商品任务': {
        'task': 'shopback.items.tasks.task_Auto_Upload_Shelf',
        'schedule': crontab(minute="0", hour="10"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时下架库存商品任务': {
        'task': 'shopback.items.tasks.task_Auto_Download_Shelf',
        'schedule': crontab(minute="0", hour="14"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
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

