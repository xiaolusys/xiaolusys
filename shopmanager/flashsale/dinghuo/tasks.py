# -*- coding:utf-8 -*-
from __future__ import division

__author__ = 'yann'
import re
import sys
import urllib2
import datetime
from collections import defaultdict

from celery.task import task
from django.db import connection
from django.db.models import Max, Sum
from django.contrib.auth.models import User

import common.constants
from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import OrderDetail, OrderList,  SupplyChainDataStats, \
    PayToPackStats, PackageBackOrderStats, gen_purchase_order_group_key
from flashsale.pay.models import SaleOrder
from flashsale.dinghuo.models_purchase import PurchaseArrangement, PurchaseDetail, PurchaseOrder
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)
from supplychain.supplier.models import SaleProduct, SupplierCharge, SaleSupplier
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_COMPANY, WARE_CHOICES
from . import utils
from . import function_of_task, functions
from django.db import transaction
import logging
logger = logging.getLogger(__name__)


@task(max_retries=3, default_retry_delay=5)
def task_update_order_group_key(order_ids):
    """ order ids 更新 order group key """
    order_id_set = set()
    from flashsale.forecast import services
    services.recursive_aggragate_orders(order_ids, order_id_set)

    order_group_key = gen_purchase_order_group_key(order_id_set)
    OrderList.objects.filter(id__in=order_id_set).update(order_group_key=order_group_key)
    logger.info('task_update_order_group_key:order_ids=%s, group_key=%s' % (order_id_set, order_group_key))


@task(max_retries=3, default_retry_delay=5)
def task_stats_paytopack(pay_date, sku_num, total_days):
    try:
        entry, status = PayToPackStats.objects.get_or_create(pay_date=pay_date)
        entry.packed_sku_num += sku_num
        entry.total_days += total_days
        entry.save()
    except Exception, exc:
        raise task_stats_paytopack.retry(exc=exc)


@task(max_retries=3, default_retry_delay=5)
def task_stats_daily_product(pre_day=1):
    """计算原始数据表"""
    try:
        function_of_task.get_daily_order_stats(pre_day)
        function_of_task.get_daily_ding_huo_stats(pre_day)
        function_of_task.get_daily_goods_arrival_stats(pre_day)
        function_of_task.get_daily_out_order_stats(pre_day)
        # 计算仓库退货已经退款的对应数量
        function_of_task.get_daily_refund_num(pre_day)
    except Exception, exc:
        raise task_stats_daily_product.retry(exc=exc)


@task()
def task_stats_product():
    """计算汇总的表"""
    function_of_task.daily_data_stats_update()


@task(max_retries=3, default_retry_delay=5)
def task_stats_daily_order_by_group(pre_day=1):
    """每组统计，已经暂停使用"""
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


@task(max_retries=3, default_retry_delay=5)
def task_send_daily_message():
    """使用企业号发送每日订货短信，已经暂停使用"""
    try:
        corp_id = "wx1657da9bb74c42d3"
        corp_secret = "UuTTtiSINnX5X2fVEbGNXO82wHRa8mae5nhAJ1K4foLMwtGUXSRYRtgyDWPegJci"
        access_token = functions.get_token_in_time(corp_id, corp_secret)
        result_str = functions.get_result_daily()
        functions.send_txt_msg(access_token, result_str)
    except Exception, exc:
        raise task_send_daily_message.retry(exc=exc)


@task(max_retries=3, default_retry_delay=5)
def task_write_supply_name():
    """根据填写的商品链接抓取供应商，已经停止使用"""
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
            content2 = urllib2.urlopen(url_str).read()
            type = sys.getfilesystemencoding()  # 关键
            content2 = content2.decode("UTF-8").encode(type)  # 关键
            reg5 = r'class="main-news-dangkou-name">.*</a>'
            re5 = re.compile(reg5)
            result2 = re.findall(re5, content2)
            if result2:
                return result2[0].split('">')[1].split("</a>")[0]
            return ""
    except Exception, ex:
        return ""


from supplychain.basic.fetch_urls import getBeaSoupByCrawUrl


@task()
def task_write_supply_name2():
    try:
        all_data = OrderList.objects.exclude(status=u'作废').filter(supplier_shop="")
        for data in all_data:
            if len(data.supplier_name) > 0:
                supplier_name = get_supply_name2(data.supplier_name)
                if supplier_name != "":
                    data.supplier_shop = supplier_name
                    data.save()
    except Exception, exc:
        raise task_write_supply_name.retry(exc=exc)


def get_supply_name2(name):
    try:
        if len(name) > 0:
            url_str = str(name)
        else:
            return ""
        tsoup, response = getBeaSoupByCrawUrl(url_str)
        result = tsoup.findAll(attrs={'class': 'main-news-dangkou-name'})
        if result:
            return result[0].string
        else:
            return ""
    except:
        return ""


from flashsale.dinghuo.models import RecordGroupPoint
from flashsale.dinghuo.models_user import MyUser, MyGroup


@task(max_retries=3, default_retry_delay=5)
def task_daily_stat_group_point():
    """每组得分情况，已经作废"""
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
        prev_p_week_from = today - datetime.timedelta(days=today.weekday() + 14)
        prev_p_week_to = today - datetime.timedelta(days=today.weekday() + 8)

        prev_week_from = today - datetime.timedelta(days=today.weekday() + 7)
        prev_week_to = today - datetime.timedelta(days=today.weekday() + 1)

        user_a = MyUser.objects.values("user__username").filter(group=1)
        user_b = MyUser.objects.values("user__username").filter(group=2)
        user_c = MyUser.objects.values("user__username").filter(group=3)
        user_a = [val["user__username"] for val in user_a]
        user_b = [val["user__username"] for val in user_b]
        user_c = [val["user__username"] for val in user_c]
        save_point_by_time(prev_p_week_from, prev_p_week_to, user_a, user_b, user_c)
        save_point_by_time(target_week_from, today, user_a, user_b, user_c)
        save_point_by_time(prev_week_from, prev_week_to, user_a, user_b, user_c)
    except Exception, exc:
        raise task_daily_stat_group_point.retry(exc=exc)


@task(max_retries=3, default_retry_delay=5)
def task_daily_stat_ding_huo():
    """订货达标任务，已经作废"""
    try:
        today = datetime.date.today()
        time_from = today - datetime.timedelta(days=14)
        all_ding_huo = OrderList.objects.exclude(status=u'作废').exclude(status=u'7').filter(
            created__range=(time_from, today))
        for item in all_ding_huo:
            reach_st = get_reach_standard_by_item(item)
            if item.reach_standard != reach_st:
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


@task()
def task_supplier_stat(start_date, end_date, group_name):
    if group_name == 0:
        group_sql = ""
    else:
        group_sql = " where group_id = " + str(group_name)
    sql = 'select supply.supplier_shop,sum(supplydata.ding_huo_num) as ding_huo_num,' \
          'sum(supplydata.sale_num) as sale_num,sum(supplydata.sale_cost_of_product) as sale_amount,' \
          'sum(inferior_num) as inferior_num,sum(return_num) as return_num,supply.group_name,supply.supplier_name,count(supplydata.product_id) ' \
          'from (select * from supply_chain_stats_daily where sale_time >="{0}" and sale_time<="{1}") as supplydata left join ' \
          '(select detail.outer_id,list.supplier_shop,list.group_name,list.supplier_name from ' \
          '(select outer_id,orderlist_id from suplychain_flashsale_orderdetail ' \
          'where orderlist_id not in(select id from suplychain_flashsale_orderlist where status="作废")) as detail left join ' \
          '(select A.id,A.supplier_shop,my_group.name as group_name,A.supplier_name  from ' \
          '(select temp_list.id,temp_list.supplier_shop,temp_list.supplier_name,my_user.group_id from ' \
          '(select temp_list.id,temp_list.supplier_shop,admin_user.id as user_id,temp_list.supplier_name  from suplychain_flashsale_orderlist as temp_list ' \
          'left join auth_user as admin_user on temp_list.buyer_name=admin_user.username) as temp_list ' \
          'left join suplychain_flashsale_myuser as my_user on temp_list.user_id=my_user.user_id  {2}) as A ' \
          'left join suplychain_flashsale_mygroup as my_group on A.group_id=my_group.id) as list ' \
          'on detail.orderlist_id=list.id where list.supplier_shop!="" group by outer_id) as supply ' \
          'on supplydata.product_id=supply.outer_id where supply.supplier_shop!="" group by supply.supplier_shop'.format(
        start_date, end_date, group_sql)
    print sql
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return raw


@task()
def task_ding_huo(shelve_from, time_to, groupname, search_text, target_date, dinghuo_begin, query_time, dhstatus):
    """非没有退款状态的，不算作销售数"""
    order_sql = "select id,outer_id,sum(num) as sale_num,outer_sku_id,pay_time from " \
                "shop_trades_mergeorder where refund_status='NO_REFUND' and sys_status='IN_EFFECT' " \
                "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                "and sys_status not in('INVALID','ON_THE_FLY') " \
                "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                "and gift_type !=4 " \
                "and (pay_time between '{0}' and '{1}') " \
                "and char_length(outer_id)>=9 " \
                "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                "group by outer_id,outer_sku_id".format(shelve_from, time_to)
    if groupname == 0:
        group_sql = ""
    else:
        group_sql = "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser where group_id = {0}))".format(
            str(groupname))
    if len(search_text) > 0:
        search_text = str(search_text)
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num," \
                      "E.id as supplier_id,E.supplier_name, E.contact as supplier_contact, F.username from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where outer_id like '%%{0}%%' or name like '%%{0}%%' ) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku " \
                      "left join supplychain_supply_product as D on A.sale_product=D.id " \
                      "left join supplychain_supply_supplier as E on D.sale_supplier_id=E.id " \
                      "left join auth_user as F on F.id=D.contactor_id".format(search_text)
    else:
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num," \
                      "E.id as supplier_id,E.supplier_name, E.contact as supplier_contact, F.username from " \
                      "(select id,name as product_name,outer_id,pic_path,sale_product from " \
                      "shop_items_product where  sale_time='{0}' " \
                      "and status!='delete' {1}) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku " \
                      "left join supplychain_supply_product as D on A.sale_product=D.id " \
                      "left join supplychain_supply_supplier as E on D.sale_supplier_id=E.id " \
                      "left join auth_user as F on F.id=D.contactor_id".format(target_date, group_sql)

    ding_huo_sql = "select B.outer_id,B.chichu_id,sum(if(A.status='草稿' or A.status='审核',B.buy_quantity,0)) as buy_quantity,sum(if(A.status='7',B.buy_quantity,0)) as sample_quantity," \
                   "sum(if(status='5' or status='6' or status='有问题' or status='验货完成' or status='已处理',B.arrival_quantity,0)) as arrival_quantity,B.effect_quantity,A.status" \
                   " from (select id,status from suplychain_flashsale_orderlist where status not in ('作废') and created between '{0}' and '{1}') as A " \
                   "left join (select orderlist_id,outer_id,chichu_id,buy_quantity,arrival_quantity,(buy_quantity-non_arrival_quantity) as effect_quantity " \
                   "from suplychain_flashsale_orderdetail) as B on A.id=B.orderlist_id group by outer_id,chichu_id".format(
        dinghuo_begin, query_time)
    sql = "select product.outer_id,product.product_name,product.outer_sku_id,product.pic_path,product.properties_alias," \
          "order_info.sale_num,ding_huo_info.buy_quantity,ding_huo_info.effect_quantity,product.sku_id,product.exist_stock_num," \
          "product.id,ding_huo_info.arrival_quantity,ding_huo_info.sample_quantity,product.supplier_id,product.supplier_name,product.supplier_contact,product.username " \
          "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id and product.outer_sku_id=order_info.outer_sku_id left join (" + ding_huo_sql + ") as ding_huo_info on product.outer_id=ding_huo_info.outer_id and product.sku_id=ding_huo_info.chichu_id"
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    trade_dict = {}
    total_more_num = 0
    total_less_num = 0
    for product in raw:
        sale_num = int(product[5] or 0)
        ding_huo_num = int(product[6] or 0)
        arrival_num = int(product[11] or 0)
        sample_num = int(product[12] or 0)
        ding_huo_status, flag_of_more, flag_of_less = functions.get_ding_huo_status(
            sale_num, ding_huo_num, int(product[9] or 0), sample_num, arrival_num)
        if flag_of_more:
            total_more_num += (sample_num + int(product[9] or 0) + ding_huo_num + arrival_num - sale_num)
        if flag_of_less:
            total_less_num += (sale_num - sample_num - int(product[9] or 0) - arrival_num - ding_huo_num)
        temp_dict = {"product_id": product[10], "sku_id": product[2], "product_name": product[1],
                     "pic_path": product[3], "sale_num": sale_num or 0, "sku_name": product[4],
                     "ding_huo_num": ding_huo_num, "effect_num": product[7] or 0,
                     "ding_huo_status": ding_huo_status, "sample_num": sample_num,
                     "flag_of_more": flag_of_more, "flag_of_less": flag_of_less,
                     "sku_id": product[8], "ku_cun_num": int(product[9] or 0),
                     "arrival_num": arrival_num, 'supplier_id': int(product[13] or 0),
                     'supplier_name': product[14] or '',
                     'supplier_contact': product[15] or '', 'username': product[16] or ''}
        if dhstatus == u'0' or ((flag_of_more or flag_of_less) and dhstatus == u'1') or (
                    flag_of_less and dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
            if product[0] not in trade_dict:
                trade_dict[product[0]] = [temp_dict]
            else:
                trade_dict[product[0]].append(temp_dict)
    supplier_dict = {}
    trade_dict = sorted(trade_dict.items(), key=lambda d: d[0])
    for item in trade_dict:
        supplier_id = item[1][0]['supplier_id']
        items = supplier_dict.setdefault(supplier_id, [])
        items.append(item)
    supplier_dict = sorted(supplier_dict.items(), key=lambda x: x[0], reverse=True)
    result_dict = {"total_more_num": total_more_num, "total_less_num": total_less_num, "supplier_dict": supplier_dict}
    return result_dict


import function_of_task_optimize


@task()
def task_ding_huo_optimize(shelve_from, time_to, groupname, search_text, target_date, dinghuo_begin, query_time,
                           dhstatus):
    """非没有退款状态的，不算作销售数,没有之前的速度快"""
    if len(search_text) > 0:
        search_text = str(search_text)
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where outer_id like '%%{0}%%' or name like '%%{0}%%' ) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            search_text)
    else:
        product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                      "(select id,name as product_name,outer_id,pic_path from " \
                      "shop_items_product where  sale_time='{0}' " \
                      "and status!='delete') as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            target_date)

    cursor = connection.cursor()
    cursor.execute(product_sql)
    product_raw = cursor.fetchall()
    trade_dict = {}
    for one_product in product_raw:
        temp_dict = {"product_id": one_product[0], "outer_sku_id": one_product[4], "product_name": one_product[1],
                     "pic_path": one_product[3], "sale_num": 0, "sku_name": one_product[6],
                     "ding_huo_num": 0, "effect_num": 0, "sku_id": one_product[7],
                     "ding_huo_status": "", "sample_num": 0,
                     "flag_of_more": "", "flag_of_less": "", "ku_cun_num": int(one_product[8] or 0),
                     "arrival_num": 0}
        if one_product[2] not in trade_dict:
            trade_dict[one_product[2]] = [temp_dict]
        else:
            trade_dict[one_product[2]].append(temp_dict)
    total_more_num = 0
    total_less_num = 0

    for product_outer_id, sku_list in trade_dict.items():

        for one_sku in sku_list:
            sale_num = function_of_task_optimize.get_sale_num(shelve_from, time_to, product_outer_id,
                                                              one_sku["outer_sku_id"])
            ding_huo_num, sample_num, arrival_num = function_of_task_optimize.get_dinghuo_num(dinghuo_begin, query_time,
                                                                                              product_outer_id,
                                                                                              one_sku["sku_id"])
            one_sku["sale_num"] = sale_num
            one_sku["ding_huo_num"] = ding_huo_num
            one_sku["sample_num"] = sample_num
            one_sku["arrival_num"] = arrival_num
            ding_huo_status, flag_of_more, flag_of_less = functions.get_ding_huo_status(
                sale_num, ding_huo_num, one_sku["ku_cun_num"], sample_num, arrival_num)
            one_sku["ding_huo_status"] = ding_huo_status
            one_sku["flag_of_less"] = flag_of_less
            one_sku["flag_of_more"] = flag_of_more
            if flag_of_more:
                total_more_num += (sample_num + one_sku["ku_cun_num"] + ding_huo_num + arrival_num - sale_num)
            if flag_of_less:
                total_less_num += (sale_num - sample_num - one_sku["ku_cun_num"] - arrival_num - ding_huo_num)
    trade_dict = sorted(trade_dict.items(), key=lambda d: d[0])
    result_dict = {"total_more_num": total_more_num, "total_less_num": total_less_num, "trade_dict": trade_dict}
    return result_dict


from supplychain.supplier.models import SaleProduct
from flashsale.pay.models import SaleRefund
from shopback.refunds.models import RefundProduct
from .models import ReturnGoods, RGDetail


def get_sale_product(sale_product):
    """　找到库存商品对应的选品信息　"""
    try:
        sal_p = SaleProduct.objects.get(id=sale_product)
        return sal_p.sale_supplier.supplier_name, sal_p.sale_supplier.pk, \
               sal_p.sale_supplier.contact, sal_p.sale_supplier.mobile
    except SaleProduct.DoesNotExist:
        return "", 0, "", ""


def time_zone_handler(date_from=None, date_to=None):
    if date_to is None or date_to == "":
        date_to = datetime.datetime.today()
    if date_from is None or date_from == "":
        date_from = datetime.datetime.today() - datetime.timedelta(days=7)
    if type(date_to) is str and type(date_from) is str:
        tyear, tmonth, tday = map(int, date_to.split('-'))
        fyear, fmonth, fday = map(int, date_from.split('-'))

        date_from = datetime.datetime(tyear, tmonth, tday, 0, 0, 0)
        date_to = datetime.datetime(fyear, fmonth, fday, 23, 59, 59)
    return date_from, date_to


def get_other_field(product_id, sku_id):
    try:
        pro = Product.objects.get(id=product_id)
        name = pro.name
        psk = ProductSku.objects.get(id=sku_id)
        cost = psk.cost
        quantity = psk.quantity
        wait_post_num = psk.wait_post_num
        inferior_num = psk.sku_inferior_num
        return name, cost, quantity, wait_post_num, inferior_num, pro.sale_product
    except:
        return u"异常商品", 0, 0, 0, 0, 0


def get_args_by_re_product(outer_id, outer_sku_id):
    try:
        pro = Product.objects.get(outer_id=outer_id)
        name = pro.name
        psk = ProductSku.objects.get(product_id=pro.id, outer_id=outer_sku_id)
        cost = psk.cost
        quantity = psk.quantity
        wait_post_num = psk.wait_post_num
        inferior_num = psk.sku_inferior_num
        return name, cost, quantity, wait_post_num, inferior_num, pro.id, psk.id, pro.sale_product
    except:
        return u"异常商品", 0, 0, 0, 0, 0, 0, 0


def get_sale_product_supplier(sale_product):
    """　找到库存商品对应的选品信息　"""
    try:
        sal_p = SaleProduct.objects.get(id=sale_product)
        return sal_p.sale_supplier.pk
    except SaleProduct.DoesNotExist:
        return 0


@task()
def calcu_refund_info_by_pro_v2(date_from=None, date_to=None):
    # SKUID   sku_id
    # 产品ID   pro_id
    # 名称　   name
    # 成本    cost
    # 库存    quantity
    # 待发数   wait_post_num
    # 次品数   inferior_num

    # 退款数
    # 申请退货数
    # 退货到仓数
    # 供应商
    date_from, date_to = time_zone_handler(date_from, date_to)
    sale_refunds = SaleRefund.objects.filter(created__gte=date_from, created__lte=date_to)
    backed_refunds = RefundProduct.objects.filter(created__gte=date_from, created__lte=date_to)
    info = {}

    for sal_re in sale_refunds:
        name, cost, quantity, wait_post_num, inferior_num, sale_product = get_other_field(sal_re.item_id, sal_re.sku_id)
        sale_supplier_pk = get_sale_product_supplier(sale_product)
        if sale_supplier_pk == 0:  # 没有供应商的不纳入退货范畴
            continue
        if wait_post_num > 0:  # 有待发的不纳入退货范畴
            continue
        if quantity <= 0:  # 库存数为０　不纳入退货范畴
            continue
        # 申请退货的数量（　包含：买家已经收到货　买家已经退货　两个状态　）
        return_pro_num = sal_re.refund_num if sal_re.good_status in (
            SaleRefund.BUYER_NOT_RECEIVED, SaleRefund.BUYER_RECEIVED) and sal_re.status in (
            SaleRefund.REFUND_WAIT_SELLER_AGREE, SaleRefund.REFUND_CONFIRM_GOODS) else 0
        # 这里要屏蔽退款成功的（货已经到仓库了的）
        # 退货到仓库的数量　在sale 中统计不到　置0
        backed_num = 0

        if info.has_key(sal_re.sku_id):  # 如果字典中存在该sku的信息
            # 叠加数量
            info[sal_re.sku_id]['return_num'] += sal_re.refund_num
            info[sal_re.sku_id]['return_pro_num'] += return_pro_num
        else:  # 没有就加入
            info[sal_re.sku_id] = {"pro_id": sal_re.item_id,
                                   "name": name, "cost": cost, "quantity": quantity,
                                   "wait_post_num": wait_post_num, "inferior_num": inferior_num,
                                   "return_num": sal_re.refund_num, "return_pro_num": return_pro_num,
                                   "backed_num": backed_num, "sale_supplier_pk": sale_supplier_pk
                                   }

    for re_pro in backed_refunds:
        name, cost, quantity, wait_post_num, inferior_num, pro_id, sku_id, sale_product = get_args_by_re_product(
            re_pro.outer_id,
            re_pro.outer_sku_id)
        sale_supplier_pk = get_sale_product_supplier(sale_product)
        if sale_supplier_pk == 0:  # 没有供应商的不纳入退货范畴
            continue
        if wait_post_num > 0:  # 有待发的不纳入退货范畴
            continue
        if quantity <= 0:  # 库存数为０　不纳入退货范畴
            continue
        if info.has_key(sku_id):  # 如果字典中存在该sku的信息
            info[sku_id]['backed_num'] += re_pro.num
        else:  # 没有就加入
            # 退款数量
            return_num = re_pro.num
            # 申请退货的数量
            return_pro_num = re_pro.num
            # 退货到仓库的数量　在sale 中统计不到　置0
            backed_num = re_pro.num
            info[sku_id] = {"pro_id": pro_id,
                            "name": name, "cost": cost, "quantity": quantity,
                            "wait_post_num": wait_post_num, "inferior_num": inferior_num,
                            "return_num": return_num, "return_pro_num": return_pro_num,
                            "backed_num": backed_num, "sale_supplier_pk": sale_supplier_pk
                            }

    data = [info]
    return data


from flashsale.dinghuo.models import DailyStatsPreview, DailySupplyChainStatsOrder


@task()
def task_daily_preview(default_time=15):
    function_of_settime(default_time)


def function_of_settime(default_time):
    today = datetime.date.today()
    for i in range(1, default_time):
        target_order = DailySupplyChainStatsOrder.objects.filter(sale_time=today - datetime.timedelta(days=i))
        total_time = 0
        total_num = 0
        total_return = 0
        total_cost = 0
        total_money = 0
        total_return_money = 0
        shelf_num = target_order.count()
        for one_data in target_order:
            try:
                one_product = Product.objects.get(outer_id=one_data.product_id)
            except:
                continue
            during_time = one_data.goods_out_time * one_data.sale_num - one_data.trade_general_time * one_data.sale_num
            if during_time > 0:
                total_return += one_data.return_num  # 退款数
                total_cost += one_data.cost_of_product  # 成本
                total_num += one_data.sale_num  # 销售数
                total_money += one_data.sale_cost_of_product  # 成本
                total_return_money += (one_product.agent_price * one_data.return_num)  # 退款额
                total_time += during_time  # 发货速度
        if total_num != 0:
            fahuo = total_time / total_num
            one_preview, state = DailyStatsPreview.objects.get_or_create(sale_time=today - datetime.timedelta(days=i))
            one_preview.sale_num = total_num
            one_preview.goods_out_time = fahuo
            one_preview.shelf_num = shelf_num
            one_preview.return_num = total_return
            one_preview.cost_of_product = total_num
            one_preview.sale_money = total_money
            one_preview.return_money = total_return_money
            one_preview.save()


# 2015-12-12
@task()
def task_supplier_avg_post_time(days=5):
    """ 统计供应商的平均发货时间
        计算方法：　供应商每次（到货时间　－　发货时间）之和　／　发货次数
        没有上架的商品没有订货　就不需要更新供应商的订货时间
    """
    from django.db.models import Avg
    from common.modelutils import update_model_fields
    time_to = datetime.datetime.today() - datetime.timedelta(days - 8)
    time_from = time_to - datetime.timedelta(days=days)
    pros = Product.objects.filter(sale_time__gte=time_from, sale_time__lte=time_to, status='normal')
    pro_sales = pros.values('sale_product').distinct()
    salpros = SaleProduct.objects.filter(id__in=pro_sales)
    suppliers = []  # 已经计算过的供应商
    for sal in salpros:
        supplier = sal.sale_supplier
        if supplier.id not in suppliers:  # 没有计算处理过则处理
            suppliers.append(supplier.id)
        else:  # 已经处理过则跳过
            continue
        one_supplier_sale = SaleProduct.objects.filter(sale_supplier_id=supplier.id)  # 该供应商的所有选品
        sale_ids = one_supplier_sale.values('id')
        sig_sup_allpros = Product.objects.filter(sale_product__in=sale_ids)  # 该供应商选品对应的所有产品
        sig_sup_outers = sig_sup_allpros.values('outer_id')
        sorders = DailySupplyChainStatsOrder.objects.filter(product_id__in=sig_sup_outers).exclude(
            trade_general_time=0). \
            exclude(goods_arrival_time=0)  # 获取统计供应链统计数据(排除订货时间为０或者到货时间为０的记录)
        # 计算平均发货天数
        avg_order_time = sorders.aggregate(order_time=Avg('trade_general_time')).get('order_time') or 0  # 平均下单时间
        avg_arrive_time = sorders.aggregate(arri_time=Avg('goods_arrival_time')).get('arri_time') or 0  # 平均到货时间
        avg_orde = datetime.datetime.utcfromtimestamp(avg_order_time)
        avr_arri = datetime.datetime.utcfromtimestamp(avg_arrive_time)
        minus = avr_arri - avg_orde  # 时间差值
        avg_day = round(minus.seconds / 3600.0 / 24, 4)  # 天数
        supplier.avg_post_days = avg_day
        update_model_fields(supplier, update_fields=['avg_post_days'])


from django.db.models import F
from common.modelutils import update_model_fields


@task()
def task_category_stock_data(days=15):
    """
        统计产品分类中的进货数据
        这里由于订货的状态不是很稳定，　即　在验货完成之后还会有修改的　还有作废的（供应商缺货） 误操作　仓库入仓出错等情况
        采用任务处理　将　15天以内的订货单来核算按照产品类别来计算产品的数量　
        新建某产品的订货单后还有可能会再次新建该产品的订货单　所以这里要累加（并且不能有重复数据）
        所以仅仅处理一天的数据在任务中每天执行一次
    """
    from shopback.categorys.models import CategorySaleStat
    # stock_num 进货数量
    # stock_amount 进货金额
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=days)
    # 验货完成状态和已经处理状态的订货单(15天前的)
    dinghuos = OrderList.objects.filter(created=target_day, status__in=(OrderList.COMPLETED, OrderList.COMPLETED))
    for dinhuo in dinghuos:
        dinhuo_details = dinhuo.order_list.all()  # 订货明细内容
        for detail in dinhuo_details:
            pro = Product.objects.get(id=detail.product_id)
            cgysta, state = CategorySaleStat.objects.get_or_create(stat_date=pro.sale_time, category=pro.category.cid)
            if state:  # 如果是新建
                cgysta.stock_amount = detail.total_price  # 订货明细金额
                cgysta.stock_num = detail.buy_quantity  # 订货明细数量
            else:  # 在原有基础上面加订货明细金额　订货明细数量
                cgysta.stock_amount = F("stock_amount") + detail.total_price
                cgysta.stock_num = F("stock_num") + detail.buy_quantity
            update_model_fields(cgysta, update_fields=["stock_amount", "stock_num"])


from .models import SaleInventoryStat


@task()
def task_stat_category_inventory_data(date=None):
    """
        统计当天的订货表的新增采购数　未到货总数　到货数 童女装分类
    """
    from django.db.models import Q, Sum
    from shopback.trades.models import MergeOrder
    target_date = datetime.date.today() - datetime.timedelta(days=1) if date is None else date
    target_from = datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    target_to = target_from + datetime.timedelta(days=1)

    all_orders = OrderDetail.objects.all().exclude(orderlist__status=OrderList.ZUOFEI)

    # 目标日期订货的订货单　订货单明细内容　排除作废的
    odts_female = all_orders.filter(outer_id__startswith='8', orderlist__created=target_date)  # 女装
    odts_child = all_orders.filter(Q(outer_id__startswith='9') | Q(outer_id__startswith='1')).filter(
        orderlist__created=target_date)  # 童装

    c_newly_increased = odts_child.aggregate(t_buy_quantity=Sum('buy_quantity')).get("t_buy_quantity") or 0

    # 产品的到货数量和未到货数量会有延迟　
    the_date = target_date - datetime.timedelta(days=15)
    odts_child_the_date = all_orders.filter(Q(outer_id__startswith='9') | Q(outer_id__startswith='1')).filter(
        orderlist__created=the_date)  # 童装
    c_arrived = odts_child_the_date.aggregate(t_arrival_quantity=Sum('arrival_quantity')).get("t_arrival_quantity") or 0
    c_not_arrive = odts_child_the_date.aggregate(t_non_arrival_quantity=Sum('non_arrival_quantity')).get(
        "t_non_arrival_quantity") or 0

    f_newly_increased = odts_female.aggregate(t_buy_quantity=Sum('buy_quantity')).get("t_buy_quantity") or 0

    # 产品的到货数量和未到货数量会有延迟　
    odts_female_the_date = all_orders.filter(outer_id__startswith='8', orderlist__created=the_date)  # 女装
    f_arrived = odts_female_the_date.aggregate(t_arrival_quantity=Sum('arrival_quantity')).get(
        "t_arrival_quantity") or 0
    f_not_arrive = odts_female_the_date.aggregate(t_non_arrival_quantity=Sum('non_arrival_quantity')).get(
        "t_non_arrival_quantity") or 0

    # 总库存统计 排除优尼世界的产品
    childps = Product.objects.filter(status=Product.NORMAL, collect_num__gt=0).filter(
        Q(outer_id__startswith='9') | Q(outer_id__startswith='1')).exclude(category__cid=1)
    femaleps = Product.objects.filter(status=Product.NORMAL, outer_id__startswith='8',
                                      collect_num__gt=0).exclude(category__cid=1)
    inventory_c_num = childps.aggregate(t_collect_num=Sum('collect_num')).get("t_collect_num") or 0
    inventory_f_num = femaleps.aggregate(t_collect_num=Sum('collect_num')).get("t_collect_num") or 0

    # 昨天称重的订单　发出的数量
    mos_f = MergeOrder.objects.filter(merge_trade__weight_time__range=(target_from, target_to),
                                      outer_id__startswith='8')
    mos_c = MergeOrder.objects.filter(merge_trade__weight_time__range=(target_from, target_to)).filter(
        Q(outer_id__startswith='9') | Q(outer_id__startswith='1'))
    mos_f_snum = mos_f.aggregate(t_fnum=Sum('num')).get("t_fnum") or 0
    mos_c_snum = mos_c.aggregate(t_cnum=Sum('num')).get("t_cnum") or 0

    # 分别保存　童装和女装的各个数量
    inventory_c, state_c = SaleInventoryStat.objects.get_or_create(stat_date=target_date,
                                                                   category=SaleInventoryStat.CHILD)
    inventory_c.newly_increased = c_newly_increased

    inventory_c.inventory = inventory_c_num
    inventory_c.deliver = mos_c_snum
    inventory_c.save()
    inventory_f, state_f = SaleInventoryStat.objects.get_or_create(stat_date=target_date,
                                                                   category=SaleInventoryStat.FEMALE)
    inventory_f.newly_increased = f_newly_increased
    inventory_f.inventory = inventory_f_num
    inventory_f.deliver = mos_f_snum
    inventory_f.save()

    # 保存十五天前的稳定的到货数据和为到货数据
    fifth_inventory_c, state_c = SaleInventoryStat.objects.get_or_create(stat_date=the_date,  # 十五天前的记录
                                                                         category=SaleInventoryStat.CHILD)
    fifth_inventory_c.arrived = c_arrived
    fifth_inventory_c.not_arrive = c_not_arrive
    fifth_inventory_c.save()

    fifth_inventory_f, state_f = SaleInventoryStat.objects.get_or_create(stat_date=the_date,
                                                                         category=SaleInventoryStat.FEMALE)
    fifth_inventory_f.arrived = f_arrived
    fifth_inventory_f.not_arrive = f_not_arrive
    fifth_inventory_f.save()


def _get_suppliers():
    sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
        merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                               pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
        merge_trade__sys_status__in=
        [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
         pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
         pcfg.REGULAR_REMAIN_STATUS],
        sys_status=pcfg.IN_EFFECT).values('outer_id',
                                          'outer_sku_id').annotate(
        sale_num=Sum('num'),
        last_pay_time=Max('pay_time'))

    order_products = {}
    for s in sale_stats:
        skus = order_products.setdefault(s['outer_id'], {})
        skus[s['outer_sku_id']] = {
            'sale_quantity': s['sale_num'],
            'last_pay_time': s['last_pay_time']
        }

    sku_ids = set()
    products = {}
    for sku in ProductSku.objects.select_related('product').filter(
            product__outer_id__in=order_products.keys()):
        order_skus = order_products[sku.product.outer_id]
        if sku.outer_id in order_skus:
            sku_ids.add(sku.id)
            skus = products.setdefault(sku.product.id, {})
            sku_dict = {
                'cost': sku.cost or 0,
                'sale_quantity': 0,
                'last_pay_time': common.constants.MIN_DATETIME,
                'buy_quantity': 0,
                'arrival_quantity': 0,
                'inferior_quantity': 0
            }
            sku_dict.update(order_skus.get(sku.outer_id) or {})
            skus[sku.id] = sku_dict

    dinghuo_stats = OrderDetail.objects \
        .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED]) \
        .values('product_id', 'chichu_id') \
        .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                  inferior_quantity=Sum('inferior_quantity'))

    for s in dinghuo_stats:
        product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
        sku_ids.add(sku_id)
        skus = products.setdefault(product_id, {})
        sku = skus.setdefault(sku_id, {'sale_quantity': 0,
                                       'last_pay_time': common.constants.MIN_DATETIME})
        sku.update({
            'buy_quantity': s['buy_quantity'],
            'arrival_quantity': s['arrival_quantity'],
            'inferior_quantity': s['inferior_quantity']
        })

    for sku in ProductSku.objects.filter(pk__in=list(sku_ids)):
        sku_dict = products[sku.product_id][sku.id]
        sku_dict.update({
            'id': sku.id,
            'quantity': max(sku.quantity, 0),
            'properties_name': sku.properties_name or sku.properties_alias,
            'outer_id': sku.outer_id,
            'cost': sku.cost or 0
        })

    saleproduct_ids = set()
    product_mapping = {}
    for product in Product.objects.filter(pk__in=products.keys()):
        saleproduct_ids.add(product.sale_product)
        product_mapping[product.id] = {
            'id': product.id,
            'name': product.name,
            'pic_path': '%s?imageView2/0/w/120' % product.pic_path.strip(),
            'outer_id': product.outer_id,
            'sale_product_id': product.sale_product
        }

    supplier_mapping = {}
    saleproduct2supplier_mapping = {}
    for saleproduct in SaleProduct.objects.select_related(
            'sale_supplier').filter(pk__in=list(saleproduct_ids)):
        saleproduct2supplier_mapping[
            saleproduct.id] = saleproduct.sale_supplier.id
        if saleproduct.sale_supplier.id not in supplier_mapping:
            supplier_mapping[saleproduct.sale_supplier.id] = {
                'id': saleproduct.sale_supplier.id,
                'supplier_name': saleproduct.sale_supplier.supplier_name,
                'ware_by': saleproduct.sale_supplier.ware_by or 0,
                'buyer_id': 0,
                'products': []
            }

    for supplier_charge in SupplierCharge.objects.filter(
            pk__in=supplier_mapping.keys(),
            status=SupplierCharge.EFFECT).order_by('-created'):
        supplier_id = supplier_charge.supplier_id
        buyer_id = supplier_mapping[supplier_id]['buyer_id']
        if not buyer_id:
            supplier_mapping[supplier_id][
                'buyer_id'] = supplier_charge.employee_id

    suppliers = {}
    for product_id in sorted(products.keys(), reverse=True):
        if product_id not in product_mapping:
            continue
        skus = products[product_id]
        new_product = product_mapping[product_id]
        new_skus = []
        for sku in [skus[k] for k in sorted(skus.keys())]:
            effect_quantity = sku['quantity'] + sku[
                'buy_quantity'] - min(sku['arrival_quantity'], sku['buy_quantity']) - sku[
                                  'sale_quantity']
            if effect_quantity >= 0:
                continue
            sku['effect_quantity'] = effect_quantity
            new_skus.append(sku)
        if not new_skus:
            continue
        new_product.update({
            'last_pay_time': max(filter(None, map(
                lambda x: x['last_pay_time'], new_skus)) or [common.constants.MIN_DATETIME]),
            'skus': new_skus
        })
        sale_product_id = new_product['sale_product_id']
        supplier_id = saleproduct2supplier_mapping.get(sale_product_id) or 0
        if supplier_id not in suppliers:
            supplier = supplier_mapping.get(supplier_id) or {
                'id': supplier_id,
                'supplier_name': '未知',
                'ware_by': WARE_SH,
                'buyer_id': 0,
                'products': []
            }
            suppliers[supplier_id] = supplier
        else:
            supplier = suppliers[supplier_id]
        supplier['products'].append(new_product)

    new_suppliers = []
    for k in sorted(suppliers.keys()):
        supplier = suppliers[k]
        if not supplier.get('products'):
            continue
        last_pay_time = max(map(lambda x: x['last_pay_time'], supplier[
            'products']))
        if last_pay_time == common.constants.MIN_DATETIME:
            last_pay_date = '暂无销售'
        else:
            last_pay_date = last_pay_time.strftime('%Y-%m-%d')
        supplier['last_pay_time'] = last_pay_time
        supplier['last_pay_date'] = last_pay_date
        new_suppliers.append(supplier)
    return new_suppliers


def get_suppliers(pay_time_threshold):
    sale_stats = SaleOrder.objects.filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                          refund_status__lte=SaleRefund.REFUND_REFUSE_BUYER,
                                          pay_time__gt=pay_time_threshold) \
        .exclude(outer_id__startswith='RMB') \
        .values('sku_id').annotate(sale_quantity=Sum('num'), last_pay_time=Max('pay_time'))

    sale_skus_dict = {}
    for sale_stat in sale_stats:
        sku_id = (sale_stat.get('sku_id') or '').strip()
        if not sku_id:
            continue
        sale_skus_dict[int(sku_id)] = {
            'sale_quantity': sale_stat['sale_quantity'],
            'last_pay_time': sale_stat.get('last_pay_time') or common.constants.MIN_DATETIME
        }

    dinghuo_skus_dict = {}
    dinghuo_stats = OrderDetail.objects.select_related('orderlist').filter(
        chichu_id__in=map(str, sale_skus_dict.keys())) \
        .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED, OrderList.TO_PAY]) \
        .values('chichu_id') \
        .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                  inferior_quantity=Sum('inferior_quantity'))
    for dinghuo_stat in dinghuo_stats:
        sku_id = (dinghuo_stat.get('chichu_id') or '').strip()
        dinghuo_skus_dict[int(sku_id)] = {
            'buy_quantity': dinghuo_stat['buy_quantity'],
            'arrival_quantity': dinghuo_stat['arrival_quantity'],
            'inferior_quantity': dinghuo_stat['inferior_quantity']
        }

    saleproduct_ids = set()
    products_dict = {}
    for sku in ProductSku.objects.select_related('product').filter(id__in=sale_skus_dict.keys()):
        product = sku.product
        saleproduct_ids.add(product.sale_product)
        product_dict = products_dict.setdefault(product.id, {
            'id': product.id,
            'name': product.name,
            'pic_path': '%s?imageView2/0/w/120' % product.pic_path.strip(),
            'outer_id': product.outer_id,
            'saleproduct_id': product.sale_product,
            'skus': {}
        })

        sku_dict = {
            'id': sku.id,
            'quantity': max(sku.quantity, 0),
            'properties_name': sku.properties_name or sku.properties_alias,
            'outer_id': sku.outer_id,
            'cost': sku.cost,
            'sale_quantity': 0,
            'buy_quantity': 0,
            'arrival_quantity': 0,
            'inferior_quantity': 0
        }
        sku_dict.update(sale_skus_dict.get(sku.id) or {})
        sku_dict.update(dinghuo_skus_dict.get(sku.id) or {})
        product_dict['skus'][sku.id] = sku_dict

    suppliers_dict = {}
    saleproduct2supplier_dict = {}
    for saleproduct in SaleProduct.objects.select_related('sale_supplier').filter(id__in=list(saleproduct_ids)):
        saleproduct2supplier_dict[saleproduct.id] = saleproduct.sale_supplier.id
        if saleproduct.sale_supplier.id not in suppliers_dict:
            suppliers_dict[saleproduct.sale_supplier.id] = {
                'id': saleproduct.sale_supplier.id,
                'name': saleproduct.sale_supplier.supplier_name,
                'ware_by': saleproduct.sale_supplier.ware_by or 0,
                'products': []
            }

    new_suppliers_dict = {}
    for product_id in sorted(products_dict.keys()):
        product_dict = products_dict[product_id]
        skus_dict = product_dict['skus']
        new_skus = []

        for sku_id in sorted(skus_dict.keys()):
            sku_dict = skus_dict[sku_id]
            effect_quantity = sku_dict['quantity'] + sku_dict['buy_quantity'] - \
                              min(sku_dict['arrival_quantity'], sku_dict['buy_quantity']) - \
                              sku_dict['sale_quantity']
            if effect_quantity >= 0:
                continue
            sku_dict['effect_quantity'] = effect_quantity
            new_skus.append(sku_dict)
        if not new_skus:
            continue
        product_dict['skus'] = new_skus
        product_dict['last_pay_time'] = max(x['last_pay_time'] for x in new_skus)

        saleproduct_id = product_dict['saleproduct_id']
        supplier_id = saleproduct2supplier_dict.get(saleproduct_id) or 0
        default_supplier_dict = {
            'id': supplier_id,
            'name': '未知',
            'ware_by': WARE_SH,
            'products': []
        }
        supplier_dict = new_suppliers_dict.setdefault(supplier_id,
                                                      suppliers_dict.get(supplier_id) or default_supplier_dict)

        supplier_dict['products'].append(product_dict)

    new_suppliers = []
    for supplier_id in sorted(new_suppliers_dict.keys()):
        supplier_dict = new_suppliers_dict[supplier_id]
        supplier_dict['last_pay_time'] = max(x['last_pay_time'] for x in supplier_dict['products'])
        new_suppliers.append(supplier_dict)
    return new_suppliers


def create_orderlist(supplier):
    return {}
    now = datetime.datetime.now()
    supplier_id = supplier['id']

    def _new(supplier, old_orderlist=None):
        orderlist = OrderList(created_by=OrderList.CREATED_BY_MACHINE,
                              status=OrderList.SUBMITTING,
                              note=u'-->%s:自动生成订货单' % now.strftime('%m月%d %H:%M'))
        if supplier_id:
            orderlist.supplier_id = supplier_id

        last_pay_time = supplier.get('last_pay_time')
        ware_by = supplier.get('ware_by')
        if last_pay_time and last_pay_time > common.constants.MIN_DATETIME:
            orderlist.last_pay_date = last_pay_time.date()
        if ware_by:
            if ware_by == WARE_SH:
                orderlist.p_district = OrderList.NEAR
            elif ware_by == WARE_COMPANY:
                orderlist.p_district = OrderList.NEAR
            elif ware_by == WARE_GZ:
                orderlist.p_district = OrderList.GUANGDONG
        if old_orderlist:
            if old_orderlist.buyer_id:
                orderlist.buyer_id = old_orderlist.buyer_id
            if old_orderlist.p_district:
                orderlist.p_district = old_orderlist.p_district
        orderlist.save()
        log_action(1, orderlist, ADDITION, '自动生成订货单')

        amount = .0
        for product in supplier['products']:
            for sku in product['skus']:
                orderdetail = OrderDetail(
                    orderlist_id=orderlist.id,
                    product_id=product['id'],
                    outer_id=product['outer_id'],
                    product_name=product['name'],
                    chichu_id=sku['id'],
                    product_chicun=sku['properties_name'],
                    buy_quantity=abs(sku['effect_quantity']),
                    buy_unitprice=sku['cost'],
                    total_price=abs(sku['effect_quantity'] * sku['cost']))
                amount += float(orderdetail.buy_unitprice) * orderdetail.buy_quantity
                orderdetail.save()
        orderlist.order_amount = amount
        orderlist.save()

    def _merge(supplier, old_orderlist):
        old_orderdetails = {}
        for old_orderdetail in old_orderlist.order_list.all():
            old_orderdetails[int(
                old_orderdetail.chichu_id)] = old_orderdetail

        for product in supplier['products']:
            for sku in product['skus']:
                if sku['id'] in old_orderdetails:
                    orderdetail = old_orderdetails[sku['id']]
                    orderdetail.buy_quantity += abs(sku['effect_quantity'])
                    orderdetail.total_price += (
                                                   orderdetail.buy_unitprice or
                                                   sku['cost']) * abs(sku['effect_quantity'])
                    orderdetail.save()
                else:
                    orderdetail = OrderDetail(
                        orderlist_id=old_orderlist.id,
                        product_id=product['id'],
                        outer_id=product['outer_id'],
                        product_name=product['name'],
                        chichu_id=sku['id'],
                        product_chicun=sku['properties_name'],
                        buy_quantity=abs(sku['effect_quantity']),
                        buy_unitprice=sku['cost'],
                        total_price=abs(sku['effect_quantity'] * sku[
                            'cost']))
                    orderdetail.save()

        amount = .0
        for orderdetail in old_orderlist.order_list.all():
            amount += float(orderdetail.buy_unitprice) * orderdetail.buy_quantity

        old_orderlist.order_amount = amount
        old_orderlist.note += '\n-->%s:自动合并订货单' % now.strftime('%m月%d %H:%M')
        old_orderlist.save()
        log_action(1, old_orderlist, CHANGE, '自动合并订货单')

    old_orderlist = None
    rows = OrderList.objects.filter(
        supplier_id=supplier_id,
        created_by=OrderList.CREATED_BY_MACHINE) \
               .exclude(status=OrderList.ZUOFEI).order_by('-created')[:1]
    if rows:
        old_orderlist = rows[0]
    if not old_orderlist:
        _new(supplier)
    else:
        if old_orderlist.status != OrderList.SUBMITTING:
            _new(supplier, old_orderlist)
        else:
            _merge(supplier, old_orderlist)


@task(max_retries=3, default_retry_delay=5)
def create_dinghuo():
    for supplier in get_suppliers(datetime.datetime(2016, 4, 1)):
        create_orderlist(supplier)


from django.db import IntegrityError


@task(max_retries=3, default_retry_delay=6)
def task_orderdetail_update_productskustats_inbound_quantity(sku_id):
    """
    Whenever we have products inbound, we update the inbound quantity.
    0) OrderDetail arrival_time add db_index=True
    1) we should build joint-index for (sku,arrival_time)?
    --Zifei 2016-04-18
    """
    from flashsale.dinghuo.models import OrderDetail
    from shopback.items.models import ProductSkuStats

    sum_res = OrderDetail.objects.filter(chichu_id=sku_id,
                                         arrival_time__gt=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME) \
        .aggregate(total=Sum('arrival_quantity'))
    total = sum_res["total"] or 0

    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        product_id = ProductSku.objects.get(id=sku_id).product.id
        try:
            stat = ProductSkuStats(sku_id=sku_id, product_id=product_id, inbound_quantity=total)
            stat.save()
        except IntegrityError as exc:
            logger.warn(
                "IntegrityError - productskustat/inbound_quantity | sku_id: %s, inbound_quantity: %s" % (sku_id, total))
            raise task_orderdetail_update_productskustats_inbound_quantity.retry(exc=exc)
    else:
        stat = stats[0]
        if stat.inbound_quantity != total:
            stat.inbound_quantity = total
            stat.save(update_fields=['inbound_quantity', 'modified'])


@task()
def task_update_product_sku_stat_rg_quantity(sku_id):
    from shopback.items.models import ProductSkuStats
    sum_res = RGDetail.objects.filter(skuid=sku_id,
                                      created__gte=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME,
                                      return_goods__status__in=[ReturnGoods.DELIVER_RG,
                                                                ReturnGoods.REFUND_RG,
                                                                ReturnGoods.SUCCEED_RG],
                                      type=RGDetail.TYPE_REFUND).aggregate(total=Sum('num'))
    total = sum_res["total"] or 0
    stat = ProductSkuStats.objects.get(sku_id=sku_id)
    if stat.rg_quantity != total:
        stat.rg_quantity = total
        stat.save(update_fields=['rg_quantity'])


@task()
def task_purchase_detail_update_purchase_order(pd):
    # print "debug: %s" % utils.get_cur_info()
    res = PurchaseDetail.objects.filter(purchase_order_unikey=pd.purchase_order_unikey). \
        aggregate(b_num=Sum('book_num'), n_num=Sum('need_num'), a_num=Sum('arrival_num'))
    book_num = res['b_num'] or 0
    need_num = res['n_num'] or 0
    arrival_num = res['a_num'] or 0

    po = PurchaseOrder.objects.filter(uni_key=pd.purchase_order_unikey).first()
    if not po:
        supplier = utils.get_supplier(pd.sku_id)
        if not supplier:
            logger.error("supplier does not exist|sku_id:%s" % pd.sku_id)
            return
        po = PurchaseOrder(uni_key=pd.purchase_order_unikey, supplier_id=supplier.id,
                           supplier_name=supplier.supplier_name,
                           book_num=book_num, need_num=need_num, arrival_num=arrival_num)
        po.save()
    else:
        if po.book_num != book_num or po.need_num != need_num or po.arrival_num != arrival_num:
            po.book_num = book_num
            po.need_num = need_num
            po.arrival_num = arrival_num
            po.save(update_fields=['book_num', 'need_num', 'arrival_num', 'modified'])


@task()
def task_purchasedetail_update_orderdetail(pd):
    # we should re-calculate the num of records each time we sync pd and od.
    res = PurchaseArrangement.objects.filter(purchase_order_unikey=pd.purchase_order_unikey,
                                             sku_id=pd.sku_id, status=PurchaseArrangement.EFFECT).aggregate(total=Sum('num'))
    total = res['total'] or 0
    total_price = total * pd.unit_price_display

    od = OrderDetail.objects.filter(purchase_detail_unikey=pd.uni_key).first()
    if not od:
        product = utils.get_product(pd.sku_id)
        od = OrderDetail(product_id=product.id, outer_id=pd.outer_id, product_name=pd.title, chichu_id=pd.sku_id,
                         product_chicun=pd.sku_properties_name, buy_quantity=total, buy_unitprice=pd.unit_price_display,
                         total_price=total_price, purchase_detail_unikey=pd.uni_key,
                         purchase_order_unikey=pd.purchase_order_unikey)

        ol = OrderList.objects.filter(purchase_order_unikey=pd.purchase_order_unikey).first()
        if ol:
            od.orderlist_id = ol.id

        od.save()
    else:
        if od.orderlist_id and OrderList.objects.get(id=od.orderlist_id).stage > 0:
            return
        if od.total_price != total_price or od.buy_quantity != total:
            od.buy_quantity = total
            od.buy_unitprice = pd.unit_price_display
            od.total_price = total_price
            od.save(update_fields=['buy_quantity', 'buy_unitprice', 'total_price', 'updated'])


@task()
def task_orderlist_update_self(ol):
    ol.update_stage()


@task()
def task_orderdetail_update_orderlist(od):
    if not od.purchase_order_unikey:
        od.orderlist.save()
        return

    ol = OrderList.objects.filter(purchase_order_unikey=od.purchase_order_unikey).first()
    if not ol:
        supplier = utils.get_supplier(od.chichu_id)
        if not supplier:
            logger.error("No supplier for orderdetail: %d" % od.id)
            return

        p_district = OrderList.NEAR
        if supplier.ware_by == WARE_GZ:
            p_district = OrderList.GUANGDONG
        now = datetime.datetime.now()
        ol = OrderList(purchase_order_unikey=od.purchase_order_unikey, order_amount=od.total_price,
                       supplier_id=supplier.id, p_district=p_district, created_by=OrderList.CREATED_BY_MACHINE,
                       status=OrderList.SUBMITTING, note=u'-->%s:动态生成订货单' % now.strftime('%m月%d %H:%M'))

        prev_orderlist = OrderList.objects.filter(supplier_id=supplier.id,
                                                  created_by=OrderList.CREATED_BY_MACHINE).exclude(
            status=OrderList.ZUOFEI).order_by('-created').first()
        if prev_orderlist and prev_orderlist.buyer_id:
            ol.buyer_id = prev_orderlist.buyer_id

        ol.save()
    else:
        od_sum = OrderDetail.objects.filter(purchase_order_unikey=od.purchase_order_unikey).aggregate(
            total=Sum('total_price'))
        purchase_total_num = OrderDetail.objects.filter(purchase_order_unikey=od.purchase_order_unikey).aggregate(
            total=Sum('buy_quantity')).get('total') or 0
        total = od_sum['total'] or 0
        if ol.order_amount != total or ol.purchase_total_num != purchase_total_num:
            if ol.is_open():
                ol.order_amount = total
                ol.purchase_total_num = purchase_total_num
                ol.save(update_fields=['order_amount', 'updated', 'purchase_total_num'])
            else:
                logger.warn("ZIFEI error: tying to modify booked order_list| ol.id: %s, od: %s" % (ol.id, od.id))
        else:
            ol.save(update_fields=['updated'])


@task(max_retries=3, default_retry_delay=6)
@transaction.atomic
def task_purchasearrangement_update_purchasedetail(pa):
    # print "debug: %s" % utils.get_cur_info()

    res = PurchaseArrangement.objects.filter(purchase_order_unikey=pa.purchase_order_unikey,
                                             sku_id=pa.sku_id, status=PurchaseArrangement.EFFECT).aggregate(total=Sum('num'))

    total = res['total'] or 0

    unit_price = int(utils.get_unit_price(pa.sku_id) * 100)
    uni_key = utils.gen_purchase_detail_unikey(pa)
    pd = PurchaseDetail.objects.filter(uni_key=uni_key).first()
    if not pd:
        pd = PurchaseDetail(uni_key=uni_key, purchase_order_unikey=pa.purchase_order_unikey,
                                unit_price=unit_price, book_num=total, need_num=total)
        fields = ['outer_id', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name']
        utils.copy_fields(pd, pa, fields)
        pd.save()
    else:
        if pd.is_open():
            if pd.book_num != total or pd.unit_price != unit_price:
                pd.book_num = total
                pd.need_num = total
                pd.unit_price = unit_price
                pd.save(update_fields=['book_num', 'need_num', 'unit_price', 'modified'])
            return


@task()
@transaction.atomic
def task_packageskuitem_update_purchase_arrangement(psi):
    pa = PurchaseArrangement.objects.filter(oid=psi.oid).first()
    if pa:
        if not pa.initial_book:
            if pa.status == PurchaseArrangement.CANCEL and psi.is_booking_needed():
                if pa.status == PurchaseArrangement.CANCEL and pa.purchase_order.status in [PurchaseOrder.BOOKED, PurchaseOrder.FINISHED]:
                    pa_new_uni_key = PurchaseOrder.gen_purchase_order_unikey(psi)
                    pa.purchase_order_unikey = pa_new_uni_key
                    pa.uni_key = PurchaseArrangement.gen_purchase_arrangement_unikey(pa_new_uni_key, psi.get_purchase_uni_key())
                pa.status = PurchaseArrangement.EFFECT
                pa.save()
            elif pa.status == PurchaseArrangement.EFFECT and (psi.is_booking_assigned() or psi.is_canceled()):
                pa.status = PurchaseArrangement.CANCEL
                pa.save()
    else:
        PurchaseArrangement.create(psi)


from shopapp.smsmgr.models import SMSPlatform, SMS_NOTIFY_VERIFY_CODE
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE


def send_msg(mobile, content):
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()
    if not platform:
        logger.error(u"send_msg: SMSPlatform object not found !")
        return
    try:
        params = {
            'content': content,
            'userid': platform.user_id,
            'account': platform.account,
            'password': platform.password,
            'mobile': mobile,
            'taskName': "小鹿美美验证码",
            'mobilenumber': 1,
            'countnumber': 1,
            'telephonenumber': 0,
            'action': 'send',
            'checkcontent': '0'
        }

        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')

        manager = sms_manager()
        success = False

        # 创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_VERIFY_CODE,
                                           params['content'])
        # 发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)


@task()
def task_update_purchasedetail_status(po):
    """
    invoke when user click button to book purchase_order.
    """
    pds = PurchaseDetail.objects.filter(purchase_order_unikey=po.uni_key).update(status=po.status)


@task()
def task_update_purchasearrangement_status(po):
    """
    invoke when user click button to book purchase_order.
    """
    pas = PurchaseArrangement.objects.filter(purchase_order_unikey=po.uni_key, status=PurchaseArrangement.EFFECT).update(
        purchase_order_status=po.status)


@task()
def task_update_purchasearrangement_initial_book(po):
    """
    invoke when user click button to book purchase_order.
    """
    pas = PurchaseArrangement.objects.filter(purchase_order_unikey=po.uni_key, status=PurchaseArrangement.EFFECT)
    pas.update(purchase_order_status=po.status, initial_book=True)

    from shopback.trades.models import PackageSkuItem
    book_time = datetime.datetime.now()
    for pa in pas:
        psi = PackageSkuItem.objects.filter(oid=pa.oid).first()
        PackageSkuItem.objects.filter(oid=pa.oid).update(purchase_order_unikey=po.uni_key, book_time=book_time)


@task()
def task_check_with_purchase_order(ol):
    res = OrderDetail.objects.filter(orderlist=ol).aggregate(total=Sum('buy_quantity'))
    total = res['total'] or 0

    mobile = '18616787808'

    if not ol.supplier:
        content = 'no supplier, order_list id: %s' % ol.id
        send_msg(mobile, content)
        return

    supplier_id = ol.supplier.id
    po = PurchaseOrder.objects.filter(supplier_id=supplier_id).order_by('-created').first()

    if not po:
        content = 'supplier_id:%s, no book_num, %s' % (supplier_id, total)
        send_msg(mobile, content)
        return

    if po.book_num != total:
        content = 'supplier_id:%s, book_num:%s-%s' % (supplier_id, po.book_num, total)
        send_msg(mobile, content)

    po.status = PurchaseOrder.BOOKED
    po.save()

    task_update_purchasearrangement_status.delay(po)
    task_update_purchasearrangement_initial_book.delay(po)


from flashsale.pay.models import SaleOrderSyncLog
from shopback.trades.models import PackageSkuItem


# def create_purchaserecord_check_log(time_from, type, uni_key):
#     psi_unikey = "%s|%s" % (SaleOrderSyncLog.SO_PSI, time_from)
#     psi_log = SaleOrderSyncLog.objects.filter(uni_key=psi_unikey).first()
#     if not (psi_log and psi_log.is_completed()):
#         return
#     time_to = time_from + datetime.timedelta(hours=1)
#     psis = PackageSkuItem.objects.filter(pay_time__gt=time_from, pay_time__lte=time_to)
#     target_num = psis.count()
#     actual_num = 0
#     for psi in psis:
#         pr = PurchaseRecord.objects.filter(oid=psi.oid).first()
#         if pr:
#             actual_num += 1
#         elif psi.is_booking_needed():
#             psi.save()
#     log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key, type=type, target_num=target_num,
#                            actual_num=actual_num)
#     if target_num == actual_num:
#         log.status = SaleOrderSyncLog.COMPLETED
#     log.save()
#
#
# @task()
# def task_packageskuitem_check_purchaserecord():
#     type = SaleOrderSyncLog.PSI_PR
#     log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
#     if not log:
#         return
#
#     time_from = log.time_to
#     now = datetime.datetime.now()
#
#     if time_from > now - datetime.timedelta(hours=2):
#         return
#
#     uni_key = "%s|%s" % (type, time_from)
#     log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
#     if not log:
#         create_purchaserecord_check_log(time_from, type, uni_key)
#     elif not log.is_completed():
#         time_to = log.time_to
#         psis = PackageSkuItem.objects.filter(pay_time__gt=time_from, pay_time__lte=time_to)
#         target_num = psis.count()
#         actual_num = 0
#         for psi in psis:
#             pr = PurchaseRecord.objects.filter(oid=psi.oid).first()
#             if pr:
#                 actual_num += 1
#                 if psi.is_booking_needed() and pr.status == PurchaseRecord.EFFECT:
#                     continue
#                 if (not psi.is_booking_needed()) and pr.status == PurchaseRecord.CANCEL:
#                     continue
#             psi.save(update_fields=['modified'])
#
#         update_fields = []
#         if log.target_num != target_num:
#             log.target_num = target_num
#             update_fields.append('target_num')
#         if log.actual_num != actual_num:
#             log.actual_num = actual_num
#             update_fields.append('actual_num')
#         if target_num == actual_num:
#             log.status = SaleOrderSyncLog.COMPLETED
#             update_fields.append('status')
#         if update_fields:
#             log.save(update_fields=update_fields)
#
#         if target_num != actual_num:
#             logger.error("task_packageskuitem_check_purchaserecord|uni_key: %s, target_num: %s, actual_num: %s" % (
#                 uni_key, target_num, actual_num))


def create_purchaseorder_booknum_check_log(time_from, type, uni_key):
    res = PackageSkuItem.objects.filter(assign_status=PackageSkuItem.NOT_ASSIGNED, purchase_order_unikey='').aggregate(
        total=Sum('num'))
    target_num = res['total'] or 0

    pos = PurchaseOrder.objects.filter(status=PurchaseOrder.OPEN)
    actual_num = 0
    for po in pos:
        res = OrderDetail.objects.filter(purchase_order_unikey=po.uni_key).aggregate(total=Sum('buy_quantity'))
        total = res['total'] or 0
        actual_num += total

    time_to = time_from + datetime.timedelta(hours=1)

    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key, type=type, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_check_purchaseorder_booknum():
    type = SaleOrderSyncLog.BOOKNUM
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return

    time_from = log.time_to
    now = datetime.datetime.now()

    if time_from > now - datetime.timedelta(hours=2):
        return

    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_purchaseorder_booknum_check_log(time_from, type, uni_key)
    elif not log.is_completed():
        res = PackageSkuItem.objects.filter(assign_status=PackageSkuItem.NOT_ASSIGNED,
                                            purchase_order_unikey='').aggregate(total=Sum('num'))
        target_num = res['total'] or 0

        pos = PurchaseOrder.objects.filter(status=PurchaseOrder.OPEN)
        actual_num = 0
        for po in pos:
            pds = PurchaseDetail.objects.filter(purchase_order_unikey=po.uni_key)
            for pd in pds:
                od = OrderDetail.objects.filter(purchase_detail_unikey=pd.uni_key).first()
                if od:
                    actual_num += od.buy_quantity
                if (not od) or od.buy_quantity != pd.book_num:
                    pd.save(update_fields=['modified'])

        update_fields = []
        if log.target_num != target_num:
            log.target_num = target_num
            update_fields.append('target_num')
        if log.actual_num != actual_num:
            log.actual_num = actual_num
            update_fields.append('actual_num')
        if target_num == actual_num:
            log.status = SaleOrderSyncLog.COMPLETED
            update_fields.append('status')
        if update_fields:
            log.save(update_fields=update_fields)

        #if target_num != actual_num:
        #    logger.error("task_check_purchaseorder_booknum|uni_key: %s, target_num: %s, actual_num: %s" % (
        #        uni_key, target_num, actual_num))


def create_inbound_out_stock_check_log(time_from, uni_key):
    from flashsale.dinghuo.models import InBound, InBoundDetail
    time_to = time_from + datetime.timedelta(hours=1)
    target_num = sum([i.out_stock_num for i in
                  InBoundDetail.objects.filter(inbound__check_time__range=(time_from, time_to))])
    actual_num = sum([i.all_arrival_quantity - i.all_allocate_quantity for i in
                  InBound.objects.filter(check_time__range=(time_from, time_to), out_stock=True)])
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.INBOUND_OUT_STOCK, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_inbound_check_out_stock():
    type = SaleOrderSyncLog.INBOUND_OUT_STOCK
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return
    time_from = log.time_to
    now = datetime.datetime.now()
    if time_from > now - datetime.timedelta(hours=1):
        return
    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_inbound_out_stock_check_log(time_from, uni_key)
        task_inbound_check_out_stock.delay()


def create_inbound_inferior_check_log(time_from, uni_key):
    from flashsale.dinghuo.models import InBound, InBoundDetail
    time_to = time_from + datetime.timedelta(hours=1)
    target_num = InBoundDetail.objects.filter(checked=True, inbound__check_time__range=(time_from, time_to)).aggregate(
        n=Sum('inferior_quantity')).get('n', 0) or 0
    actual_num = sum([i.all_inferior_quantity for i in
                  InBound.objects.filter(check_time__range=(time_from, time_to), checked=True)])
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.INBOUND_INFERIOR, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_inbound_check_inferior():
    return
    type = SaleOrderSyncLog.INBOUND_INFERIOR
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return
    time_from = log.time_to
    now = datetime.datetime.now()
    if time_from > now - datetime.timedelta(hours=1):
        return

    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_inbound_inferior_check_log(time_from, uni_key)
        task_inbound_check_inferior.delay()


def get_orderdetail_buyer_maping(start_time, end_time):
    start_time = start_time - datetime.timedelta(days=90)
    end_time = end_time + datetime.timedelta(days=30)
    orderdetails = OrderDetail.objects.filter(orderlist__created__range=(start_time, end_time))
    detail_buyer_values_list = orderdetails.values_list('product_id', 'orderlist__buyer').distinct()
    return dict(detail_buyer_values_list)

@task()
def task_save_package_backorder_stats():
    logger.info('task_save_package_backorder_stats start')
    from shopback.trades.models import PackageSkuItem

    now = datetime.datetime.now()
    stats_day_list = [(3, 'three_backorder_num'), (5, 'five_backorder_num'), (15, 'fifteen_backorder_num')]
    purchaser_map = get_orderdetail_buyer_maping(now - datetime.timedelta(days=max([ds[0] for ds in stats_day_list])) , now)

    q = PackageSkuItem.objects.filter(
        assign_status__in=[PackageSkuItem.NOT_ASSIGNED, PackageSkuItem.ASSIGNED]
    )
    for day, day_field in stats_day_list:
        day_dt = now - datetime.timedelta(days=day)
        sku_id_set = q.filter(pay_time__gte=day_dt).values_list('sku_id', flat=True).distinct()
        sku_product_map = dict(ProductSku.objects.filter(id__in=sku_id_set).values_list('id', 'product_id'))

        order_values_list = q.filter(pay_time__gte=day_dt).values_list('sku_id', 'oid', 'num')
        purchaser_dict = {}
        for sku_id, oid, num in order_values_list:
            purchaser = purchaser_map.get(str(sku_product_map.get(int(sku_id))))
            purchaser_dict.setdefault(purchaser, {'num':0, 'orders': []})
            purchaser_dict[purchaser]['num'] += num
            purchaser_dict[purchaser]['orders'].append(oid)

        logger.info('%s, %s'%(day_dt, purchaser_dict))
        for purchaser , stats in purchaser_dict.items():
            backorder = PackageBackOrderStats.objects.filter(day_date=now, purchaser_id=purchaser).first()
            if not backorder:
                backorder = PackageBackOrderStats(day_date=now, purchaser_id=purchaser)
            setattr(backorder, day_field, stats['num'])
            order_ids = backorder.backorder_ids and backorder.backorder_ids.split(',') or []
            order_ids.extend(stats['orders'])
            backorder.backorder_ids = ','.join(set(order_ids))
            backorder.save()

    logger.info('task_save_package_backorder_stats end')

