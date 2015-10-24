# coding=utf-8
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from common.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.refunds.models import Refund
from shopback.users.models import User
from auth import apis
import logging
__author__ = 'meixqhi'

logger = logging.getLogger('django.request')



@task(max_retry=3)
def saveUserRefundOrderTask(user_id,update_from=None,update_to=None):

    update_from = format_datetime(update_from)
    update_to   = format_datetime(update_to)

    has_next = True
    cur_page = 1

    while has_next:
        
        response_list = apis.taobao_refunds_receive_get(tb_user_id=user_id,page_no=cur_page,
             page_size=settings.TAOBAO_PAGE_SIZE,start_modified=update_from,end_modified=update_to)

        refund_list = response_list['refunds_receive_get_response']
        if refund_list['total_results']>0:
            for r in refund_list['refunds']['refund']:

                refund,state = Refund.objects.get_or_create(refund_id=r['refund_id'])
                refund.save_refund_through_dict(user_id,r)

        total_nums = refund_list['total_results']
        cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums<total_nums
        cur_page += 1
        




@task()
def updateAllUserRefundOrderTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if not hander_update:
        dt  = datetime.datetime.now()
        update_from = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0)
        update_to   = dt

    users = User.effect_users.filter(type__in=('B','C'))
    for user in users:
        saveUserRefundOrderTask(user.visitor_id,update_from=update_from,update_to=update_to)


from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund


@task()
def refund_analysis(dat):
    year, montth, day = map(int, dat.split('-'))
    time_from = datetime.datetime(year, montth, day, 0, 0, 0)
    time_to = datetime.datetime(year, montth, day, 23, 59, 59)
    sodrs = SaleOrder.objects.filter(created__gte=time_from,
                                     created__lte=time_to).exclude(sale_trade__pay_time=None)  # 支付的订单
    # 支付的订单的退款数量（）　
    refs = sodrs.exclude(refund_status__in=(SaleRefund.NO_REFUND, SaleRefund.REFUND_CLOSED,
                                            SaleRefund.REFUND_REFUSE_BUYER))  # 排除　没有退款，　退款关闭，　拒绝退款

    sds_cut = sodrs.count()
    rfs_cnt = refs.count()
    ref_rate = "%0.4f" % (float(rfs_cnt)/sds_cut) if rfs_cnt > 0 else 0

    data = []
    dic_ref = {"dat": dat, "ref_num": rfs_cnt, "pay_num": sds_cut, "ref_rate": ref_rate}
    data.append(dic_ref)
    return data

from models_refund_rate import PayRefundRate


def refDataToMol(target_day=None):
    """ 写入特卖的退款率 数据到数据库中
    target_date: 日期时间类型
    """
    time_from = datetime.datetime(target_day.year, target_day.month, target_day.day, 0, 0, 0)
    time_to = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)

    sodrs = SaleOrder.objects.filter(created__gte=time_from,
                                     created__lte=time_to).exclude(sale_trade__pay_time=None)  # 支付的订单
    # 支付的订单的退款数量（）　
    refs = sodrs.exclude(refund_status__in=(SaleRefund.NO_REFUND, SaleRefund.REFUND_CLOSED,
                                            SaleRefund.REFUND_REFUSE_BUYER))  # 排除　没有退款，　退款关闭，　拒绝退款

    sds_cut = sodrs.count()  # 付款数量
    rfs_cnt = refs.count()  # 退款数量
    ref_rate = "%0.4f" % (float(rfs_cnt) / sds_cut) if rfs_cnt > 0 else 0
    date_cal = target_day.date()
    prfr, state = PayRefundRate.objects.get_or_create(date_cal=date_cal)
    prfr.ref_num = rfs_cnt
    prfr.pay_num = sds_cut
    prfr.ref_rate = ref_rate
    prfr.save()


def flushHistToRefRat(bt=None):
    """ 仅仅运行一次 """
    if bt is None:
        return
    today = datetime.datetime.today()
    while bt <= today:
        refDataToMol(target_day=bt)
        bt += datetime.timedelta(days=1)
        print u"统计时间:%s" % bt


@task()
def fifDaysRateFlush(days=15):
    """ 每天定时执行 刷新过去15天的数据 """
    for i in range(days):
        target_day = datetime.datetime.today() - datetime.timedelta(days=i)
        print u"target_day:%s" % target_day
        refDataToMol(target_day=target_day)



