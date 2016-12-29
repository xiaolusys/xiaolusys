# coding=utf-8
from shopback.trades.models import *
from flashsale.pay.models import *
from flashsale.dinghuo.models_purchase import *
from common.dingding import DingDingAPI
from shopmanager import celery_app as app

dingding_users = (
        ('04371031623485', u'崔人帅'),
        ('04666934261184086', u'邓辉'),
        ('01534652611551', u'黄炎'),
        ('01591912287010', u'林杰'),
        ('02301542299173', u'梅秀青'),
        ('03630839235943', u'孙捷'),
        ('02401336675559', u'伍磊'),
        ('0550581811782786', u'张波'))
USER_DICT = {item[1]:item[0] for item in dingding_users}


def send_supplychain_alarm(msg, users=[u'黄炎', u'伍磊', u'邓辉', u'梅秀青']):
    dd = DingDingAPI()
    for user in users:
        if USER_DICT.get(user):
            dd.sendMsg(user + ':' + msg, touser=USER_DICT[user])


def alarm_saleorder_not_create_packageskuitem():
    oids = [s.oid for s in SaleOrder.objects.filter(status=2, refund_status=0, sale_trade__order_type=0)]
    poids = [p.oid for p in PackageSkuItem.objects.filter(oid__in=oids)]
    err_oids = list(set(oids) - set(poids))
    if err_oids:
        msg = str(err_oids) + u'没有产生包裹商品单'
        send_supplychain_alarm(msg)


def alarm_psi_not_merge():
    psi_ids = PackageSkuItem.objects.filter(status=PSI_STATUS.ASSIGNED, type=PSI_TYPE.NORMAL).values_list('id', flat=True)
    psi_ids = list(psi_ids)
    PackageSkuItem.batch_merge()
    if psi_ids:
        msg = str(psi_ids) + u'未进行合单'
        send_supplychain_alarm(msg, [u'黄炎'])


@app.task()
def alarms_shopback_trades():
    alarm_saleorder_not_create_packageskuitem()
    alarm_psi_not_merge()