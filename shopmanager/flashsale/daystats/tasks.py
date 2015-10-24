# -*- encoding:utf8 -*-
from __future__ import division
import datetime
from django.db.models import F, Sum
from celery.task import task

from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models import Clicks, CarryLog
from flashsale.pay.models import Customer
from  flashsale.pay.models_refund import SaleRefund
from .models import DailyStat, PopularizeCost

import logging
from flashsale.xiaolumm.models import XiaoluMama
from django.conf import settings
from shopapp.weixin.models import get_Unionid
from calendar import monthrange
from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
from supplychain.supplier.models import SaleProduct, SaleSupplier, SupplierCharge, SaleCategory


logger = logging.getLogger('celery.handler')


@task()
def task_Push_Sales_To_DailyStat(target_date):
    df = datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    dt = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    seven_day_ago = target_date - datetime.timedelta(days=7)
    seven_day_before = datetime.datetime(seven_day_ago.year, seven_day_ago.month, seven_day_ago.day, 0, 0, 0)
    # click_count = ClickCount.objects.get(date=target_date)
    # cc_stats = click_count.aggregate(total_user_num=Sum('user_num'),
    # total_valid_num=Sum('valid_num'))
    clicks = Clicks.objects.filter(click_time__range=(df, dt))

    total_click_count = clicks.values('linkid', 'openid').distinct().count()
    total_user_num = clicks.values('openid').distinct().count()
    total_valid_count = clicks.filter(isvalid=True).values('linkid', 'openid').distinct().count()

    total_old_visiter_num = 0
    click_openids = clicks.values('openid').distinct()
    for stat in click_openids:
        last_clicks = Clicks.objects.filter(click_time__lte=df, openid=stat['openid'])
        if last_clicks.count() > 0:
            total_old_visiter_num += 1

    shoping_stats = StatisticsShopping.objects.filter(shoptime__range=(df, dt))
    total_payment = shoping_stats.aggregate(total_payment=Sum('wxorderamount')).get('total_payment') or 0
    total_order_num = shoping_stats.values('wxorderid').distinct().count()
    total_buyer_num = shoping_stats.values('openid').distinct().count()

    total_old_buyer_num = 0
    seven_old_buyer_num = 0

    total_old_order_num = 0
    stats_openids = shoping_stats.values('openid').distinct()
    for stat in stats_openids:
        day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=df, openid=stat['openid'])
        if day_ago_stats.count() > 0:
            total_old_buyer_num += 1
            total_old_order_num += shoping_stats.filter(openid=stat['openid']).values('wxorderid').distinct().count()

        seven_day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=seven_day_before,
                                                                openid=stat['openid'])
        if seven_day_ago_stats.count() > 0:
            seven_old_buyer_num += 1

    dstat, state = DailyStat.objects.get_or_create(day_date=target_date)
    dstat.total_click_count = total_click_count
    dstat.total_valid_count = total_valid_count
    dstat.total_visiter_num = total_user_num
    dstat.total_new_visiter_num = total_user_num - total_old_visiter_num

    dstat.total_payment = total_payment
    dstat.total_order_num = total_order_num
    dstat.total_new_order_num = total_order_num - total_old_order_num

    dstat.total_buyer_num = total_buyer_num
    dstat.total_old_buyer_num = total_old_buyer_num
    dstat.seven_buyer_num = seven_old_buyer_num
    dstat.save()


@task()
def task_Calc_Sales_Stat_By_Day(pre_day=1):
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)

    task_Push_Sales_To_DailyStat(pre_date)


def carrylog_Handler_By_Log_Type(date, log_type=CarryLog.ORDER_REBETA):
    carrylogs = CarryLog.objects.filter(log_type=log_type, carry_date=date).exclude(status=CarryLog.CANCELED)  # 指定的类型
    carry = carrylogs.aggregate(total_carry=Sum('value')).get('total_carry') or 0
    carry = carry / 100.0
    return carry


def carrylogs_By_Date(date):
    carrylog_order = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.ORDER_REBETA)  # 订单返现
    carrylog_click = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.CLICK_REBETA)  # 点击返现
    carrylog_thousand = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.THOUSAND_REBETA)  # 千元提成
    carrylog_agency = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.AGENCY_SUBSIDY)  # 代理补贴
    carrylog_recruit = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.MAMA_RECRUIT)  # 招募奖金
    carrylog_order_buy = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.ORDER_BUY)  # 消费支出
    carrylog_refund_return = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.REFUND_RETURN)  # 退款返现
    carrylog_cash_out = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.CASH_OUT)  # 提现
    carrylog_deposit = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.DEPOSIT)  # 押金
    carrylog_red_packet = carrylog_Handler_By_Log_Type(date=date, log_type=CarryLog.ORDER_RED_PAC)  # 订单红包

    total_carrys_out = CarryLog.objects.filter(carry_type=CarryLog.CARRY_OUT, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 妈妈支出
    total_carry_out = total_carrys_out.aggregate(total_out=Sum('value')).get(
        'total_out') or 0
    total_carry_out = total_carry_out / 100.0
    # carry_in
    total_carrys_in = CarryLog.objects.filter(carry_type=CarryLog.CARRY_IN, carry_date=date).exclude(
        log_type=CarryLog.DEPOSIT).exclude(log_type=CarryLog.REFUND_RETURN).exclude(
        status=CarryLog.CANCELED)  # 推广费用(不包含押金，不包含退款返现)
    total_carry_in = total_carrys_in.aggregate(total_in=Sum('value')).get(
        'total_in') or 0
    total_carry_in = total_carry_in / 100.0

    data = [carrylog_order, carrylog_click, carrylog_thousand, carrylog_agency, carrylog_recruit,
            carrylog_order_buy, carrylog_refund_return, carrylog_cash_out, carrylog_deposit,
            total_carry_in, total_carry_out, carrylog_red_packet]
    return data


@task()
def task_PopularizeCost_By_Day(pre_day=1):
    # PopularizeCost
    # 写昨天的数据（确认状态 AND pending 状态的）
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)

    data = carrylogs_By_Date(pre_date)  # 接收计算数据
    # 创建推广记录
    popu_cost, state = PopularizeCost.objects.get_or_create(date=pre_date)
    popu_cost.carrylog_order = data[0]
    popu_cost.carrylog_click = data[1]
    popu_cost.carrylog_thousand = data[2]
    popu_cost.carrylog_agency = data[3]
    popu_cost.carrylog_recruit = data[4]

    popu_cost.carrylog_order_buy = data[5]
    popu_cost.carrylog_refund_return = data[6]
    popu_cost.carrylog_cash_out = data[7]
    popu_cost.carrylog_deposit = data[8]
    popu_cost.total_carry_in = data[9]

    popu_cost.total_carry_out = data[10]
    popu_cost.carrylog_red_packet = data[11]
    popu_cost.save()

    twelve_date = datetime.date.today() - datetime.timedelta(days=12)

    # 修改12天前的推广记录
    try:
        twelve_date_popu_cost = PopularizeCost.objects.get(date=twelve_date)
        data = carrylogs_By_Date(twelve_date)

        twelve_date_popu_cost.carrylog_order = data[0]
        twelve_date_popu_cost.carrylog_click = data[1]
        twelve_date_popu_cost.carrylog_thousand = data[2]
        twelve_date_popu_cost.carrylog_agency = data[3]
        twelve_date_popu_cost.carrylog_recruit = data[4]

        twelve_date_popu_cost.carrylog_order_buy = data[5]
        twelve_date_popu_cost.carrylog_refund_return = data[6]
        twelve_date_popu_cost.carrylog_cash_out = data[7]
        twelve_date_popu_cost.carrylog_deposit = data[8]
        twelve_date_popu_cost.total_carry_in = data[9]

        twelve_date_popu_cost.total_carry_out = data[10]
        twelve_date_popu_cost.carrylog_red_packet = data[11]
        twelve_date_popu_cost.save()
    except PopularizeCost.DoesNotExist:
        logger.warning('First time running no popularizecost data to search ')


import os
import csv
STAT_DIR = "stat_backup"

@task(max_retry=3, default_retry_delay=5)
def task_calc_xlmm(start_time_str, end_time_str, old=True):
    """计算某个月内所有购买的人数和小鹿妈妈数量，重复购买"""
    try:
        if old:
            file_dir = os.path.join(settings.DOWNLOAD_ROOT, STAT_DIR)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            file_name = u'month_sale.csv'
            file_path_name = os.path.join(file_dir, file_name)

            result_list = []
            my_file = file(file_path_name, 'rb')
            reader = csv.reader(my_file)
            for line in reader:
                result_list.append(line)
            my_file.close()
            return result_list
        else:
            today = datetime.date.today()
            if start_time_str:
                year, month, day = start_time_str.split('-')
                start_date = datetime.date(int(year), int(month), int(day))
                if start_date > today:
                    start_date = today
            else:
                start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
            if end_time_str:
                year, month, day = end_time_str.split('-')
                end_date = datetime.date(int(year), int(month), int(day))
            else:
                end_date = today
            """找出选择的开始月份和结束月份"""
            start_month = start_date.month
            end_month = end_date.month
            month_range = range(start_month, end_month + 1)
            result_list = []
            for month in month_range:
                month_start_date = datetime.date(start_date.year, month, 1)
                month_end_date = datetime.date(end_date.year, month + 1, 1)

                all_purchase = StatisticsShopping.objects.filter(shoptime__gte=month_start_date,
                                                                 shoptime__lt=month_end_date).values(
                    "openid").distinct()
                all_purchase_num = all_purchase.count()
                history_purchase = StatisticsShopping.objects.filter(shoptime__lt=month_start_date).values(
                    "openid").distinct()
                history_purchase_detail = set([val['openid'] for val in history_purchase])

                all_purchase_detail = set([val['openid'] for val in all_purchase])
                all_purchase_detail_unionid = set(
                    [get_Unionid(val['openid'], settings.WEIXIN_APPID) for val in all_purchase])

                repeat_user = all_purchase_detail & history_purchase_detail
                repeat_user_unionid = set([get_Unionid(val, settings.WEIXIN_APPID) for val in repeat_user])

                all_xlmm = XiaoluMama.objects.filter(charge_status=u'charged', agencylevel=2).values("openid").distinct()
                all_xlmm_detail = set([val['openid'] for val in all_xlmm])

                repeat_xlmm = repeat_user_unionid & all_xlmm_detail
                xlmm_num = all_purchase_detail_unionid & all_xlmm_detail
                result_list.append(
                    (month, all_purchase_num, len(repeat_user), len(repeat_xlmm), len(xlmm_num))
                )


            file_dir = os.path.join(settings.DOWNLOAD_ROOT, STAT_DIR)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            file_name = u'month_sale.csv'
            file_path_name = os.path.join(file_dir, file_name)



            csvfile = file(file_path_name, 'wb')
            writer = csv.writer(csvfile)
            data = result_list
            writer.writerows(data)
            csvfile.close()
            return result_list
    except Exception, exc:
        raise task_calc_xlmm.retry(exc=exc)


from django.db import connection
from shopback.items.models import Product
from django.db.models import Q



@task(max_retry=3, default_retry_delay=5)
def task_calc_hot_sale(start_time_str, end_time_str, category, limit=100):
    """计算热销商品"""
    try:
        today = datetime.date.today()
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""

        sql = '''select substring(outer_id, 1, CHAR_LENGTH(outer_id) -1) as souter_id,sum(num) as cnum from shop_trades_mergeorder
        where sys_status= 'IN_EFFECT' and pay_time between %s and %s and is_merge= 0 and CHAR_LENGTH(outer_id)>= 9
        group by souter_id
        order by cnum desc
        limit %s'''
        cursor = connection.cursor()
        cursor.execute(sql, [start_date, end_date, limit])
        plist = cursor.fetchall()
        cursor.close()
        result_list = []
        for p_t in plist:
            p_outer = p_t[0].strip()
            p_sales = int(p_t[1])
            p_products = Product.objects.filter(outer_id__startswith=p_outer, status='normal')
            if p_products.count() > 0 and (True if not category else p_outer.startswith(category)):
                product_item = p_products[0]
                cost = product_item.cost
                agent_price = product_item.agent_price
                sale_product_id = p_products[0].sale_product
                product_category = p_products[0].category.__unicode__() if p_products[0].category else ""
                tui_huo = 0
                daily_data = DailySupplyChainStatsOrder.objects.filter(product_id__startswith=p_outer)
                for one_data in daily_data:
                    tui_huo += one_data.return_num
                supplier_list = ""
                sale_contactor = ""
                if sale_product_id != 0:
                    one_sale_product = SaleProduct.objects.filter(id=sale_product_id)
                    if one_sale_product.count() > 0:
                        supplier_list = one_sale_product[0].sale_supplier.supplier_name
                        sale_contactor = one_sale_product[0].contactor.username if one_sale_product[0].contactor else ""
                p_dict = {"p_outer": p_outer, "p_name": product_item.name,
                          "sale_time": product_item.sale_time.strftime("%Y-%m-%d") if product_item.sale_time else "",
                          "p_sales": p_sales, "cost": cost, "agent_price": agent_price, "p_cost": cost * int(p_sales),
                          "p_agent_price": agent_price * int(p_sales), "suppliers": supplier_list,
                          "pic_path": product_item.pic_path, "sale_contactor": sale_contactor,
                          "tui_huo": tui_huo, "product_category": product_category}
                result_list.append(p_dict)
        return result_list

    except Exception, exc:
        raise task_calc_hot_sale.retry(exc=exc)

@task(max_retry=3, default_retry_delay=5)
def task_calc_sale_bad(start_time_str, end_time_str, category, limit=100):
    """计算滞销商品"""
    try:
        today = datetime.date.today()
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""

        sql = '''select substring(outer_id, 1, CHAR_LENGTH(outer_id) -1) as souter_id,sum(num) as cnum from shop_trades_mergeorder
        where sys_status= 'IN_EFFECT' and pay_time between %s and %s and is_merge= 0 and CHAR_LENGTH(outer_id)>= 9
        group by souter_id
        order by cnum asc
        limit %s'''
        cursor = connection.cursor()
        cursor.execute(sql, [start_date, end_date, limit])
        plist = cursor.fetchall()
        cursor.close()
        result_list = []
        for p_t in plist:
            p_outer = p_t[0].strip()
            p_sales = int(p_t[1])
            p_products = Product.objects.filter(outer_id__startswith=p_outer, status='normal')
            if p_products.count() > 0 and (True if not category else p_outer.startswith(category)):
                product_item = p_products[0]
                cost = product_item.cost
                agent_price = product_item.agent_price
                sale_product_id = p_products[0].sale_product
                product_category = p_products[0].category.__unicode__() if p_products[0].category else ""
                tui_huo = 0
                daily_data = DailySupplyChainStatsOrder.objects.filter(product_id__startswith=p_outer)
                for one_data in daily_data:
                    tui_huo += one_data.return_num
                supplier_list = ""
                sale_contactor = ""
                if sale_product_id != 0:
                    one_sale_product = SaleProduct.objects.filter(id=sale_product_id)
                    if one_sale_product.count() > 0:
                        supplier_list = one_sale_product[0].sale_supplier.supplier_name
                        sale_contactor = one_sale_product[0].contactor.username if one_sale_product[0].contactor else ""
                p_dict = {"p_outer": p_outer, "p_name": product_item.name,
                          "sale_time": product_item.sale_time.strftime("%Y-%m-%d") if product_item.sale_time else "",
                          "p_sales": p_sales, "cost": cost, "agent_price": agent_price, "p_cost": cost * int(p_sales),
                          "p_agent_price": agent_price * int(p_sales), "suppliers": supplier_list,
                          "pic_path": product_item.pic_path, "sale_contactor": sale_contactor,
                          "tui_huo": tui_huo, "product_category": product_category}
                result_list.append(p_dict)
        return result_list

    except Exception, exc:
        raise task_calc_sale_bad.retry(exc=exc)

@task(max_retry=3, default_retry_delay=5)
def task_calc_stock_top(start_time_str, end_time_str, limit=100):
    """计算库存多的商品"""
    try:
        today = datetime.date.today()
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))

        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""

        outer_idset = set([])
        sale_top = {}
        product_qs = Product.objects.filter(status=Product.NORMAL, collect_num__gt=0).extra(
            where=["CHAR_LENGTH(outer_id)>=9"]) \
            .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8")).filter(
            sale_time__range=(start_date, end_date))

        for product in product_qs:
            outer_id = product.outer_id
            router_id = outer_id[0:-1]
            if outer_id in outer_idset:
                continue
            outer_idset.add(outer_id)
            if router_id not in sale_top:
                sale_top[router_id] = {'name': product.name, 'collect_num': product.collect_num}
            else:
                sale_top[router_id]['collect_num'] += product.collect_num

        sale_list = sorted(sale_top.items(), key=lambda d: d[1]['collect_num'], reverse=True)
        return sale_list[0:limit]

    except Exception, exc:
        raise task_calc_stock_top.retry(exc=exc)


def get_new_user(user_data, old_user):
    new_user = []
    for val in user_data:
        if val not in old_user:
            new_user.append(val[0])
    return new_user


@task(max_retry=3, default_retry_delay=5)
def task_calc_new_user_repeat(start_date, end_date):
    """计算新用户的重复购买率"""
    start_month = start_date.month
    end_month = end_date.month
    month_march = "2015-03-01"
    stats_month_range = range(start_month, end_month)
    month_range = range(start_month + 1, end_month + 1)
    result_data_list = []
    try:
        for target_month in stats_month_range:
            month_date_begin = datetime.datetime(start_date.year, target_month, 1)
            month_date_end = datetime.datetime(start_date.year, target_month + 1, 1)

            """找出目标月的所有购买用户"""
            user_sql = 'select openid from flashsale_tongji_shopping where shoptime>="{0}" and shoptime<="{1}" and openid!="" group by openid'.format(
                month_date_begin, month_date_end)
            cursor = connection.cursor()
            cursor.execute(user_sql)
            user_data = cursor.fetchall()
            all_user_num = len(user_data)

            """找出目标月之前的所有用户"""
            old_user_sql = 'select openid from flashsale_tongji_shopping where shoptime<="{0}" and shoptime>="{1}" group by openid'.format(
                month_date_begin, month_march)
            cursor.execute(old_user_sql)
            old_user_data = cursor.fetchall()

            new_user = get_new_user(user_data, old_user_data)
            new_user_quantity = len(new_user)
            result_data_dict = {"month": target_month, "new_user": new_user_quantity}
            user_data_list = []
            for i in month_range:
                if target_month >= i:
                    user_data_list.append("None")
                else:
                    stats_date_begin = datetime.datetime(start_date.year, i, 1)
                    stats_date_end = datetime.datetime(start_date.year, i + 1, 1)
                    count_month = StatisticsShopping.objects.filter(
                        shoptime__range=(stats_date_begin, stats_date_end)).filter(openid__in=new_user).values(
                        'openid').distinct().count()

                    temp_dict = {"num": count_month, "rec_num": float(
                        '%0.2f' % (count_month * 100 / new_user_quantity if new_user_quantity else 0))}
                    user_data_list.append(temp_dict)
            result_data_dict["user_data"] = user_data_list
            result_data_list.append(result_data_dict)
        return result_data_list
    except Exception, exc:
        raise task_calc_new_user_repeat.retry(exc=exc)

from shopback.trades.models import MergeTrade


@task(max_retry=3, default_retry_delay=5)
def task_calc_package(start_date, end_date, old=True):
    """计算包裹数量"""
    try:
        if old:
            file_dir = os.path.join(settings.DOWNLOAD_ROOT, STAT_DIR)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            file_name = u'month_package.csv'
            file_path_name = os.path.join(file_dir, file_name)


            result_list = []
            my_file = file(file_path_name, 'rb')
            reader = csv.reader(my_file)
            for line in reader:
                result_list.append(line)
            my_file.close()
            return result_list
        else:
            start_month = start_date.month
            end_month = end_date.month

            month_range = range(start_month, end_month + 1)
            result_list = []
            for month in month_range:
                month_start_date = datetime.date(start_date.year, month, 1)
                month_end_date = datetime.date(end_date.year, month + 1, 1)
                total_sale_amount = DailyStat.objects.filter(day_date__gte=month_start_date,
                                                             day_date__lt=month_end_date).aggregate(
                    total_sale_amount=Sum('total_payment')).get('total_sale_amount') or 0
                total_order_num = DailyStat.objects.filter(day_date__gte=month_start_date,
                                                           day_date__lt=month_end_date).aggregate(
                    total_sale_order=Sum('total_order_num')).get('total_sale_order') or 0
                shoping_stats = StatisticsShopping.objects.filter(shoptime__gte=month_start_date,
                                                                  shoptime__lt=month_end_date)
                total_sale_num = 0
                sm = {}
                for shop_stat in shoping_stats:
                    tm = '%s-%s-%s' % (shop_stat.shoptime.year, shop_stat.shoptime.month, shop_stat.shoptime.day)
                    if tm in sm:
                        sm[tm].add(shop_stat.openid)
                    else:
                        sm[tm] = set([shop_stat.openid])
                for s, m in sm.iteritems():
                    total_sale_num += len(m)

                total_package_num = MergeTrade.objects.filter(type__in=("sale", "wx")).filter(
                    sys_status=u'FINISHED').filter(weight_time__gte=month_start_date, weight_time__lt=month_end_date).count()
                result_list.append(
                    (month, total_sale_amount / 100, total_order_num, total_package_num, total_sale_num))

            file_dir = os.path.join(settings.DOWNLOAD_ROOT, STAT_DIR)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            file_name = u'month_package.csv'
            file_path_name = os.path.join(file_dir, file_name)

            csv_file = file(file_path_name, 'wb')
            writer = csv.writer(csv_file)
            data = result_list
            writer.writerows(data)
            csv_file.close()
            return result_list
    except Exception, exc:
        raise task_calc_package.retry(exc=exc)



@task(max_retry=1, default_retry_delay=5)
def task_calc_performance_by_user(start_date, end_date, category="0"):
    """计算买手绩效"""
    try:
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        if category == "0":
            all_created_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time))
            all_sale_product = SaleProduct.objects.filter(sale_time__range=(start_date_time, end_date_time),
                                                          status=SaleProduct.SCHEDULE)
        else:
            all_created_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time),
                                                             sale_category__parent_cid=category)
            all_sale_product = SaleProduct.objects.filter(sale_time__range=(start_date_time, end_date_time),
                                                          sale_category__parent_cid=category,
                                                          status=SaleProduct.SCHEDULE)

        result_data = []
        result_contactors = set()
        all_order_data = DailySupplyChainStatsOrder.objects.filter(sale_time__range=(start_date_time, end_date_time))
        if category == "1":
            all_order_data = DailySupplyChainStatsOrder.objects.filter(
                sale_time__range=(start_date_time, end_date_time)).filter(product_id__startswith='9')
        elif category == "2":
            all_order_data = DailySupplyChainStatsOrder.objects.filter(
                sale_time__range=(start_date_time, end_date_time)).filter(product_id__startswith='8')
        #获取商品的销售情况
        for one_order_data in all_order_data:
            try:
                one_product = Product.objects.get(outer_id=one_order_data.product_id)
                sale_product_bean = SaleProduct.objects.get(id=one_product.sale_product)
                one_contactor = sale_product_bean.contactor.username
                if one_contactor in result_contactors:
                    for one_data in result_data:
                        if one_data["username"] == one_contactor:
                            one_data["all_sale_num"] += one_order_data.sale_num
                            one_data["all_sale_cost"] += one_order_data.cost_of_product
                            one_data["all_sale_money"] += one_order_data.sale_cost_of_product
                            one_data["all_tui_kuan"] += one_order_data.return_num
                            one_data["tui_kuan_money"] += one_order_data.return_num * one_product.agent_price
                else:
                    result_contactors.add(one_contactor)
                    
                    one_temp_data = {"username": one_contactor,
                                     "all_sale_num": one_order_data.sale_num,
                                     "all_sale_cost": one_order_data.cost_of_product,
                                     "all_sale_money": one_order_data.sale_cost_of_product,
                                     "all_tui_kuan": one_order_data.return_num,
                                     "tui_kuan_money": one_order_data.return_num * one_product.agent_price}
                    result_data.append(one_temp_data)
            except:
                continue
        all_contactors = (e['contactor__username'] for e in
                          all_created_product.values("contactor__username").distinct())
        all_sale_contactors = (e['contactor__username'] for e in
                               all_sale_product.values("contactor__username").distinct())
        all_contactors = set(all_contactors)
        all_sale_contactors = set(all_sale_contactors)
        contactors = result_contactors | all_contactors | all_sale_contactors
        for contactor in contactors:
            charger_product = all_created_product.filter(contactor__username=contactor)
            choose_sale_num = charger_product.count()
            charger_product_shelf = all_sale_product.filter(contactor__username=contactor)
            shelf_sale_num = charger_product_shelf.count()
            shelf_percent = 0 if choose_sale_num == 0 else round(shelf_sale_num / choose_sale_num, 2)
            is_in = False
            for one_data in result_data:
                if one_data["username"] == contactor:
                    is_in = True
                    one_data["choose_sale_num"] = choose_sale_num
                    one_data["shelf_sale_num"] = shelf_sale_num
                    one_data["shelf_percent"] = shelf_percent
                    break
            if not is_in:
                result_data.append({"username": contactor,
                                    "choose_sale_num": choose_sale_num,
                                    "shelf_sale_num": shelf_sale_num,
                                    "shelf_percent": shelf_percent,
                                    "all_sale_num": 0,
                                    "all_sale_cost": 0,
                                    "all_sale_money": 0,
                                    "all_tui_kuan": 0,
                                    "tui_kuan_money": 0})

    except Exception, exc:
        raise task_calc_performance_by_user.retry(exc=exc)
    return result_data


REFUND_REASON = (u'其他', u'错拍', u'缺货', u'开线/脱色/脱毛/有色差/有虫洞',
                 u'发错货/漏发', u'没有发货', u'未收到货', u'与描述不符', u'退运费', u'发票问题', u'七天无理由退换货')

@task(max_retry=1, default_retry_delay=5)
def task_calc_performance_by_supplier(start_date, end_date, category="0"):
    """计算供应商"""
    try:
        #获取开始和结束时间
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)

        if category == "0":
            all_created_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time))
            all_sale_product = SaleProduct.objects.filter(sale_time__range=(start_date_time, end_date_time),
                                                          status=SaleProduct.SCHEDULE)
        else:
            all_created_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time),
                                                             sale_category__parent_cid=category)
            all_sale_product = SaleProduct.objects.filter(sale_time__range=(start_date_time, end_date_time),
                                                          sale_category__parent_cid=category,
                                                          status=SaleProduct.SCHEDULE)
        result_data = []
        result_suppliers = set()
        all_order_data = DailySupplyChainStatsOrder.objects.filter(sale_time__range=(start_date_time, end_date_time))
        if category == "1":
            all_order_data = DailySupplyChainStatsOrder.objects.filter(
                sale_time__range=(start_date_time, end_date_time)).filter(product_id__startswith='9')
        elif category == "2":
            all_order_data = DailySupplyChainStatsOrder.objects.filter(
                sale_time__range=(start_date_time, end_date_time)).filter(product_id__startswith='8')
        #获取商品的销售情况
        for one_order_data in all_order_data:
            try:
                one_product = Product.objects.get(outer_id=one_order_data.product_id)
                sale_product_bean = SaleProduct.objects.get(id=one_product.sale_product)
                one_supplier = sale_product_bean.sale_supplier
                supplier_name = one_supplier.supplier_name
                try:
                    category = one_supplier.category.__unicode__()
                except:
                    category = ""
                charge_info = SupplierCharge.objects.filter(supplier_id=one_supplier.id)
                try:
                    buyer_name = charge_info[0].employee.username
                except:
                    buyer_name = ""
                fa_huo_num = 0
                fa_huo_time = 0
                tuo_kuan = {u"七天无理由退换货": 0, u"与描述不符": 0, u"其他": 0,
                            u"发票问题": 0, u"发错货/漏发": 0, u"开线/脱色/脱毛/有色差/有虫洞": 0,
                            u"未收到货": 0, u"没有发货": 0, u"缺货": 0, u"退运费": 0, u"错拍": 0}
                all_refund = SaleRefund.objects.filter(item_id=one_product.id, created__gte=start_date_time)
                all_tui_kuan_ceshi = all_refund.count()
                if one_order_data.order_deal_time > 0 and one_order_data.goods_arrival_time > 0:
                            fa_huo_num = one_order_data.sale_num
                            fa_huo_time = (one_order_data.goods_arrival_time - one_order_data.order_deal_time)\
                                                                                * one_order_data.sale_num
                if one_supplier.id in result_suppliers:
                    for one_data in result_data:
                        if one_data["supplier_id"] == one_supplier.id:
                            one_data["all_sale_num"] += one_order_data.sale_num  #销售数量
                            one_data["all_sale_cost"] += one_order_data.cost_of_product #销售成本
                            one_data["all_sale_money"] += one_order_data.sale_cost_of_product #销售额
                            one_data["all_tui_kuan"] += one_order_data.return_num #退款数
                            one_data["tui_kuan_money"] += one_order_data.return_num * one_product.agent_price #退款钱
                            one_data["fa_huo_num"] += fa_huo_num
                            one_data["fa_huo_time"] += fa_huo_time
                            one_data["all_tui_kuan_ceshi"] += all_tui_kuan_ceshi
                            for k, v in one_data['tuo_kuan'].items():
                                one_data['tuo_kuan'][k] += all_refund.filter(reason=k).count()
                else:
                    result_suppliers.add(sale_product_bean.sale_supplier_id)
                    for one_reason in REFUND_REASON:
                        if one_reason in tuo_kuan:
                            tuo_kuan[one_reason] += all_refund.filter(reason=one_reason).count()
                        else:
                            tuo_kuan[one_reason] = all_refund.filter(reason=one_reason).count()
                    one_temp_data = {"supplier_id": sale_product_bean.sale_supplier_id,
                                     "supplier_name": supplier_name,
                                     "buyer_name": buyer_name,
                                     "category": category,
                                     "all_sale_num": one_order_data.sale_num,
                                     "all_sale_cost": one_order_data.cost_of_product,
                                     "all_sale_money": one_order_data.sale_cost_of_product,
                                     "all_tui_kuan": one_order_data.return_num,
                                     "tui_kuan_money": one_order_data.return_num * one_product.agent_price,
                                     "fa_huo_num": fa_huo_num,
                                     "fa_huo_time": fa_huo_time,
                                     "tuo_kuan": tuo_kuan,
                                     "all_tui_kuan_ceshi": all_tui_kuan_ceshi}
                    result_data.append(one_temp_data)
            except:
                continue

        for one_data in result_data:
            supplier_bean = SaleSupplier.objects.filter(id=one_data['supplier_id'])
            if supplier_bean.count() == 0:
                continue
            charger_product = all_created_product.filter(sale_supplier__id=one_data['supplier_id'])
            choose_sale_num = charger_product.count()
            one_data["choose_sale_num"] = choose_sale_num

            charger_product_shelf = all_sale_product.filter(sale_supplier__id=one_data['supplier_id'],
                                                            status=SaleProduct.SCHEDULE)
            shelf_sale_num = charger_product_shelf.count()
            one_data["shelf_sale_num"] = shelf_sale_num
            one_data["shelf_percent"] = 0 if choose_sale_num == 0 else round(shelf_sale_num/choose_sale_num, 2)
            fa_huo_time = one_data["fa_huo_time"]/one_data["fa_huo_num"] if one_data["fa_huo_num"] != 0 else 0
            one_data["fa_huo_time"] = format_time(fa_huo_time)

    except Exception, exc:
        raise task_calc_performance_by_supplier.retry(exc=exc)
    return result_data


def task_calc_performance_by_supplier_back(start_date, end_date, category="0"):
    """计算供应商_back"""
    try:
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        if category == "0":
            all_sale_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time))
        else:
            all_sale_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time),
                                                          sale_supplier__category_id=category)
        all_suppliers = all_sale_product.values("sale_supplier__id").distinct()
        result_data = []

        for supplier in all_suppliers:
            supplier_bean = SaleSupplier.objects.filter(id=supplier['sale_supplier__id'])
            if supplier_bean.count() == 0:
                continue
            one_temp = {"supplier_name": supplier_bean[0].supplier_name}
            charger_product = all_sale_product.filter(sale_supplier__id=supplier['sale_supplier__id'])
            choose_sale_num = charger_product.count()
            one_temp["choose_sale_num"] = choose_sale_num
            try:
                one_temp["category"] = supplier_bean[0].category.__unicode__()
            except:
                one_temp["category"] = ""
            charger_product_shelf = charger_product.filter(status=SaleProduct.SCHEDULE)
            shelf_sale_num = charger_product_shelf.count()
            one_temp["shelf_sale_num"] = shelf_sale_num
            one_temp["shelf_percent"] = 0 if choose_sale_num == 0 else round(shelf_sale_num/choose_sale_num, 2)
            all_sale_num = 0
            all_sale_cost = 0
            all_sale_money = 0
            all_tui_kuan = 0
            all_tui_kuan_ceshi = 0
            tui_kuan_money = 0
            fa_huo_time = 0
            fa_huo_num = 0
            one_temp["tuo_kuan"] = {u"七天无理由退换货": 0, u"与描述不符": 0, u"其他": 0, u"发票问题": 0, u"发错货/漏发": 0,
                                    u"开线/脱色/脱毛/有色差/有虫洞": 0, u"未收到货": 0, u"没有发货": 0, u"缺货": 0, u"退运费": 0, u"错拍": 0}
            for one_sale_product in charger_product_shelf:
                kucun_product = Product.objects.filter(sale_product=one_sale_product.id)

                for one_kucun_product in kucun_product:
                    one_product_data = DailySupplyChainStatsOrder.objects.filter(product_id=one_kucun_product.outer_id)
                    for stat_data in one_product_data:
                        all_sale_num += stat_data.sale_num
                        all_sale_cost += stat_data.cost_of_product
                        all_sale_money += stat_data.sale_cost_of_product
                        all_tui_kuan += stat_data.return_num
                        tui_kuan_money += stat_data.return_num * one_kucun_product.agent_price
                        if stat_data.order_deal_time > 0 and stat_data.goods_arrival_time > 0:
                            fa_huo_num += stat_data.sale_num
                            fa_huo_time += (stat_data.goods_arrival_time - stat_data.order_deal_time)\
                                                                                * stat_data.sale_num
                    all_refund = SaleRefund.objects.filter(item_id=one_kucun_product.id, created__gte=start_date_time)
                    all_tui_kuan_ceshi += all_refund.count()
                    for one_reason in REFUND_REASON:
                        if one_reason in one_temp["tuo_kuan"]:
                            one_temp["tuo_kuan"][one_reason] += all_refund.filter(reason=one_reason).count()
                        else:
                            one_temp["tuo_kuan"][one_reason] = all_refund.filter(reason=one_reason).count()
            fa_huo_time = fa_huo_time/fa_huo_num if fa_huo_num != 0 else 0
            fa_huo_time = format_time(fa_huo_time)
            one_temp["fa_huo_time"] = fa_huo_time
            one_temp["all_tui_kuan_ceshi"] = all_tui_kuan_ceshi
            one_temp["all_sale_num"] = all_sale_num
            one_temp["all_sale_cost"] = all_sale_cost
            one_temp["all_sale_money"] = all_sale_money
            one_temp["all_tui_kuan"] = all_tui_kuan
            one_temp["tui_kuan_money"] = tui_kuan_money
            charge_info = SupplierCharge.objects.filter(supplier_id=supplier_bean[0].id)
            one_temp["buyer_name"] = ""
            try:
                one_temp["buyer_name"] = charge_info[0].employee.username
            except:
                one_temp["buyer_name"] = ""
            result_data.append(one_temp)
    except Exception, exc:
        raise task_calc_performance_by_supplier.retry(exc=exc)
    return result_data


def format_time(time_of_long):
    days = 0
    tm_hours = 0
    if time_of_long > 0:
        days = time_of_long // 86400
        tm_hours = time_of_long % 86400 / 3600
    if days > 0 or tm_hours > 0:
        return str(int(days)) + "天" + str(round(tm_hours, 1)) + "小时"
    else:
        return ""


import collections
@task(max_retry=1, default_retry_delay=5)
def task_calc_sale_product(start_date, end_date, category="0"):
    """计算选品情况"""
    try:
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        all_sale_product = SaleProduct.objects.filter(created__range=(start_date_time, end_date_time)).exclude(
            status=SaleProduct.IGNORED)
        all_contactors = (e.contactor.username if e.contactor else "" for e in all_sale_product)
        all_contactors = set(all_contactors)
        print all_contactors
        nv_category = SaleCategory.objects.filter(is_parent=False, status=SaleCategory.NORMAL, parent_cid=2)
        child_category = SaleCategory.objects.filter(is_parent=False, status=SaleCategory.NORMAL, parent_cid=1)

        nv_data = []
        child_data = []
        for contactor in all_contactors:

            if contactor != "":
                temp_nv_dict = {}
                temp_child_dict = {}
                nv_num = 0
                child_num = 0
                for one_category in nv_category:
                    category_num = all_sale_product.filter(contactor__username=contactor,
                                                           sale_category=one_category).count()
                    nv_num += category_num
                    if len(temp_nv_dict) > 0:
                        temp_nv_dict[contactor][one_category.name] = category_num
                    else:
                        temp_nv_dict[contactor] = collections.OrderedDict({one_category.name: category_num})
                if nv_num != 0:
                    temp_nv_dict[contactor]["选款"] = nv_num
                    temp_nv_dict[contactor]["排期"] = SaleProduct.objects.filter(
                        sale_time__range=(start_date_time, end_date_time), contactor__username=contactor,
                        status=SaleProduct.SCHEDULE).count()
                    nv_data.append(temp_nv_dict)

                for one_category in child_category:
                    category_num = all_sale_product.filter(contactor__username=contactor,
                                                           sale_category=one_category).count()
                    child_num += category_num
                    if len(temp_child_dict) > 0:
                        temp_child_dict[contactor][one_category.name] = category_num
                    else:
                        temp_child_dict[contactor] = collections.OrderedDict({one_category.name: category_num})
                if child_num != 0:
                    temp_child_dict[contactor]["选款"] = child_num
                    temp_child_dict[contactor]["排期"] = SaleProduct.objects.filter(
                        sale_time__range=(start_date_time, end_date_time), contactor__username=contactor,
                        status=SaleProduct.SCHEDULE).count()
                    child_data.append(temp_child_dict)
    except Exception, exc:
        raise task_calc_sale_product.retry(exc=exc)
    return {"nv_data": nv_data, "child_data": child_data}

from django.core.serializers.json import DjangoJSONEncoder
import json
@task(max_retry=1, default_retry_delay=5)
def task_calc_operate_data(start_date, end_date, category="0"):
    """计算运营数据"""
    try:

        year, month, day = start_date.split('-')
        start_date = datetime.date(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date = datetime.date(int(year), int(month), int(day))

        all_data = DailySupplyChainStatsOrder.objects.filter(sale_time__range=(start_date, end_date))
        interval_day = (end_date - start_date).days
        if interval_day <= 0:
            return []
        result_data = []
        child_result_data = []
        for i in range(interval_day + 1):
            target_date = start_date+datetime.timedelta(days=i)
            daily_data = all_data.filter(sale_time=target_date)
            temp_data = []
            for one_data in daily_data:
                try:
                    one_product = Product.objects.get(outer_id=one_data.product_id)
                    product_category = get_category(one_product.category)
                    category_name = one_product.category.__unicode__()
                    if u"秒杀" in one_product.name:
                        continue
                except:
                    continue
                product_outer_id = one_data.product_id[0:len(one_data.product_id) - 1]
                is_already_in, temp_dict = judge_already(product_outer_id, temp_data)
                if is_already_in:
                    temp_dict['sale_num'] += one_data.sale_num
                    temp_dict['total_cost'] += one_product.cost * one_data.sale_num
                    temp_dict['total_sale_money'] += one_product.agent_price * one_data.sale_num
                    temp_dict['stock_num'] += one_product.collect_num
                    temp_dict['stock_cost'] += one_product.cost * one_product.collect_num
                else:
                    temp_data.append(
                        {"outer_id": product_outer_id,
                         "cost": one_product.cost,
                         "sale_num": one_data.sale_num,
                         "sale_time": target_date.strftime("%Y-%m-%d"),
                         "title": one_product.name.split("/")[0],
                         "group": product_category,
                         "category": category_name,
                         "agent_price": one_product.agent_price,
                         "total_cost": one_product.cost * one_data.sale_num,
                         "total_sale_money": one_product.agent_price * one_data.sale_num,
                         "stock_num": one_product.collect_num,
                         "stock_cost": one_product.cost * one_product.collect_num})
            child_result_data.extend(temp_data)
            result_data.extend(temp_data)
    except Exception, exc:
        raise task_calc_operate_data.retry(exc=exc)
    return {"table_list": result_data}


def judge_already(p_id, p_list):
    for one_dict in p_list:
        if p_id == one_dict["outer_id"]:
            return True, one_dict
    return False, []
def get_category(category):
    if not category.parent_cid:
        return unicode(category.name)
    try:
        p_cat = category.__class__.objects.get(cid=category.parent_cid).name
    except:
        p_cat = u'--'
    return p_cat