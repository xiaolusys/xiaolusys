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


from flashsale.pay.models import SaleOrder, SaleRefund
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


@task()
def taskRefundRecord(obj):
    from common.modelutils import update_model_fields
    from flashsale.pay.models import SaleOrder
    from shopback.refunds.models_refund_rate import PayRefNumRcord
    order = SaleOrder.objects.get(id=obj.order_id)
    trade = order.sale_trade
    time_from = trade.pay_time
    time_to = trade.pay_time + datetime.timedelta(days=1)
    date_cal = datetime.date(time_from.year, time_from.month, time_from.day)
    # 判断提交申请的时间是否是在付款后24小时内产生的 (只有在付款后才会有退款)
    refund_record, state = PayRefNumRcord.objects.get_or_create(date_cal=date_cal)
    if obj.created >= time_to:  # 24小时外
        if order.status in (SaleOrder.WAIT_BUYER_CONFIRM_GOODS, SaleOrder.TRADE_BUYER_SIGNED):
            # 如果　已发货　　则　算入　发货后退货数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_sed_num = 1
            else:  # 有记录则累加
                refund_record.ref_sed_num += 1
            write_dinghuo_return_pro(obj)   # 计算到订货表中的退货数量
        if order.status in (SaleOrder.WAIT_SELLER_SEND_GOODS, ):
            # 如果　未发货　　则　算入　24小时外未发货退款数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_num_out = 1
            else:  # 有记录则累加
                refund_record.ref_num_out += 1
    else:  # 如果24小时内　已发货   则　算入　发货后退货数量
        if order.status in (SaleOrder.WAIT_BUYER_CONFIRM_GOODS, SaleOrder.TRADE_BUYER_SIGNED):
            # 如果　已发货　　则　算入　发货后退货数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_sed_num = 1
            else:  # 有记录则累加
                refund_record.ref_sed_num += 1
            write_dinghuo_return_pro(obj)   # 计算到订货表中的退货数量
        else:  # 否则　算入　24小时内　　　退款数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_num_in = 1
            else:  # 有记录则累加
                refund_record.ref_num_in += 1
    update_model_fields(refund_record, update_fields=['ref_sed_num', 'ref_num_out', 'ref_num_in'])


def write_dinghuo_return_pro(refund):
    from common.modelutils import update_model_fields
    from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
    try:
        record = DailySupplyChainStatsOrder.objects.get(product_id=refund.outer_id)
        record.return_pro += refund.refund_num
        update_model_fields(record, update_fields=['return_pro'])
    except:
        return


def his_dinghuo_return_pro():
    """ 写入产品退货历史退货数量数据　"""
    from common.modelutils import update_model_fields
    from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
    from flashsale.pay.models_refund import SaleRefund
    # 已经收到货　或者　已经退货的　
    refunds = SaleRefund.objects.filter(
        good_status__in=(SaleRefund.BUYER_RECEIVED, SaleRefund.BUYER_RETURNED_GOODS)).exclude(
        status=SaleRefund.REFUND_CLOSED)
    for refund in refunds:
        record = DailySupplyChainStatsOrder.objects.filter(product_id=refund.outer_id)
        if record.exists():
            record[0].return_pro += refund.refund_num
            update_model_fields(record[0], update_fields=['return_pro'])

