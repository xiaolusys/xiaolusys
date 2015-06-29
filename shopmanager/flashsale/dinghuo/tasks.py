# -*- coding:utf-8 -*-
__author__ = 'yann'
from celery.task import task
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models_stats import SupplyChainDataStats
from flashsale.dinghuo.models import OrderDetail, OrderList
import functions
import datetime
import function_of_task
import urllib2
import re
from django.db import connection


@task(max_retry=3, default_retry_delay=5)
def task_stats_daily_order_by_group(pre_day=1):
    try:
        today = datetime.date.today()
        target_day = today - datetime.timedelta(days=pre_day)
        start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
        end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
        order_qs = functions.get_source_orders(start_dt, end_dt)

        order_dict = functions.get_product_from_order(order_qs)
        data_stats_dict = {
            u"采购A": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0},
            u"采购B": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0},
            u"采购C": {"total_sale_num": 0, "total_cost_amount": 0, "total_sale_amount": 0,
                     "total_order_goods_quantity": 0, "total_order_goods_amount": 0}}
        for pro_id, sale_detail in order_dict.items():
            pro_bean = Product.objects.get(outer_id=pro_id)
            group = pro_bean.sale_group
            if group != u"None":
                group_name = group.name
                total_sale_num, total_cost_amount, total_sale_amount = 0, 0, 0
                for sku_outer_id, order_bean in sale_detail.items():
                    sku_qs = ProductSku.objects.filter(product__outer_id=pro_id, outer_id=sku_outer_id)
                    cost, agent_price = 0, 0
                    if sku_qs.count() > 0:
                        cost = sku_qs[0].cost
                        agent_price = sku_qs[0].agent_price
                        total_sale_num += order_bean['num']
                        total_cost_amount += order_bean['num'] * cost
                        total_sale_amount += order_bean['num'] * agent_price

                if group_name in data_stats_dict:
                    data_stats_dict[group_name]['total_sale_num'] += total_sale_num
                    data_stats_dict[group_name]['total_cost_amount'] += total_cost_amount
                    data_stats_dict[group_name]['total_sale_amount'] += total_sale_amount

        dinghuo_qs = OrderDetail.objects.exclude(orderlist__status=u'作废').filter(created__gte=start_dt,
                                                                                 created__lte=end_dt)
        for product_of_ding in dinghuo_qs:
            pro_bean = Product.objects.filter(id=product_of_ding.product_id)

            if pro_bean.count() > 0 and pro_bean[0].sale_group != u"None" and (
                        pro_bean[0].sale_group.name in data_stats_dict):
                data_stats_dict[pro_bean[0].sale_group.name][
                    'total_order_goods_quantity'] += product_of_ding.buy_quantity
                data_stats_dict[pro_bean[0].sale_group.name]['total_order_goods_amount'] += product_of_ding.total_price

        for group_name, data_of_group in data_stats_dict.items():
            temp_data_stats = SupplyChainDataStats.objects.filter(stats_time=target_day, group=group_name)
            if temp_data_stats.count() > 0:
                data_stats_bean = temp_data_stats[0]
                data_stats_bean.sale_quantity = data_of_group['total_sale_num']
                data_stats_bean.cost_amount = data_of_group['total_cost_amount']
                data_stats_bean.turnover = data_of_group['total_sale_amount']
                data_stats_bean.order_goods_quantity = data_of_group['total_order_goods_quantity']
                data_stats_bean.order_goods_amount = data_of_group['total_order_goods_amount']
                data_stats_bean.save()
            else:
                new_order = SupplyChainDataStats(stats_time=target_day, group=group_name)
                new_order.sale_quantity = data_of_group['total_sale_num']
                new_order.cost_amount = data_of_group['total_cost_amount']
                new_order.turnover = data_of_group['total_sale_amount']
                new_order.order_goods_quantity = data_of_group['total_order_goods_quantity']
                new_order.order_goods_amount = data_of_group['total_order_goods_amount']
                new_order.save()
    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_stats_daily_product(pre_day=1):
    try:
        function_of_task.get_daily_order_stats(pre_day)
        function_of_task.get_daily_ding_huo_stats(pre_day)
        function_of_task.get_daily_goods_arrival_stats(pre_day)
        function_of_task.get_daily_out_order_stats(pre_day)
    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_stats_product():
    try:
        function_of_task.daily_data_stats()

    except Exception, exc:
        raise task_stats_daily_order_by_group.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_send_daily_message():
    try:
        corp_id = "wx1657da9bb74c42d3"
        corp_secret = "UuTTtiSINnX5X2fVEbGNXO82wHRa8mae5nhAJ1K4foLMwtGUXSRYRtgyDWPegJci"
        access_token = functions.get_token_in_time(corp_id, corp_secret)
        result_str = functions.get_result_daily()
        functions.send_txt_msg(access_token, result_str)
    except Exception, exc:
        raise task_send_daily_message.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_write_supply_name():
    try:
        all_data = OrderList.objects.exclude(status=u'作废').filter(supplier_shop="")
        for data in all_data:
            if len(data.supplier_name) > 0:
                data.supplier_shop = get_supply_name(data.supplier_name)
                data.save()
    except Exception, exc:
        raise task_write_supply_name.retry(exc=exc)


def get_supply_name(name):
    if len(name) > 0:
        url_str = str(name)
    else:
        return ""
    try:
        content = urllib2.urlopen(url_str).read()
        reg1 = r'<a href=".*">首页</a>'
        reg2 = r'<a data-spm="d21" href=".*" target="_blank">进入店铺</a>'
        reg3 = r'<a class="enter-shop" href=".*" data-spm="d4918105"><i></i><span>进店逛逛</span></a>'
        reg4 = r'<a href=".*" target="_blank" class="button">进入企业网站</a>'
        content = str(content.decode('gb2312', 'ignore'))
        re1 = re.compile(reg1)
        re2 = re.compile(reg2)
        re3 = re.compile(reg3)
        re4 = re.compile(reg4)
        result = re.findall(re1, content) or re.findall(re2, content) or re.findall(re3, content) or re.findall(re4,
                                                                                                                content)
        if result:
            return result[0].split("//")[1].split(".")[0]
        else:
            return ""
    except Exception, ex:
        return ""


from flashsale.dinghuo.models_stats import RecordGroupPoint
from flashsale.dinghuo.models_user import MyUser, MyGroup


@task(max_retry=3, default_retry_delay=5)
def task_daily_stat_group_point():
    try:
        today = datetime.date.today()
        """统计一段时间内的订货单号得分情况"""
        all_ding_huo = OrderList.objects.exclude(status=u'作废').exclude(status=u'7')
        for item in all_ding_huo:
            content = "D" + str(item.id)
            record_point = RecordGroupPoint.objects.get_or_create(point_type=u'1', point_content=content)
            my_user = MyUser.objects.filter(user__username=item.buyer_name)
            if my_user.count() > 0:
                record_point[0].group_id = my_user[0].group.id
                record_point[0].group_name = my_user[0].group.name
                if item.reach_standard:
                    record_point[0].get_point = 1
                else:
                    record_point[0].get_point = 0
                record_point[0].record_time = item.created
                record_point[0].save()
        target_week_from = today - datetime.timedelta(days=today.weekday())
        prev_week_from = today - datetime.timedelta(days=today.weekday() + 7)
        prev_week_to = today - datetime.timedelta(days=today.weekday() + 1)
        user_a = MyUser.objects.values("user__username").filter(group=1)
        user_b = MyUser.objects.values("user__username").filter(group=2)
        user_c = MyUser.objects.values("user__username").filter(group=3)
        user_a = [val["user__username"] for val in user_a]
        user_b = [val["user__username"] for val in user_b]
        user_c = [val["user__username"] for val in user_c]
        save_point_by_time(target_week_from, today, user_a, user_b, user_c)
        save_point_by_time(prev_week_from, prev_week_to, user_a, user_b, user_c)
    except Exception, exc:
        raise task_daily_stat_group_point.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_daily_stat_ding_huo():
    try:
        all_ding_huo = OrderList.objects.exclude(status=u'作废').exclude(status=u'7')
        for item in all_ding_huo:
            reach_st = get_reach_standard_by_item(item)
            item.reach_standard = reach_st
            item.save()
    except Exception, exc:
        raise task_daily_stat_group_point.retry(exc=exc)


def get_reach_standard_by_item(ding_huo):
    all_detail = ding_huo.order_list.all()
    arrival_time = False
    for item in all_detail:
        if item.buy_quantity > item.arrival_quantity:
            return False
        else:
            arrival_time = item.arrival_time
    if arrival_time:
        arrival_date = datetime.date(arrival_time.year, arrival_time.month, arrival_time.day)
        ding_between = (arrival_date - ding_huo.created).days
        if ding_huo.p_district == '1' and ding_between <= 2:
            return True
        elif ding_huo.p_district == '2' and ding_between <= 3:
            return True
        elif ding_huo.p_district == '3' and ding_between <= 4:
            return True
        else:
            return False
    else:
        return False


def get_sale_amount_by_product(product):
    shelve_from = product.sale_time
    time_to = shelve_from + datetime.timedelta(days=14)
    pro_outer_id = product.outer_id
    cost = product.cost or 0
    agent_price = product.agent_price or 0
    order_sql = "select id,outer_id,sum(num) as sale_num from " \
                "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                "and sys_status not in('INVALID','ON_THE_FLY') " \
                "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                "and gift_type !=4 " \
                "and (pay_time between '{0}' and '{1}') " \
                "and char_length(outer_id)>=9 " \
                "and outer_id={2} " \
                "group by outer_id".format(shelve_from, time_to, pro_outer_id)
    try:
        cursor = connection.cursor()
        cursor.execute(order_sql)
        raw = cursor.fetchall()
    finally:
        cursor.close()
    print raw
    if len(raw) > 0:
        sale_num = raw[0][2]
        sale_amount = sale_num * agent_price
        gain_amount = sale_num * (agent_price - cost)
        if sale_amount > 5000:
            point = 3
        elif sale_amount > 2000:
            point = 1
        else:
            point = 0
        data_dict = {"pro_id": pro_outer_id, "sale_num": sale_num, "point": point, "sale_amount": sale_amount,
                     "gain_amount": gain_amount}
    else:
        data_dict = {"pro_id": pro_outer_id, "sale_num": 0, "point": 0, "sale_amount": 0, "gain_amount": 0}
    return data_dict


def save_point_by_time(time_from, time_to, user_a, user_b, user_c):
    all_product_a = Product.objects.filter(sale_time__range=(time_from, time_to)).filter(
        sale_charger__in=user_a).filter(status='normal')
    all_product_b = Product.objects.filter(sale_time__range=(time_from, time_to)).filter(
        sale_charger__in=user_b).filter(status='normal')
    all_product_c = Product.objects.filter(sale_time__range=(time_from, time_to)).filter(
        sale_charger__in=user_c).filter(status='normal')
    total_sale = {"A-sale": 0, "B-sale": 0, "C-sale": 0, "A-gain": 0, "B-gain": 0, "C-gain": 0}
    for product in all_product_a:
        product_dict = get_sale_amount_by_product(product)
        total_sale["A-sale"] += product_dict["sale_amount"]
        total_sale["A-gain"] += product_dict["gain_amount"]
        point = product_dict["point"]
        content = product_dict["pro_id"] + "-" + product.sale_time.strftime("%Y%m%d")
        record_point = RecordGroupPoint.objects.get_or_create(point_type=u'2', point_content=content)
        my_user = MyUser.objects.filter(user__username=product.sale_charger)
        if my_user.count() > 0:
            record_point[0].group_id = my_user[0].group.id
            record_point[0].group_name = my_user[0].group.name
            record_point[0].get_point = point
            record_point[0].record_time = product.sale_time
            record_point[0].save()
    for product in all_product_b:
        product_dict = get_sale_amount_by_product(product)
        total_sale["B-sale"] += product_dict["sale_amount"]
        total_sale["B-gain"] += product_dict["gain_amount"]
        point = product_dict["point"]
        content = product_dict["pro_id"] + "-" + product.sale_time.strftime("%Y%m%d")
        record_point = RecordGroupPoint.objects.get_or_create(point_type=u'2', point_content=content)
        my_user = MyUser.objects.filter(user__username=product.sale_charger)
        if my_user.count() > 0:
            record_point[0].group_id = my_user[0].group.id
            record_point[0].group_name = my_user[0].group.name
            record_point[0].get_point = point
            record_point[0].record_time = product.sale_time
            record_point[0].save()
    for product in all_product_c:
        product_dict = get_sale_amount_by_product(product)
        total_sale["C-sale"] += product_dict["sale_amount"]
        total_sale["C-gain"] += product_dict["gain_amount"]
        point = product_dict["point"]
        content = product_dict["pro_id"] + "-" + product.sale_time.strftime("%Y%m%d")
        record_point = RecordGroupPoint.objects.get_or_create(point_type=u'2', point_content=content)
        my_user = MyUser.objects.filter(user__username=product.sale_charger)
        if my_user.count() > 0:
            record_point[0].group_id = my_user[0].group.id
            record_point[0].group_name = my_user[0].group.name
            record_point[0].get_point = point
            record_point[0].record_time = product.sale_time
            record_point[0].save()
    if total_sale["A-sale"] > total_sale["B-sale"] and total_sale["A-sale"] > total_sale["C-sale"]:
        group_id = 1
        group_name = "采购A"
    elif total_sale["B-sale"] > total_sale["C-sale"]:
        group_id = 2
        group_name = "采购B"
    elif total_sale["C-sale"] > total_sale["B-sale"]:
        group_id = 3
        group_name = "采购C"
    else:
        return ""

    content = "X" + time_from.strftime("%Y") + time_from.strftime("%W")
    record_point = RecordGroupPoint.objects.get_or_create(point_type=u'2', point_content=content)
    record_point[0].group_id = group_id
    record_point[0].group_name = group_name
    record_point[0].get_point = 5
    record_point[0].record_time = time_to
    record_point[0].save()
    if total_sale["A-gain"] > total_sale["B-gain"] and total_sale["A-gain"] > total_sale["C-gain"]:
        group_id = 1
        group_name = "采购A"
    elif total_sale["B-gain"] > total_sale["C-gain"]:
        group_id = 2
        group_name = "采购B"
    elif total_sale["C-gain"] > total_sale["B-gain"]:
        group_id = 3
        group_name = "采购C"
    else:
        return ""
    content = "M" + time_from.strftime("%Y") + time_from.strftime("%W")
    record_point = RecordGroupPoint.objects.get_or_create(point_type=u'2', point_content=content)
    record_point[0].group_id = group_id
    record_point[0].group_name = group_name
    record_point[0].get_point = 5
    record_point[0].record_time = time_to
    record_point[0].save()