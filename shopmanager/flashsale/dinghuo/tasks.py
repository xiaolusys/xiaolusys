# -*- coding:utf-8 -*-
from __future__ import division
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
import sys

@task(max_retry=3, default_retry_delay=5)
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


@task(max_retry=3, default_retry_delay=5)
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


@task(max_retry=3, default_retry_delay=5)
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


@task(max_retry=3, default_retry_delay=5)
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
            type = sys.getfilesystemencoding()   # 关键
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

from flashsale.dinghuo.models_stats import RecordGroupPoint
from flashsale.dinghuo.models_user import MyUser, MyGroup


@task(max_retry=3, default_retry_delay=5)
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


@task(max_retry=3, default_retry_delay=5)
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
                      "and status!='delete' {1}) as A " \
                      "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku where status!='delete') as B " \
                      "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(
            target_date, group_sql)
    ding_huo_sql = "select B.outer_id,B.chichu_id,sum(if(A.status='草稿' or A.status='审核',B.buy_quantity,0)) as buy_quantity,sum(if(A.status='7',B.buy_quantity,0)) as sample_quantity," \
                   "sum(if(status='5' or status='6' or status='有问题' or status='验货完成' or status='已处理',B.arrival_quantity,0)) as arrival_quantity,B.effect_quantity,A.status" \
                   " from (select id,status from suplychain_flashsale_orderlist where status not in ('作废') and created between '{0}' and '{1}') as A " \
                   "left join (select orderlist_id,outer_id,chichu_id,buy_quantity,arrival_quantity,(buy_quantity-inferior_quantity-non_arrival_quantity) as effect_quantity " \
                   "from suplychain_flashsale_orderdetail) as B on A.id=B.orderlist_id group by outer_id,chichu_id".format(
        dinghuo_begin, query_time)
    sql = "select product.outer_id,product.product_name,product.outer_sku_id,product.pic_path,product.properties_alias," \
          "order_info.sale_num,ding_huo_info.buy_quantity,ding_huo_info.effect_quantity,product.sku_id,product.exist_stock_num," \
          "product.id,ding_huo_info.arrival_quantity,ding_huo_info.sample_quantity " \
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
                     "arrival_num": arrival_num}
        if dhstatus == u'0' or ((flag_of_more or flag_of_less) and dhstatus == u'1') or (
                    flag_of_less and dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
            if product[0] not in trade_dict:
                trade_dict[product[0]] = [temp_dict]
            else:
                trade_dict[product[0]].append(temp_dict)
    trade_dict = sorted(trade_dict.items(), key=lambda d: d[0])
    result_dict = {"total_more_num": total_more_num, "total_less_num": total_less_num, "trade_dict": trade_dict}
    return result_dict


from supplychain.supplier.models import SaleProduct
from flashsale.pay.models_refund import SaleRefund
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


@task()
def calcu_refund_info_by_pro(pro_queryset=None):
    from django.forms import model_to_dict
    from django.db.models import Sum
    data = []
    for i in pro_queryset:
        # # 退款数量 return_num
        #  实时过滤退款单中的状态 2015-09-30
        skus = i.prod_skus.all()
        for sku in skus:
            sale_refunds = SaleRefund.objects.filter(item_id=i.id, sku_id=sku.id)

            # 申请退货数量（已经发货生成的退货申请）
            sended_refunds = sale_refunds.filter(good_status=SaleRefund.BUYER_RECEIVED)

            # 退货途中数量(已经到货，填写了退货物流信息的退货申请) 排除　退款关闭，退款成功，等待返款的状态
            backing_refunds = sale_refunds.filter(good_status=SaleRefund.BUYER_RETURNED_GOODS).exclude\
                (status__in=(SaleRefund.REFUND_CLOSED, SaleRefund.REFUND_SUCCESS, SaleRefund.REFUND_APPROVE))

            # 退货到仓库的数量
            backed_refunds = RefundProduct.objects.filter(outer_id=i.outer_id, outer_sku_id=sku.outer_id)

            # 已经退货数量
            already_return_goods = RGDetail.objects.filter(skuid=sku.id)  # 过滤出审核通过的退货单

            already_num = already_return_goods.aggregate(total_al=Sum("num")).get("total_al") or 0
            already_inferior_num_num = already_return_goods.aggregate(total_al=Sum("inferior_num")).get("total_al") or 0
            already_return_goods_num = already_num + already_inferior_num_num

            return_num = sale_refunds.aggregate(total_num=Sum("refund_num")).get("total_num") or 0  # 退款数量

            sended_refund_num = sended_refunds.aggregate(total_num=Sum("refund_num")).get("total_num") or 0  # 申请退货数量
            backing_refund_num = backing_refunds.aggregate(total_num=Sum("refund_num")).get("total_num") or 0  # 退货途中数量
            backed_refund = backed_refunds.aggregate(total_num=Sum("num")).get("total_num") or 0  # 退货到仓库数量

            if return_num == 0 and sended_refund_num == 0 and backed_refund == 0:
                continue
            # 找出供应商和买手
            sale_supplier_name, sale_supplier_pk, \
            sale_supplier_contact, sale_supplier_mobile = get_sale_product(i.sale_product)

            prod = model_to_dict(i, exclude=("created", "modified", "sale_time"))
            prod['s_id'] = sku.id
            prod['s_cost'] = sku.cost
            prod["sku_quantity"] = sku.quantity  # 库存数
            prod['sku_inferior_num'] = sku.sku_inferior_num  # sku的次品数量
            prod['sku_wait_post_num'] = sku.wait_post_num  # 待发数
            prod['return_num'] = return_num  # 退款数量
            prod['sended_refund_num'] = sended_refund_num  # 申请退货数量
            prod['backing_refund_num'] = backing_refund_num  # 退货途中数量
            prod['backed_refund'] = backed_refund  # 退货到仓库数量

            prod['sale_supplier_name'] = sale_supplier_name  # 供应商名称
            prod['sale_supplier_pk'] = sale_supplier_pk
            prod['sale_supplier_contact'] = sale_supplier_contact  # 联系人
            prod['sale_supplier_mobile'] = sale_supplier_mobile  # 手机
            prod['already_num'] = already_return_goods_num  # 已退数量

            data.append(prod)
    return data


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
        name, cost, quantity, wait_post_num, inferior_num, pro_id, sku_id, sale_product = get_args_by_re_product(re_pro.outer_id,
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


from flashsale.dinghuo.models_stats import DailyStatsPreview, DailySupplyChainStatsOrder


@task()
def task_daily_preview(default_time=15):
    function_of_settime(default_time)


def function_of_settime(default_time):
    today = datetime.date.today()
    for i in range(1, default_time):
        target_order = DailySupplyChainStatsOrder.objects.filter(sale_time=today-datetime.timedelta(days=i))
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
                total_return += one_data.return_num                                     # 退款数
                total_cost += one_data.cost_of_product                                  # 成本
                total_num += one_data.sale_num                                          # 销售数
                total_money += one_data.sale_cost_of_product                            # 成本
                total_return_money += (one_product.agent_price * one_data.return_num)   # 退款额
                total_time += during_time                                               # 发货速度
        if total_num != 0:
            fahuo = total_time / total_num
            one_preview, state = DailyStatsPreview.objects.get_or_create(sale_time=today-datetime.timedelta(days=i))
            one_preview.sale_num = total_num
            one_preview.goods_out_time = fahuo
            one_preview.shelf_num = shelf_num
            one_preview.return_num = total_return
            one_preview.cost_of_product = total_num
            one_preview.sale_money = total_money
            one_preview.return_money = total_return_money
            one_preview.save()