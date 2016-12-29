# coding=utf-8
import datetime
from django.db import connection, transaction
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers

from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from shopback.items.models import Product, ProductSku


def product_category_map():
    return {
        4: '小鹿美美',
        5: '小鹿美美 / 童装',
        6: '小鹿美美 / 箱包',
        8: '小鹿美美 / 女装',
        10: '小鹿美美 / 饰品',
        39: '小鹿美美 / 美食',
        44: '小鹿美美 / 美妆',
        49: '小鹿美美 / 家居',
        52: '小鹿美美 / 母婴',
    }


def date_handler(request):
    date_from = request.GET.get('date_from') or None
    date_to = request.GET.get('date_to') or None
    t_to_1 = datetime.datetime.strptime(date_to, '%Y-%m-%d')  # 将字符串转化成时间
    t_to = t_to_1 + datetime.timedelta(days=1)  # 包含结束当天
    date_from_time = date_from
    date_to_time = t_to.strftime('%Y-%m-%d')
    return date_from, date_to, date_from_time, date_to_time


def choice_display(choice, value):
    for i in choice:
        if i[0] == value:
            return i[1]
    return None


class FinanceChannelPayApiView(APIView):
    """
    ###　特卖商城交易渠道
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    channel_pay_sql = "SELECT t.channel, COUNT(o.id) , SUM(o.payment), SUM(o.total_fee) FROM" \
                      " flashsale_trade AS t LEFT JOIN flashsale_order AS o ON t.id = o.sale_trade_id WHERE" \
                      " t.pay_time BETWEEN '{0}' AND '{1}' AND t.status" \
                      " IN (2 , 3, 4, 5, 6) and o.oid regexp '[a-zA-Z0-9]' GROUP BY t.channel;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.channel_pay_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        total_count = 0
        total_payment = 0
        total_fees = 0
        for i in raw:
            channel_display = choice_display(SaleTrade.CHANNEL_CHOICES, i[0])
            results.append({'channel': i[0],
                            'count': i[1],
                            'sum_payment': i[2],
                            'total_fee': i[3],
                            'channel_display': channel_display})
            total_count += i[1]
            total_payment += i[2]
            total_fees += i[3]
        cursor.close()

        return Response({'code': 0,
                         'info': 'success',
                         'desc': '订单(含押金含退款)支付渠道交易金额',
                         'aggregate_data': {
                             'total_count': total_count,
                             'total_payment': total_payment,
                             'total_fees': total_fees,
                         },
                         'sql': sql,
                         'items_data': results})


class FinanceRefundApiView(APIView):
    """
    ### 退款单数
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    refund_sql = "SELECT refund_status , COUNT(*) , SUM(payment) FROM flashsale_order " \
                 "WHERE pay_time BETWEEN '{0}' AND '{1}' AND" \
                 " refund_status > 0 AND status IN (2 , 3, 4, 5, 6) GROUP BY refund_status;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.refund_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        total_count = 0
        total_payment = 0
        for i in raw:
            refund_status_display = choice_display(SaleRefund.REFUND_STATUS, i[0])
            results.append({'refund_status': i[0],
                            'count': i[1],
                            'sum_payment': i[2],
                            'refund_status_display': refund_status_display})
            total_count += i[1]
            total_payment += i[2]
        cursor.close()
        return Response({'code': 0,
                         'info': 'success',
                         'desc': '退款各状态笔数及金额',
                         'aggregate_data': {
                             'total_count': total_count,
                             'total_payment': total_payment
                         },
                         'sql': sql,
                         'items_data': results})


class FinanceReturnGoodApiView(APIView):
    """
    ### 退款单数
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    return_good_sql = "SELECT r.good_status, COUNT(r.id), SUM(r.refund_fee) FROM flashsale_refund " \
                      "AS r LEFT JOIN flashsale_order AS o ON r.order_id = o.id " \
                      "WHERE o.pay_time BETWEEN '{0}' AND '{1}' GROUP BY r.good_status;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.return_good_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        total_count = 0
        total_payment = 0
        for i in raw:
            return_good_status_display = choice_display(SaleRefund.GOOD_STATUS_CHOICES, i[0])
            results.append({'return_goods_status': i[0], 'count': i[1], 'sum_payment': i[2],
                            'return_good_status_display': return_good_status_display})
            total_count += i[1]
            total_payment += i[2]
        cursor.close()
        return Response({'code': 0,
                         'info': 'success',
                         'desc': '退货状态金额笔数',
                         'aggregate_data': {
                             'total_count': total_count,
                             'total_payment': total_payment
                         },
                         'sql': sql,
                         'items_data': results})


class FinanceDepositApiView(APIView):
    """
    ### 代理押金统计
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    deposit_sql = "SELECT sku_id, COUNT(*), SUM(payment) FROM flashsale_order " \
                  "WHERE status = 5 AND pay_time BETWEEN '{0}' AND '{1}' " \
                  "AND refund_status = 0 AND item_id = 2731 GROUP BY sku_id;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.deposit_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        deposit_display_map = {
            '11873': '188元',
            '221408': '99元',
            '221409': '1元'
        }
        total_count = 0
        total_payment = 0
        for i in raw:
            try:
                deposit_display = deposit_display_map[i[0]]
            except KeyError:
                deposit_display = '未知'
            results.append({'sku_id': i[0], 'count': i[1], 'sum_payment': i[2],
                            'deposit_display': deposit_display})
            total_count += i[1]
            total_payment += i[2]
        cursor.close()
        return Response({'code': 0,
                         'info': 'success',
                         'sql': sql,
                         'desc': '押金订单笔数金额',
                         'aggregate_data': {
                             'total_count': total_count,
                             'total_payment': total_payment
                         },
                         'items_data': results})


class FinanceStockApiView(APIView):
    """
    ### 实时库存统计: 类别id 　数量　金额　
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    stock_sql = "SELECT c.parent_cid, SUM(s.history_quantity + s.adjust_quantity + s.inbound_quantity +" \
                " s.return_quantity - s.post_num - s.rg_quantity), " \
                "SUM(p.cost * (s.history_quantity + s.adjust_quantity + s.inbound_quantity + " \
                "s.return_quantity - s.post_num - s.rg_quantity)) FROM " \
                "shop_items_product AS p LEFT JOIN shop_items_productskustats AS s ON p.id = s.product_id " \
                " LEFT JOIN shop_categorys_productcategory AS c ON p.category_id = c.cid " \
                "WHERE p.sale_time BETWEEN '{0}' AND '{1}' AND p.status = 'normal' GROUP BY c.parent_cid;"

    category_map = product_category_map()

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.stock_sql.format(date_from, date_to)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        total_count = 0
        total_payment = 0
        for i in raw:
            try:
                category_display = self.category_map[i[0]]
            except KeyError:
                category_display = '未知'
            results.append({
                'category_id': i[0],
                'sum_num': i[1],
                'sum_cost': i[2],
                'category_display': category_display
            })
            total_count += i[1]
            total_payment += i[2]
        cursor.close()
        return Response({'code': 0,
                         'info': 'success',
                         'desc': '库存成本分类订单金额笔数',
                         'aggregate_data': {
                             'total_count': total_count,
                             'total_payment': total_payment
                         },
                         'sql': sql,
                         'items_data': results})


class FinanceCostApiView(APIView):
    """
    ### 成本统计(不含押金)　交易额　交易成本　利润率　交易件数　日期
    - method: get
        * args:
            1. `date_from`: 开始日期
            2. `date_to`: 结束日期
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    cost_sql = "SELECT SUM(o.payment), SUM(sku.cost * o.num), " \
               "SUM(o.payment)/SUM(sku.cost * o.num) , SUM(o.num), " \
               "DATE(o.pay_time) AS cost_date " \
               "FROM flashsale_order AS o " \
               "LEFT JOIN shop_items_product AS p ON o.item_id = p.id " \
               "LEFT JOIN shop_items_productsku AS sku ON sku.id = o.sku_id " \
               "WHERE o.pay_time BETWEEN '{0}' " \
               "AND '{1}' AND o.status >= 2 AND o.status <= 5 AND o.refund_status=0 " \
               "AND o.sku_id != '11873' AND o.sku_id!='221408' AND o.sku_id!='221409'  " \
               "GROUP BY cost_date ORDER BY cost_date;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.cost_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        items = []
        total_payment = 0
        total_cost = 0
        total_count = 0
        for i in raw:
            total_payment += i[0]
            total_cost += i[1]
            total_count += i[3]
            items.append({
                'sum_payment': i[0],
                'sum_cost': i[1],
                'profit': i[2],
                'sum_num': i[3],
                'date': i[4],
            })
        cursor.close()
        return Response({
            'code': 0,
            'info': 'success',
            'desc': u'交易成本统计',
            'aggregate_data': {
                'total_payment': total_payment,
                'total_cost': total_cost,
                'total_count': total_count,
                'total_Profit': round(total_cost / total_payment, 5)
            },
            'sql': sql,
            'items_data': items
        })


class MamaOrderCarryStatApiView(APIView):
    """
    小鹿妈妈订单数占比: 状态在 预计 or 已经确定 订单类型 包含商城直接订单 和 app直接订单记录类型 不包含 下属订单类型
    小鹿妈妈带来的单量 carry_num:提成金额　　order_value：订单金额
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    sql = "SELECT COUNT(*), SUM(carry_num / 100), SUM(order_value / 100), date_field FROM " \
          "flashsale_xlmm_order_carry WHERE date_field >= '{0}' AND date_field <= '{1}' " \
          "AND status in( 1, 2) AND mama_id > 140 and carry_type<3 GROUP BY date_field;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.sql.format(date_from, date_to)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        items_data = []
        total_count = 0
        total_carry_num = 0
        total_order_value = 0
        for i in raw:
            total_count += i[0]
            total_carry_num += i[1]
            total_order_value += i[2]
            items_data.append({
                'count': i[0],
                'sum_carry_num': i[1],
                'sum_order_value': i[2],
                'date': i[3]
            })
        return Response(
            {
                'code': 0,
                'info': 'success',
                'desc': u'特卖商城小鹿妈妈订单占比信息',
                'aggregate_data': {
                    'total_count': total_count,
                    'total_carry_num': total_carry_num,
                    'total_order_value': total_order_value
                },
                'sql': sql,
                'items_data': items_data
            }
        )


class BoutiqueCouponStatApiView(APIView):
    """1. 精品券销售情况统计  : 指定日期的 每天 销售 张数 券额  状态 和 总全额 总张数 不同状态总券额 总张数
       2. 精品商品销售情况统计: 指定日期内的 销售总额 总件数 退精品订单总额
       3. 注意: (1) 精品券有赠送的情况(没有精品券订单) . (2) 这里的精品商品订单仅仅包含用券购买的订单(排除直接付款 但包含 兑换订单)
    """
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    sql = "SELECT COUNT(id), SUM(value), status, DATE(created) AS date_field FROM flashsale_user_coupon " \
          "WHERE created >= '{0}' AND created <= '{1}' AND coupon_type = 8 AND status IN (0 , 1, 2) " \
          "GROUP BY date_field , status;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        items_data = []
        total_status_0_count = 0
        total_status_0_value = 0
        total_status_1_count = 0
        total_status_1_value = 0
        total_status_2_count = 0
        total_status_2_value = 0
        total_count = 0
        total_value = 0
        for i in raw:
            total_count += i[0]
            total_value += i[1]
            status = i[2]
            if status == 0:
                total_status_0_count += i[0]
                total_status_0_value += i[1]
            if status == 1:
                total_status_1_count += i[0]
                total_status_1_value += i[1]
            if status == 2:
                total_status_2_count += i[0]
                total_status_2_value += i[1]
            items_data.append({
                'count': i[0],
                'sum_value': i[1],
                'status': status,
                'date': i[3]
            })
        # 计算精品券订单金额和件数 # 交易成功状态 电子商品订单
        from flashsale.pay.models import SaleOrder

        orders_sum = SaleOrder.objects.filter(pay_time__gte=date_from_time,
                                              pay_time__lte=date_to_time,
                                              sale_trade__order_type=4,
                                              status=SaleOrder.TRADE_FINISHED).aggregate(s_num=Sum('num'),
                                                                                         s_payment=Sum('payment'))
        orders_s_num = orders_sum.get('s_num') or 0  # 件数
        orders_s_payment = orders_sum.get('s_payment') or 0  # 交易金额

        # 精品汇商品订单
        boutique_orders = SaleOrder.objects.filter(Q(payment=0) | Q(extras__contains='"exchange": true'),
                                                   pay_time__gte=date_from_time,
                                                   pay_time__lte=date_to_time,
                                                   sale_trade__order_type=0,
                                                   sale_trade__is_boutique=1,
                                                   status__gte=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                                   status__lte=SaleOrder.TRADE_CLOSED)

        refund_boutique_orders = boutique_orders.filter(refund_status__gt=0)
        sum_boutique = boutique_orders.aggregate(bs_num=Sum('num'), bs_payment=Sum('payment'))
        total_boutique_num = sum_boutique.get('bs_num') or 0
        total_boutique_payment = sum_boutique.get('bs_payment') or 0
        total_refund_boutique_fee = refund_boutique_orders.aggregate(brf=Sum('refund_fee')).get('brf') or 0
        return Response(
            {
                'code': 0,
                'info': 'success',
                'desc': u'<h3>精品券/精品商品订单统计:</h3> <p>%s</p>' % self.__doc__.replace('\n', '</br>'),
                'aggregate_data': {
                    'total_count': total_count,
                    'total_value': total_value,
                    'total_status_0_count': total_status_0_count,
                    'total_status_0_value': total_status_0_value,
                    'total_status_1_count': total_status_1_count,
                    'total_status_1_value': total_status_1_value,
                    'total_status_2_count': total_status_2_count,
                    'total_status_2_value': total_status_2_value,
                    'orders_s_num': orders_s_num,
                    'orders_s_payment': orders_s_payment,

                    'total_boutique_num': total_boutique_num,
                    'total_boutique_payment': total_boutique_payment,
                    'total_refund_boutique_fee': total_refund_boutique_fee,
                },
                'sql': sql + '不包含订单统计sql',
                'items_data': items_data
            }
        )
