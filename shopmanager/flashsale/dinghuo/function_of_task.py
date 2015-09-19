# coding:utf-8
__author__ = 'yann'
import datetime
import functions
import time
from flashsale.dinghuo.models_stats import SupplyChainStatsOrder, DailySupplyChainStatsOrder
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models import OrderDetail


def get_daily_order_stats(prev_day):
    """统计每天的订单里面的商品的平均下单时间"""
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=prev_day)
    start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
    end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
    order_qs = functions.get_source_orders(start_dt, end_dt)

    order_dict = {}
    for order in order_qs:
        pay_time = time.mktime(order['pay_time'].timetuple()) or 0
        num = order["num"]
        if order["outer_id"] in order_dict:
            if order["outer_sku_id"] in order_dict[order["outer_id"]]:
                old_num = order_dict[order["outer_id"]][order["outer_sku_id"]]["num"]
                old_pay_time = order_dict[order["outer_id"]][order["outer_sku_id"]]["pay_time"]
                pay_time = (pay_time * num + old_pay_time * old_num) / (old_num + num)
                order_dict[order["outer_id"]][order["outer_sku_id"]]["num"] = old_num + num
                order_dict[order["outer_id"]][order["outer_sku_id"]]["pay_time"] = pay_time
            else:
                order_dict[order["outer_id"]][order["outer_sku_id"]] = {"num": num, 'pay_time': pay_time}
        else:
            order_dict[order["outer_id"]] = {order["outer_sku_id"]: {"num": num, 'pay_time': pay_time}}

    for product_outer_id, product_dict in order_dict.items():
        pro_bean = Product.objects.filter(outer_id=product_outer_id)
        if pro_bean.count() > 0 and pro_bean[0].sale_time and not (pro_bean[0].sale_time > target_day):
            for outer_sku_id, product in product_dict.items():
                temp_new_data = SupplyChainStatsOrder.objects.filter(product_id=product_outer_id,
                                                                     outer_sku_id=outer_sku_id,
                                                                     sale_time=target_day)
                if temp_new_data.count() > 0:
                    stats_new = temp_new_data[0]
                    stats_new.sale_num = product['num']
                    stats_new.trade_general_time = product['pay_time']
                    stats_new.save()
                else:
                    stats_new = SupplyChainStatsOrder(product_id=product_outer_id, outer_sku_id=outer_sku_id,
                                                      sale_time=target_day, sale_num=product['num'],
                                                      shelve_time=pro_bean[0].sale_time,
                                                      trade_general_time=product['pay_time'])
                    stats_new.save()


def get_daily_out_order_stats(prev_day):
    """统计每天的订单里面的商品的平均出货时间"""
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=prev_day)
    start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
    end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
    order_qs = functions.get_source_orders_consign(start_dt, end_dt)

    order_dict = {}
    for order in order_qs:
        pay_time = time.mktime(order['merge_trade__weight_time'].timetuple()) or 0
        sale_num = order["num"]
        if order["outer_id"] in order_dict:
            if order["outer_sku_id"] in order_dict[order["outer_id"]]:
                old_sale_num = order_dict[order["outer_id"]][order["outer_sku_id"]]["num"]
                old_pay_time = order_dict[order["outer_id"]][order["outer_sku_id"]]["pay_time"]
                pay_time = (pay_time * sale_num + old_pay_time * old_sale_num) / (old_sale_num + sale_num)
                order_dict[order["outer_id"]][order["outer_sku_id"]]["num"] = old_sale_num + sale_num
                order_dict[order["outer_id"]][order["outer_sku_id"]]["pay_time"] = pay_time
            else:
                order_dict[order["outer_id"]][order["outer_sku_id"]] = {"num": sale_num, 'pay_time': pay_time}
        else:
            order_dict[order["outer_id"]] = {order["outer_sku_id"]: {"num": sale_num, 'pay_time': pay_time}}

    for product_outer_id, product_dict in order_dict.items():
        pro_bean = Product.objects.filter(outer_id=product_outer_id)
        if pro_bean.count() > 0 and pro_bean[0].sale_time and not (pro_bean[0].sale_time > target_day):
            for outer_sku_id, product in product_dict.items():
                temp_new_data = SupplyChainStatsOrder.objects.filter(product_id=product_outer_id,
                                                                     outer_sku_id=outer_sku_id,
                                                                     sale_time=target_day)
                if temp_new_data.count() > 0:
                    stats_new = temp_new_data[0]
                    stats_new.goods_out_num = product['num']
                    stats_new.goods_out_time = product['pay_time']
                    stats_new.save()
                else:
                    stats_new = SupplyChainStatsOrder(product_id=product_outer_id, outer_sku_id=outer_sku_id,
                                                      sale_time=target_day, goods_out_num=product['num'],
                                                      shelve_time=pro_bean[0].sale_time,
                                                      goods_out_time=product['pay_time'])
                    stats_new.save()


def get_daily_ding_huo_stats(prev_day):
    """统计每天的大货里面的商品的平均拍货时间"""
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=prev_day)
    start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
    end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
    order_details_dict = OrderDetail.objects.values("outer_id", "chichu_id", "buy_quantity", "created"). \
        exclude(orderlist__status=u'作废').filter(created__gte=start_dt, created__lte=end_dt)

    ding_huo_dict = {}
    for order_detail in order_details_dict:
        order_deal_time = time.mktime(order_detail['created'].timetuple()) or 0
        ding_huo_num = order_detail['buy_quantity']
        sku = ProductSku.objects.get(id=order_detail["chichu_id"])
        if order_detail["outer_id"] in ding_huo_dict:
            if sku.outer_id in ding_huo_dict[order_detail["outer_id"]]:
                old_num = ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["num"]
                old_time = ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["order_deal_time"]
                order_deal_time = (order_deal_time * ding_huo_num + old_time * old_num) / (old_num + ding_huo_num)
                ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["num"] = old_num + ding_huo_num
                ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["order_deal_time"] = order_deal_time
            else:
                ding_huo_dict[order_detail["outer_id"]][sku.outer_id] = {"num": ding_huo_num,
                                                                         "order_deal_time": order_deal_time}
        else:
            ding_huo_dict[order_detail["outer_id"]] = {
                sku.outer_id: {"num": ding_huo_num, "order_deal_time": order_deal_time}}

    for product_outer_id, product_dict in ding_huo_dict.items():
        pro_bean = Product.objects.filter(outer_id=product_outer_id)
        if pro_bean.count() > 0 and pro_bean[0].sale_time and not (pro_bean[0].sale_time > target_day):
            for outer_sku_id, product in product_dict.items():
                temp_new_data = SupplyChainStatsOrder.objects.filter(product_id=product_outer_id,
                                                                     outer_sku_id=outer_sku_id,
                                                                     sale_time=target_day)
                if temp_new_data.count() > 0:
                    stats_new = temp_new_data[0]
                    stats_new.ding_huo_num = product['num']
                    stats_new.order_deal_time = product['order_deal_time']
                    stats_new.save()
                else:
                    stats_new = SupplyChainStatsOrder(product_id=product_outer_id, outer_sku_id=outer_sku_id,
                                                      sale_time=target_day, ding_huo_num=product['num'],
                                                      shelve_time=pro_bean[0].sale_time,
                                                      order_deal_time=product['order_deal_time'])
                    stats_new.save()


def get_daily_goods_arrival_stats(prev_day):
    """统计每天的大货里面的商品的平均到货时间"""
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=prev_day)
    start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
    end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
    order_details_dict = OrderDetail.objects.values("outer_id", "chichu_id", "arrival_quantity", "inferior_quantity",
                                                    "updated").exclude(orderlist__status=u'作废').filter(
        arrival_time__gte=start_dt, arrival_time__lte=end_dt)

    ding_huo_dict = {}
    for order_detail in order_details_dict:
        order_deal_time = time.mktime(order_detail['updated'].timetuple()) or 0
        ding_huo_num = order_detail['arrival_quantity'] + order_detail['inferior_quantity']
        sku = ProductSku.objects.get(id=order_detail["chichu_id"])
        if ding_huo_num > 0:
            if order_detail["outer_id"] in ding_huo_dict:
                if sku.outer_id in ding_huo_dict[order_detail["outer_id"]]:
                    old_num = ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["num"]
                    old_time = ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["order_deal_time"]
                    order_deal_time = (order_deal_time * ding_huo_num + old_time * old_num) / (old_num + ding_huo_num)
                    ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["num"] = old_num + ding_huo_num
                    ding_huo_dict[order_detail["outer_id"]][sku.outer_id]["order_deal_time"] = order_deal_time
                else:
                    ding_huo_dict[order_detail["outer_id"]][sku.outer_id] = {"num": ding_huo_num,
                                                                             "order_deal_time": order_deal_time}
            else:
                ding_huo_dict[order_detail["outer_id"]] = {
                    sku.outer_id: {"num": ding_huo_num, "order_deal_time": order_deal_time}}

    for product_outer_id, product_dict in ding_huo_dict.items():
        pro_bean = Product.objects.filter(outer_id=product_outer_id)
        if pro_bean.count() > 0 and pro_bean[0].sale_time and not (pro_bean[0].sale_time > target_day):
            for outer_sku_id, product in product_dict.items():
                temp_new_data = SupplyChainStatsOrder.objects.filter(product_id=product_outer_id,
                                                                     outer_sku_id=outer_sku_id,
                                                                     sale_time=target_day)
                if temp_new_data.count() > 0:
                    stats_new = temp_new_data[0]
                    stats_new.arrival_num = product['num']
                    stats_new.goods_arrival_time = product['order_deal_time']
                    stats_new.save()
                else:
                    stats_new = SupplyChainStatsOrder(product_id=product_outer_id, outer_sku_id=outer_sku_id,
                                                      sale_time=target_day, arrival_num=product['num'],
                                                      shelve_time=pro_bean[0].sale_time,
                                                      goods_arrival_time=product['order_deal_time'])
                    stats_new.save()


def daily_data_stats():
    all_data = SupplyChainStatsOrder.objects.all()
    all_data_dict = {}
    for data in all_data:
        if data.product_id in all_data_dict and data.shelve_time in all_data_dict[data.product_id]:
            temp_var = all_data_dict[data.product_id][data.shelve_time]
            if data.ding_huo_num > 0:
                ding_huo_num = temp_var['ding_huo_num']
                ding_huo_time = temp_var['order_deal_time']
                ding_huo_time = (data.ding_huo_num * data.order_deal_time + ding_huo_num * ding_huo_time) / (
                    ding_huo_num + data.ding_huo_num)
                temp_var['order_deal_time'] = ding_huo_time
                temp_var['ding_huo_num'] += data.ding_huo_num
            if data.sale_num > 0:
                sale_num = temp_var['sale_num']
                trade_general_time = temp_var['trade_general_time']
                trade_general_time = (data.sale_num * data.trade_general_time + trade_general_time * sale_num) / (
                    sale_num + data.sale_num)
                temp_var['trade_general_time'] = trade_general_time
                temp_var['sale_num'] += data.sale_num
            if data.arrival_num > 0:
                arrival_num = temp_var['arrival_num']
                goods_arrival_time = temp_var['goods_arrival_time']
                goods_arrival_time = \
                    (data.arrival_num * data.goods_arrival_time + goods_arrival_time * arrival_num) / (
                        arrival_num + data.arrival_num)
                temp_var['goods_arrival_time'] = goods_arrival_time
                temp_var['arrival_num'] += data.arrival_num
            if data.goods_out_num > 0:
                goods_out_num = temp_var['goods_out_num']
                goods_out_time = temp_var['goods_out_time']
                goods_out_time = (data.goods_out_num * data.goods_out_time + goods_out_time * goods_out_num) / (
                    goods_out_num + data.goods_out_num)
                temp_var['goods_out_time'] = goods_out_time
                temp_var['goods_out_num'] += data.goods_out_num
        else:
            all_data_dict[data.product_id] = {data.shelve_time: {"sale_num": data.sale_num,
                                                                 "trade_general_time": data.trade_general_time,
                                                                 "ding_huo_num": data.ding_huo_num,
                                                                 "order_deal_time": data.order_deal_time,
                                                                 "arrival_num": data.arrival_num,
                                                                 "goods_arrival_time": data.goods_arrival_time,
                                                                 "goods_out_num": data.goods_out_num,
                                                                 "goods_out_time": data.goods_out_time}}
    for pro_id, temp_data in all_data_dict.items():
        for shelve_time, data in temp_data.items():
            product = DailySupplyChainStatsOrder.objects.filter(product_id=pro_id, sale_time=shelve_time)
            pro_bean = ProductSku.objects.filter(product__outer_id=pro_id)
            cost = 0
            sale_price = 0
            if pro_bean.count() > 0:
                cost = pro_bean[0].cost * data['sale_num']
                sale_price = pro_bean[0].agent_price * data['sale_num']
            if product.count() > 0:
                daily_order = product[0]
                # daily_order.return_num = get_return_num_by_product_id(pro_id)
                daily_order.inferior_num = get_inferior_num_by_product_id(pro_id)
                daily_order.sale_num = data['sale_num']
                daily_order.ding_huo_num = data['ding_huo_num']
                daily_order.cost_of_product = cost
                daily_order.sale_cost_of_product = sale_price
                daily_order.trade_general_time = data['trade_general_time']
                daily_order.order_deal_time = data['order_deal_time']
                daily_order.goods_arrival_time = data['goods_arrival_time']
                daily_order.goods_out_time = data['goods_out_time']
                daily_order.save()
            else:
                temp = DailySupplyChainStatsOrder(product_id=pro_id, sale_time=shelve_time, sale_num=data['sale_num'],
                                                  ding_huo_num=data['ding_huo_num'],
                                                  cost_of_product=cost, sale_cost_of_product=sale_price,
                                                  # return_num=get_return_num_by_product_id(pro_id),
                                                  inferior_num=get_inferior_num_by_product_id(pro_id),
                                                  trade_general_time=data['trade_general_time'],
                                                  order_deal_time=data['order_deal_time'],
                                                  goods_arrival_time=data['goods_arrival_time'],
                                                  goods_out_time=data['goods_out_time'])
                temp.save()


from shopback.refunds.models import RefundProduct, Refund
from django.db.models import Sum, F
from shopback.trades.models import MergeTrade, MergeOrder


def handler_refund():
    # 过滤今天生成的　原始数据表
    today = datetime.date.today() - datetime.timedelta(days=1)
    ori_datas = SupplyChainStatsOrder.objects.filter(sale_time=today, refund_amount_num__gt=0)  # 退款数量大于0的记录
    # 取出今天统计出来的所有产品的编码
    product_id_vls = ori_datas.values('product_id')
    # 去重处理
    set_p = set()
    for i in product_id_vls:
        set_p.add(i['product_id'])
    # 对编码进行循环
    for i in set_p:
        pro_ds = ori_datas.filter(product_id=i)  # 找出同一个编码的记录
        # 计算退款数量
        refund_amount_nums = pro_ds.aggregate(total_num=Sum('refund_amount_num')).get('total_num') or 0
        # 将退款数量写入　供应链数据统计表　表中
        if refund_amount_nums > 0:
            dsos = DailySupplyChainStatsOrder.objects.filter(product_id=i)
            if dsos.exists():
                dsos[0].return_num = F("return_num") + refund_amount_nums  # 累加同款商品的退款数量
                dsos[0].save()
            else:
                products = Product.objects.filter(outer_id=i)
                if products.exists():
                    DailySupplyChainStatsOrder.objects.create(product_id=i,
                                                              sale_time=products[0].sale_time,
                                                              return_num=refund_amount_nums)


def get_daily_refund_num(pre_day=None):
    if pre_day is None:
        return
    today = datetime.date.today()
    target_day = today - datetime.timedelta(days=pre_day)
    start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
    end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
    ref_pros = RefundProduct.objects.filter(created__gte=start_dt, created__lte=end_dt)
    # SupplyChainStatsOrder 记录创建
    for pro in ref_pros:  # 退货数量计算
        products = Product.objects.filter(outer_id=pro.outer_id)
        if products.exists() and products[0].sale_time:
            scso, state = SupplyChainStatsOrder.objects.get_or_create(product_id=pro.outer_id,
                                                                      outer_sku_id=pro.outer_sku_id,
                                                                      shelve_time=products[0].sale_time,
                                                                      sale_time=target_day)
            # 过滤出　对应产品的退货集合
            ref = ref_pros.filter(outer_id=pro.outer_id, outer_sku_id=pro.outer_sku_id)
            # 计算同款集合中的　数量和
            refund_num = ref.aggregate(total_num=Sum('num')).get('total_num') or 0
            scso.refund_num = refund_num  # 保存退货数量
            scso.save()
            # 过滤订单中一款产品的集合 付款时间是昨天的
    from shopback import paramconfig as pcfg
    # 付款时间是昨天　是退款状态的订单　
    refunds = Refund.objects.filter(modified__gte=start_dt, modified__lte=end_dt,
                                    status__in=(pcfg.REFUND_SUCCESS,  # 退款成功
                                                pcfg.REFUND_CONFIRM_GOODS,  # 买家已经退货
                                                pcfg.REFUND_WAIT_SELLER_AGREE))  # 卖家同意退款
    for refund in refunds:
        mo = MergeOrder.objects.filter(oid=refund.oid)
        if mo.exists():
            products = Product.objects.filter(outer_id=mo[0].outer_id)
            if products.exists() and products[0].sale_time:
                scso, state = SupplyChainStatsOrder.objects.get_or_create(product_id=mo[0].outer_id,
                                                                          outer_sku_id=mo[0].outer_sku_id,
                                                                          shelve_time=products[0].sale_time,
                                                                          sale_time=target_day)
                scso.refund_amount_num = F("refund_amount_num") + 1
                scso.save()
    handler_refund()


from django.db import connection


def get_return_num_by_product_id(outer_id):
    sql = "select sum(num) as return_num from " \
          "shop_trades_mergeorder where status in ('TRADE_CLOSED','TRADE_REFUNDED','TRADE_REFUNDING') and " \
          "sys_status  not in('INVALID','ON_THE_FLY') and outer_id = '{0}' group by outer_id".format(outer_id)
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return raw[0][0] if len(raw) else 0


def get_inferior_num_by_product_id(outer_id):
    sql = "select sum(inferior_quantity) as inferior_num from " \
          "suplychain_flashsale_orderdetail where outer_id='{0}' group by outer_id".format(outer_id)
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return raw[0][0] if len(raw) else 0