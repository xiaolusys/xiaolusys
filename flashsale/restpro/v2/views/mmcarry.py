# encoding=utf8
import simplejson
from datetime import datetime, timedelta
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework import permissions

from common.auth import WeAppAuthentication
from flashsale.coupon.models import CouponTransferRecord, TransferCouponDetail
from flashsale.coupon.models.usercoupon import UserCoupon
from flashsale.pay.models.user import Customer, BudgetLog
from flashsale.restpro.v2.serializers.serializers import BudgetLogSerialize
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.daystats.mylib.db import get_cursor, execute_sql
from flashsale.daystats.mylib.util import groupby, process


def process_items(items):
    def get_origin_price(item):
        extras = item['extras']
        extras = simplejson.loads(extras)
        origin_price = extras.get('origin_price')
        item['origin_price'] = origin_price
        return item

    def cal_profit(items):
        res = {
            'id': items[0]['id'],
            'created': items[0]['created'],
            'flow_amount': items[0]['flow_amount'],
            'origin_price': sum([x['origin_price'] for x in items])
        }
        return res

    items = map(get_origin_price, items)
    items = filter(lambda x: x['origin_price'], items)

    items = groupby(items, lambda x: x['id'])
    items = process(items, cal_profit)
    items = [x[1] for x in items]
    return items

class MMCarryViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BudgetLogSerialize

    def index(self, request, *args, **kwargs):
        """
        GET /rest/v2/mmcarry

        小鹿妈妈累计收益(只计算返点和兑换订单利润)
        """
        customer = Customer.getCustomerByUser(user=request.user)
        mama = customer.getXiaolumm()

        if not mama:
            return Response({'code': 1, 'msg': '没有mama'})

        result = []

        sql = """
        SELECT
            bg.id, bg.created, bg.flow_amount, coupon.extras
        FROM
            flashsale_userbudgetlog AS bg
        join flashsale_coupon_transfer_record as ctr on ctr.order_no=bg.uni_key
        join flashsale_transfer_detail as ctd on ctd.transfer_id=ctr.id
        join flashsale_user_coupon as coupon on coupon.id = ctd.coupon_id
        WHERE
            bg.customer_id = "{}"
        AND bg.budget_log_type = 'exchg'
        and bg.status = 0
        and ctr.transfer_type = 8
        and ctd.transfer_type = 8
        """.format(customer.id)
        items = execute_sql(get_cursor(conn='default'), sql)
        items = process_items(items)

        for item in items:
            origin_price = item['origin_price']
            profit = item['flow_amount'] - origin_price
            result.append({'type': '兑换订单', 'amount': profit, 'created': item['created'], 'budget_log_id': item['id']})

        sql = """
        SELECT
            bg.id, bg.created, bg.flow_amount, coupon.extras
        FROM
            flashsale_userbudgetlog AS bg
        join flashsale_coupon_transfer_record as ctr on ctr.id=bg.referal_id
        join flashsale_transfer_detail as ctd on ctd.transfer_id=ctr.id
        join flashsale_user_coupon as coupon on coupon.id = ctd.coupon_id
        WHERE
         	bg.customer_id = "{}"
        and bg.budget_log_type = 'rtexchg'
        """.format(customer.id)
        items = execute_sql(get_cursor(conn='default'), sql)
        items = process_items(items)

        for item in items:
            origin_price = item['origin_price']
            profit = item['flow_amount'] - origin_price
            result.append({'type': '取消兑换订单', 'amount': -profit, 'created': item['created'], 'budget_log_id': item['id']})

        bgs = BudgetLog.objects.filter(budget_log_type=BudgetLog.BG_FANDIAN,
                                       status=BudgetLog.CONFIRMED, customer_id=customer.id)
        for bg in bgs:
            result.append({'type': '返点', 'amount': bg.flow_amount, 'created': bg.created, 'budget_log_id': bg.id})

        result = sorted(result, key=lambda x: x['created'], reverse=True)
        total = sum([x['amount'] for x in result])
        return Response({'detail': result, 'total': total})
