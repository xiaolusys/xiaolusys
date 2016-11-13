# coding=utf-8
import time
import datetime
import calendar
from celery.task import task
from django.conf import settings
from common.utils import format_time, format_datetime
from shopback.refunds.models import Refund
from shopback.users.models import User
from shopapp.taobao import apis
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('django.request')


@task(max_retries=3)
def saveUserRefundOrderTask(user_id, update_from=None, update_to=None):
    update_from = format_datetime(update_from)
    update_to = format_datetime(update_to)

    has_next = True
    cur_page = 1

    while has_next:

        response_list = apis.taobao_refunds_receive_get(tb_user_id=user_id, page_no=cur_page,
                                                        page_size=settings.TAOBAO_PAGE_SIZE, start_modified=update_from,
                                                        end_modified=update_to)

        refund_list = response_list['refunds_receive_get_response']
        if refund_list['total_results'] > 0:
            for r in refund_list['refunds']['refund']:
                refund, state = Refund.objects.get_or_create(refund_id=r['refund_id'])
                refund.save_refund_through_dict(user_id, r)

        total_nums = refund_list['total_results']
        cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums < total_nums
        cur_page += 1


@task()
def updateAllUserRefundOrderTask(days=0, update_from=None, update_to=None):
    hander_update = update_from and update_to
    if not hander_update:
        dt = datetime.datetime.now()
        update_from = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0) - datetime.timedelta(days, 0, 0)
        update_to = dt

    users = User.effect_users.filter(type__in=('B', 'C'))
    for user in users:
        saveUserRefundOrderTask(user.visitor_id, update_from=update_from, update_to=update_to)


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
def fifDaysRateFlush(days=30):
    """ 每天定时执行 刷新过去30天的数据 """
    for i in range(days):
        target_day = datetime.datetime.today() - datetime.timedelta(days=i)
        print u"target_day:%s" % target_day
        refDataToMol(target_day=target_day)


from flashsale.pay.models import SaleOrder, SaleRefund
from shopback.refunds.models_refund_rate import PayRefNumRcord
from shopback.items.models import Product
from flashsale.dinghuo.models import DailySupplyChainStatsOrder
from common.modelutils import update_model_fields
from shopback.refunds.models_refund_rate import ProRefunRcord
from supplychain.supplier.models import SaleProduct
from django.db.models import F


@task()
def taskRefundRecord(obj):
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
                refund_record.ref_sed_num = F('ref_sed_num') + 1
            write_dinghuo_return_pro(obj)  # 计算到订货表中的退货数量
        if order.status in (SaleOrder.WAIT_SELLER_SEND_GOODS,):
            # 如果　未发货　　则　算入　24小时外未发货退款数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_num_out = 1
            else:  # 有记录则累加
                refund_record.ref_num_out = F('ref_num_out') + 1
    else:  # 如果24小时内　已发货   则　算入　发货后退货数量
        if order.status in (SaleOrder.WAIT_BUYER_CONFIRM_GOODS, SaleOrder.TRADE_BUYER_SIGNED):
            # 如果　已发货　　则　算入　发货后退货数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_sed_num = 1
            else:  # 有记录则累加
                refund_record.ref_sed_num = F('ref_sed_num') + 1
            write_dinghuo_return_pro(obj)  # 计算到订货表中的退货数量
        else:  # 否则　算入　24小时内　　　退款数量
            if state:  # 新建记录　填写　付款成功数量
                refund_record.ref_num_in = 1
            else:  # 有记录则累加
                refund_record.ref_num_in = F('ref_num_in') + 1
    update_model_fields(refund_record, update_fields=['ref_sed_num', 'ref_num_out', 'ref_num_in'])
    # 添加产品的退货记录
    record_pro(obj)
    # 记录供应商的一些参数
    record_supplier(obj)


def record_supplier(obj):
    """ 记录某供应商下产品的的退款状况：　总退款件数　总退款额
        Args: obj SaleRefund instance
        Returns: None
        Raises: None
    """
    try:
        item_id = obj.item_id  # 商品id
        pro = Product.objects.get(id=item_id)  # 找到商品
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_refund_num = F('total_refund_num') + obj.refund_num
            supplier.total_refund_amount = F('total_refund_amount') + obj.total_fee
            update_model_fields(supplier, update_fields=['total_refund_num', 'total_refund_amount'])  # 更新字段
    except:
        return


def write_dinghuo_return_pro(refund):
    try:
        record = DailySupplyChainStatsOrder.objects.get(product_id=refund.outer_id)
        record.return_pro += refund.refund_num
        update_model_fields(record, update_fields=['return_pro'])
    except:
        return


def his_dinghuo_return_pro():
    """ 写入产品退货历史退货数量数据　"""
    # 已经收到货　或者　已经退货的　
    refunds = SaleRefund.objects.filter(
        good_status__in=(SaleRefund.BUYER_RECEIVED, SaleRefund.BUYER_RETURNED_GOODS)).exclude(
        status=SaleRefund.REFUND_CLOSED)
    for refund in refunds:
        record = DailySupplyChainStatsOrder.objects.filter(product_id=refund.outer_id())
        if record.exists():
            record = record[0]
            refund_num = refund.refund_num
            record.return_pro += refund_num
            update_model_fields(record, update_fields=['return_pro'])


def his_refund_record():
    """ 写入产品的退货记录　"""
    # 所有退款单
    refunds = SaleRefund.objects.all().exclude(status=SaleRefund.REFUND_CLOSED)
    for ref in refunds:
        record_pro(ref)


def record_pro(ref):
    order = ref.saleorder
    if order is None:
        return
    trade = order.sale_trade
    # 订单的付款时间　与　退款单的创建时间　比较　判断是否属于24小时内
    pay_time = trade.pay_time
    if pay_time is None:
        return
    ref_created = ref.created
    after_24_h = pay_time + datetime.timedelta(days=1)
    pro_ref_rcd, state = ProRefunRcord.objects.get_or_create(product=ref.item_id)
    if ref_created > after_24_h:
        # 表示24小时外申请
        if ref.good_status in (SaleRefund.BUYER_RECEIVED, SaleRefund.BUYER_RETURNED_GOODS):
            if state:
                pro_ref_rcd.ref_sed_num = ref.refund_num
            else:
                pro_ref_rcd.ref_sed_num += ref.refund_num
        else:
            if state:
                pro_ref_rcd.ref_num_out = ref.refund_num
            else:
                pro_ref_rcd.ref_num_out += ref.refund_num
    else:
        # 表示24小时内申请
        if ref.good_status in (SaleRefund.BUYER_RECEIVED, SaleRefund.BUYER_RETURNED_GOODS):
            if state:
                pro_ref_rcd.ref_sed_num = ref.refund_num
            else:
                pro_ref_rcd.ref_sed_num += ref.refund_num
        else:
            if state:
                pro_ref_rcd.ref_num_in = ref.refund_num
            else:
                pro_ref_rcd.ref_num_in += ref.refund_num

    contactor = ref.sale_contactor() if ref.sale_contactor() is not None else 0

    pro_model = ref.pro_model() if ref.pro_model() is not None else 0

    pro_ref_rcd.contactor = contactor
    pro_ref_rcd.pro_model = pro_model
    if pro_ref_rcd.sale_time() is not None:
        # 这里如果重新上架的产品产生的退款会将以前的上架日期覆盖掉
        pro_ref_rcd.sale_date = pro_ref_rcd.sale_time()

    update_model_fields(pro_ref_rcd, update_fields=['ref_sed_num', 'ref_num_out', 'ref_num_in', 'contactor',
                                                    'pro_model', 'sale_date'])


def insert_field_hist_pro_rcd():
    """ ProRefunRcord 添加字段后　将对应产品ｉd的　款式id以及接洽人　写入 对应字段　"""
    pro_rcds = ProRefunRcord.objects.all()
    for rcd in pro_rcds:
        pro = rcd.item_product()
        if pro is None:
            continue
        model_id = 0 if pro.model_id is None else pro.model_id
        rcd.pro_model = model_id
        if pro.sale_product > 0:
            sal_pro = SaleProduct.objects.get(id=pro.sale_product)
            contactor = 0 if sal_pro.contactor is None else sal_pro.contactor
            rcd.contactor = contactor
        update_model_fields(rcd, update_fields=['pro_model', 'contactor'])


def write_rcd_column_sale_date():
    """ ProRefunRcord 添加日期字段后　将对应产品上架日期写入 对应字段　"""
    pro_rcds = ProRefunRcord.objects.all()
    print(u"条数：", pro_rcds.count())
    for rcd in pro_rcds:
        sale_date = rcd.sale_time()
        if sale_date is None:
            continue
        rcd.sale_date = sale_date
        update_model_fields(rcd, update_fields=['sale_date'])


def handler_Refund_Send_Num():
    """
    2015-12-08 脏数据处理　taskRefundRecord　中发货后的数据出现问题
    """
    time_from = datetime.datetime(2015, 11, 1)
    time_to = datetime.datetime(2015, 12, 9)
    print "time_from:", time_from, "time_to", time_to
    rcds = PayRefNumRcord.objects.filter(date_cal__gte=time_from, date_cal__lte=time_to)

    for rcd in rcds:
        refra = PayRefundRate.objects.get(date_cal=rcd.date_cal)  # 找到总的退款率记录
        ref_num = refra.ref_num  # 总退款数量
        ref_num_out = rcd.ref_num_out
        ref_num_in = rcd.ref_num_in
        rcd.ref_sed_num = ref_num - ref_num_out - ref_num_in  # 发货后等于总的减去２４外和内
        print "{0}记录,总退款 {1},发货后退款 {2}".format(rcd.date_cal, ref_num, rcd.ref_sed_num)
        rcd.save()
