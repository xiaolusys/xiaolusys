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
    channel_pay_sql = "SELECT t.channel, COUNT(o.id) , SUM(o.payment) FROM" \
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
        for i in raw:
            channel_display = choice_display(SaleTrade.CHANNEL_CHOICES, i[0])
            results.append({'channel': i[0], 'count': i[1], 'sum_payment': i[2], 'channel_display': channel_display})
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


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
        for i in raw:
            refund_status_display = choice_display(SaleRefund.REFUND_STATUS, i[0])
            results.append({'refund_status': i[0], 'count': i[1], 'sum_payment': i[2],
                            'refund_status_display': refund_status_display})
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


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
        for i in raw:
            return_good_status_display = choice_display(SaleRefund.GOOD_STATUS_CHOICES, i[0])
            results.append({'return_goods_status': i[0], 'count': i[1], 'sum_payment': i[2],
                            'return_good_status_display': return_good_status_display})
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


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
        for i in raw:
            try:
                deposit_display = deposit_display_map[i[0]]
            except KeyError:
                deposit_display = '未知'
            results.append({'sku_id': i[0], 'count': i[1], 'sum_payment': i[2],
                            'deposit_display': deposit_display})
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


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
               "DATE(o.pay_time) AS cost_date FROM flashsale_order AS o LEFT JOIN shop_items_productsku" \
               " AS sku ON sku.id = o.sku_id WHERE o.pay_time BETWEEN '{0}' " \
               "AND '{1}' AND o.status >= 2 AND o.status <= 5 AND o.refund_status=0 " \
               "AND o.sku_id != '11873' AND o.sku_id!='221408' AND o.sku_id!='221409'  GROUP BY cost_date;"

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.cost_sql.format(date_from_time, date_to_time)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
        for i in raw:
            results.append({
                'sum_payment': i[0],
                'sum_cost': i[1],
                'profit': i[2],
                'sum_num': i[3],
                'date': i[4]
            })
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


def product_category_map():
    return {1: '优尼世界',
            3: '小鹿美美-健康',
            4: '小鹿美美',
            5: '小鹿美美-童装',
            6: '小鹿美美-箱包',
            8: '小鹿美美-女装',
            9: '小鹿美美-亲子装',
            10: '小鹿美美-配饰',
            11: '小鹿美美-秒杀',
            12: '小鹿美美-童装-外套',
            13: '小鹿美美-童装-上装',
            14: '小鹿美美-童装-连衣裙',
            15: '小鹿美美-童装-套装',
            16: '小鹿美美-童装-哈衣',
            17: '小鹿美美-童装-下装',
            18: '小鹿美美-女装-外套',
            19: '小鹿美美-女装-连衣裙',
            20: '小鹿美美-女装-上装',
            21: '小鹿美美-女装-下装',
            22: '小鹿美美-女装-套装',
            23: '小鹿美美-童装-配饰',
            24: '小鹿美美-女装-配饰',
            25: '小鹿美美-童装-亲子装',
            26: '小鹿美美-童装-内衣',
            27: '小鹿美美-女装-内衣',
            29: '小鹿美美-健康-果粒茶',
            30: '小鹿美美-健康-固体茶',
            31: '小鹿美美-健康-袋泡茶',
            32: '小鹿美美-健康-花草茶',
            34: '小鹿美美-箱包-手提包',
            35: '小鹿美美-箱包-行李箱',
            36: '小鹿美美-箱包-钱包',
            37: '小鹿美美-箱包-手拿包',
            38: '小鹿美美-箱包-肩背包',
            39: '小鹿美美-食品',
            40: '小鹿美美-食品-保健滋补',
            41: '小鹿美美-食品-南北干货',
            42: '小鹿美美-食品-养生茶饮',
            43: '小鹿美美-食品-休闲零食',
            44: '小鹿美美-美妆',
            45: '小鹿美美-美妆-护肤',
            46: '小鹿美美-美妆-彩妆',
            47: '小鹿美美-美妆-洗护',
            48: '小鹿美美-美妆-面膜',
            49: '小鹿美美-家居',
            50: '小鹿美美-家居-保温杯',
            51: '小鹿美美-美妆-香水',
            52: '小鹿美美-母婴',
            53: '小鹿美美-母婴-孕妈专区',
            54: '小鹿美美-母婴-婴童家居',
            55: '小鹿美美-母婴-益智玩具',
            56: '小鹿美美-母婴-书包文具',
            57: '小鹿美美-美食-饼干糕点',
            58: '小鹿美美-童装-演出服',
            59: '小鹿美美-童装-连体衣',
            60: '小鹿美美-童装-裤装',
            61: '小鹿美美-童装-内衣家居',
            62: '小鹿美美-童装-裙装',
            63: '小鹿美美-女装-裤装',
            64: '小鹿美美-女装-裙装',
            65: '小鹿美美-家居-电器',
            66: '小鹿美美-母婴-童鞋',
            67: '小鹿美美-家居-家纺',
            68: '小鹿美美-家居-厨具',
            69: '小鹿美美-家居-收纳清洁',
            70: '小鹿美美-家居-拖鞋',
            71: '小鹿美美-家居-拖鞋',
            72: '小鹿美美-母婴-绘本',
            73: '小鹿美美-家居-雨伞'}


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
    stock_sql = "SELECT p.category_id, SUM(s.history_quantity + s.adjust_quantity + s.inbound_quantity +" \
                " s.return_quantity - s.post_num - s.rg_quantity), " \
                "SUM(p.cost * (s.history_quantity + s.adjust_quantity + s.inbound_quantity + " \
                "s.return_quantity - s.post_num - s.rg_quantity)) FROM " \
                "shop_items_product AS p LEFT JOIN shop_items_productskustats AS s ON p.id = s.product_id " \
                "WHERE p.sale_time BETWEEN '{0}' AND '{1}' AND p.status = 'normal' GROUP BY p.category_id;"

    category_map = product_category_map()

    def get(self, request):
        date_from, date_to, date_from_time, date_to_time = date_handler(request)
        sql = self.stock_sql.format(date_from, date_to)
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        results = []
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
        cursor.close()
        return Response({'code': 0, 'info': 'success', 'sql': sql,
                         'results': results})


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
        results = []
        total_count = 0
        total_carry_num = 0
        total_order_value = 0
        for i in raw:
            total_count += i[0]
            total_carry_num += i[1]
            total_order_value += i[2]
            results.append({
                'count': i[0],
                'sum_carry_num': i[1],
                'sum_order_value': i[2]
            })
        return Response({
            'code': 0,
            'info': 'success',
            'desc': u'特卖商城小鹿妈妈订单占比信息',
            'aggregate': {
                'total_count': total_count,
                'total_carry_num': total_carry_num,
                'total_order_value': total_order_value
            },
            'sql': sql,
            'results': results
        })
