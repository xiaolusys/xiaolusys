#-*- coding:utf-8 -*-
import datetime
import time
import json
from celery.task import task
from celery.task.sets import subtask
from shopback import paramconfig as pcfg
from shopback.items.tasks import updateUserItemsTask,updateUserProductSkuTask
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from shopback.orders.tasks import saveUserDuringOrdersTask
from shopback.fenxiao.tasks import saveUserPurchaseOrderTask



@task()
def initSystemDataFromAuthTask(visitor_id):
    #更新用户所有商品显示
    updateUserItemsTask(visitor_id)
    #更新商品规格信息
    updateUserProductSkuTask(visitor_id)
    #更新分销商品信息
    saveUserFenxiaoProductTask(visitor_id)
    #更新等待发货商城订单
    saveUserDuringOrdersTask.delay(visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
    #更新待发货分销订单
    saveUserPurchaseOrderTask.delay(visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
    