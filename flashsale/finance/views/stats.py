# coding=utf-8
import datetime
from django.db import connection, transaction
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
