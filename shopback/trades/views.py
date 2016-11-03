# coding: utf-8
import cStringIO as StringIO
import datetime
import json
import logging
import re
import time

from django.core.urlresolvers import reverse
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.views.generic import FormView

from shopapp.taobao import apis
from common.utils import (parse_date, CSVUnicodeWriter, parse_datetime,
                          format_date, format_datetime)
from shopback import paramconfig as pcfg
from shopback.base import log_action, ADDITION, CHANGE
from shopback.base.new_renders import new_BaseJSONRenderer
from shopback.items.models import Product, ProductSku, ProductDaySale
from shopback.logistics import getLogisticTrace
from shopback.logistics.models import LogisticsCompany

from shopback.items.models import Product, ProductSku, ProductDaySale
from core.options import log_action, ADDITION, CHANGE

from flashsale.pay.models import SaleOrder      #dh
from shopback.trades.models import PackageOrder, PackageSkuItem         #dh

from shopapp.memorule import ruleMatchSplit
from shopback.refunds.models import REFUND_STATUS, Refund
from shopback.signals import rule_signal, change_addr_signal
from shopback.trades.models_dirty import DirtyMergeOrder
from shopback.trades.models import (MergeTrade, MergeOrder, PackageOrder,PackageSkuItem,
                                    ReplayPostTrade, GIFT_TYPE,
                                    SYS_TRADE_STATUS, TAOBAO_TRADE_STATUS,
                                    SHIPPING_TYPE_CHOICE, TAOBAO_ORDER_STATUS)
from shopback.trades.forms import ExchangeTradeForm
from shopback.users.models import User

from rest_framework import authentication, filters, generics, permissions, status, viewsets
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from renderers import *
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
from . import forms, serializers
logger = logging.getLogger('django.request')


############################### 缺货订单商品列表 #################################
class OutStockOrderProductView(APIView):
    """ docstring for class OutStockOrderProductView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (StatisticOutStockRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        outer_stock_orders = MergeOrder.objects.filter(
            merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS,
            out_stock=True)
        trade_items = {}

        for order in outer_stock_orders:
            outer_id = order.outer_id or str(order.num_iid)
            outer_sku_id = order.outer_sku_id or str(order.sku_id)

            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order.num
                skus = trade_items[outer_id]['skus']
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order.num
                else:
                    prod_sku = None
                    try:
                        prod_sku = ProductSku.objects.get(
                            outer_id=outer_sku_id,
                            product__outer_id=outer_id)
                    except:
                        prod_sku = None
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    skus[outer_sku_id] = {'sku_name': prod_sku_name,
                                          'num': order.num,
                                          'quality': prod_sku.quantity
                                          if prod_sku else 0,
                                          'wait_post_num':
                                              prod_sku.wait_post_num if prod_sku
                                              else 0}
            else:
                prod = None
                try:
                    prod = Product.objects.get(outer_id=outer_id)
                except:
                    prod = None

                prod_sku = None
                try:
                    prod_sku = ProductSku.objects.get(
                        outer_id=outer_sku_id,
                        product__outer_id=outer_id)
                except:
                    prod_sku = None
                prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name

                trade_items[outer_id] = {
                    'num': order.num,
                    'title': prod.name if prod else order.title,
                    'collect_num': prod.collect_num if prod else 0,
                    'wait_post_num': prod.wait_post_num if prod else 0,
                    'skus': {outer_sku_id: {
                        'sku_name': prod_sku_name,
                        'num': order.num,
                        'quality': prod_sku.quantity if prod_sku else 0,
                        'wait_post_num': prod_sku.wait_post_num
                        if prod_sku else 0,
                    }}
                }

        trade_list = sorted(trade_items.items(),
                            key=lambda d: d[1]['num'],
                            reverse=True)
        for trade in trade_list:
            skus = trade[1]['skus']
            trade[1]['skus'] = sorted(skus.items(),
                                      key=lambda d: d[1]['num'],
                                      reverse=True)

        return Response({"object": {'trade_items': trade_list,}})


class StatisticMergeOrderView(APIView):
    """ docstring for class StatisticsMergeOrderView """
    # serializer_class = serializers. ItemListTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (StatisticMergeOrderRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def parseStartDt(self, start_dt):

        if not start_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

        if len(start_dt) > 10:
            return parse_datetime(start_dt)

        return parse_date(start_dt)

    def parseEndDt(self, end_dt):

        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)

        if len(end_dt) > 10:
            return parse_datetime(end_dt)

        return parse_date(end_dt)

    def getSourceOrders(self,
                        shop_id=None,
                        is_sale=None,
                        sc_by='created',
                        start_dt=None,
                        end_dt=None,
                        wait_send='0',
                        p_outer_id='',
                        empty_code=False):

        order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
            .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
            .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
        if shop_id:
            order_qs = order_qs.filter(merge_trade__user=shop_id)

        if sc_by == 'pay':
            order_qs = order_qs.filter(pay_time__gte=start_dt,
                                       pay_time__lte=end_dt)
        elif sc_by == 'weight':
            order_qs = order_qs.filter(merge_trade__weight_time__gte=start_dt,
                                       merge_trade__weight_time__lte=end_dt)
        else:
            order_qs = order_qs.filter(created__gte=start_dt,
                                       created__lte=end_dt)

        if wait_send == '1':
            order_qs = order_qs.filter(
                merge_trade__sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
        elif wait_send == '2':
            order_qs = order_qs.filter(
                merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS,
                merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS)
        else:
            order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
                .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
                .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)

        if empty_code:
            order_qs = order_qs.filter(outer_id='')
            return order_qs

        if is_sale:
            order_qs = order_qs.extra(where=["CHAR_LENGTH(outer_id)>=9"]) \
                .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8"))

        if p_outer_id:
            order_qs = order_qs.filter(outer_id__startswith=p_outer_id)

        return order_qs

    def getSourceTrades(self, order_qs):

        trade_ids = [t[0] for t in order_qs.values_list('merge_trade__id')]

        return set(trade_ids)
        # return MergeTrade.objects.filter(id__in=trade_ids)

    def getEffectOrdersId(self, order_qs):

        return [o[0] for o in order_qs.values_list('oid') if len(o) > 0]

    def getProductByOuterId(self, outer_id):

        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None

    def getProductSkuByOuterId(self, outer_id, outer_sku_id):

        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except:
            return None

    def getProductAndSku(self, outer_id, outer_sku_id):

        self.prod_map = {}
        outer_key = '-'.join((outer_id, outer_sku_id))
        if self.prod_map.has_key(outer_key):
            return self.prod_map.get(outer_key)

        prod = self.getProductByOuterId(outer_id)
        prod_sku = self.getProductSkuByOuterId(outer_id, outer_sku_id)
        self.prod_map[outer_key] = (prod, prod_sku)
        return (prod, prod_sku)

    def getTradeSortedItems(self, order_qs, is_sale=False):

        trade_items = {}
        for order in order_qs:

            outer_id = order.outer_id.strip() or str(order.num_iid)
            outer_sku_id = order.outer_sku_id.strip() or str(order.sku_id)
            payment = float(order.payment or 0)
            order_num = order.num or 0
            prod, prod_sku = self.getProductAndSku(outer_id, outer_sku_id)

            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order_num
                skus = trade_items[outer_id]['skus']

                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order_num
                    skus[outer_sku_id]['cost'] += skus[outer_sku_id][
                                                      'std_purchase_price'] * order_num
                    skus[outer_sku_id]['sales'] += payment
                    # 累加商品成本跟销售额
                    trade_items[outer_id]['cost'] += skus[outer_sku_id][
                                                         'std_purchase_price'] * order_num
                    trade_items[outer_id]['sales'] += payment
                else:
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    purchase_price = float(prod_sku.cost) if prod_sku else 0
                    # 累加商品成本跟销售额
                    trade_items[outer_id]['cost'] += purchase_price * order_num
                    trade_items[outer_id]['sales'] += payment

                    skus[outer_sku_id] = {
                        'sku_name': prod_sku_name,
                        'num': order_num,
                        'cost': purchase_price * order_num,
                        'sales': payment,
                        'std_purchase_price': purchase_price
                    }
            else:
                prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                purchase_price = float(
                    prod_sku.cost) if prod_sku else payment / order_num
                trade_items[outer_id] = {
                    'product_id': prod and prod.id or None,
                    'num': order_num,
                    'title': prod.name if prod else order.title,
                    'cost': purchase_price * order_num,
                    'pic_path': prod and prod.PIC_PATH or '',
                    'sales': payment,
                    'sale_charger': prod and prod.sale_charger or '',
                    'storage_charger': prod and prod.storage_charger or '',
                    'sales': payment,
                    'skus': {outer_sku_id: {
                        'sku_name': prod_sku_name,
                        'num': order_num,
                        'cost': purchase_price * order_num,
                        'sales': payment,
                        'std_purchase_price': purchase_price
                    }}
                }

        if is_sale:

            def sort_items(x, y):
                if x[0][:-1] == y[0][:-1]:
                    return -cmp(x[1], y[1])
                return cmp(x[0], y[0])

            order_items = sorted(trade_items.items(),
                                 key=lambda d: (d[0], d[1]['num']),
                                 cmp=sort_items)
        else:
            order_items = sorted(trade_items.items(),
                                 key=lambda d: d[1]['num'],
                                 reverse=True)

        total_cost = 0
        total_sales = 0
        total_num = 0
        for trade in order_items:
            total_cost += trade[1]['cost']
            total_sales += trade[1]['sales']
            total_num += trade[1]['num']
            trade[1]['skus'] = sorted(trade[1]['skus'].items(),
                                      key=lambda d: d[0])

        order_items.append(total_sales)
        order_items.append(total_cost)
        order_items.append(total_num)

        return order_items

    def getTotalRefundFee(self, order_qs):

        effect_oids = self.getEffectOrdersId(order_qs)

        return Refund.objects.filter(oid__in=effect_oids, status__in=(
            pcfg.REFUND_WAIT_SELLER_AGREE, pcfg.REFUND_CONFIRM_GOODS, pcfg.REFUND_SUCCESS)) \
                   .aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee') or 0

    def responseCSVFile(self, request, order_items):

        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1
        pcsv = []
        pcsv.append(("商品编码", "商品名称", "总数量", "成本", "销售额", "规格编码", "商品规格	", "数量",
                     "成本", "销售额"))

        for order in order_items:
            first_loop = True
            for item in order:
                pcsv.append((first_loop and order[0] or '',
                             first_loop and order[1]['title'] or '',
                             first_loop and str(order[1]['num']) or '',
                             first_loop and str(order[1]['cost']) or '',
                             first_loop and str(order[1]['sales']) or '',
                             item[0],
                             item[1]['title'],
                             str(item[1]['num']),
                             str(item[1]['cost']),
                             str(item[1]['sales']),))
                first_loop = False

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile,
                                  encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(),
                                content_type='application/octet-stream')
        tmpfile.close()

        dt = datetime.datetime.now()

        response[
            'Content-Disposition'] = 'attachment;filename=wx-sale-%s.csv' % dt.strftime(
            "%Y%m%d%H")

        return response

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        start_dt = content.get('df', '').strip()
        end_dt = content.get('dt', '').strip()
        shop_id = content.get('shop_id')
        p_outer_id = content.get('outer_id', '')
        sc_by = content.get('sc_by', 'pay')
        wait_send = content.get('wait_send', '0')
        is_sale = content.get('is_sale', '')
        action = content.get('action', '')

        start_dt = self.parseStartDt(start_dt)
        end_dt = self.parseEndDt(end_dt)

        order_qs = self.getSourceOrders(shop_id=shop_id,
                                        sc_by=sc_by,
                                        wait_send=wait_send,
                                        p_outer_id=p_outer_id,
                                        start_dt=start_dt,
                                        end_dt=end_dt,
                                        is_sale=is_sale)

        empty_order_qs = self.getSourceOrders(shop_id=shop_id,
                                              sc_by=sc_by,
                                              wait_send=wait_send,
                                              p_outer_id=p_outer_id,
                                              start_dt=start_dt,
                                              end_dt=end_dt,
                                              empty_code=True)

        trade_qs = self.getSourceTrades(order_qs)

        buyer_nums = len(trade_qs)
        trade_nums = len(trade_qs)
        total_post_fee = 0.00

        refund_fees = self.getTotalRefundFee(order_qs)
        empty_order_count = empty_order_qs.count()
        trade_list = self.getTradeSortedItems(order_qs, is_sale=is_sale)
        total_num = trade_list.pop()
        total_cost = trade_list.pop()
        total_sales = trade_list.pop()

        if action == "download":
            return self.responseCSVFile(request, trade_list)

        # shopers = User.objects.filter(status=User.NORMAL)
        shopers = serializers.UserSerializer(
            User.objects.filter(status=User.NORMAL),
            many=True).data

        return Response(
            {"object":
                 {'df': format_datetime(start_dt),
                  'dt': format_datetime(end_dt),
                  'sc_by': sc_by,
                  'is_sale': is_sale,
                  'outer_id': p_outer_id,
                  'wait_send': wait_send,
                  'shops': shopers,
                  'trade_items': trade_list,
                  'empty_order_count': empty_order_count,
                  'shop_id': shop_id and int(shop_id) or '',
                  'total_cost': total_cost and round(total_cost, 2) or 0,
                  'total_sales': total_sales and round(total_sales, 2) or 0,
                  'total_num': total_num,
                  'refund_fees': refund_fees and round(refund_fees, 2) or 0,
                  'buyer_nums': buyer_nums,
                  'trade_nums': trade_nums,
                  'post_fees': total_post_fee}})

    post = get


from shopback.trades.tasks import task_Gen_Product_Statistic


class StatisticMergeOrderAsyncView(APIView):
    """ docstring for class StatisticsMergeOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (StatisticMergeOrderAsyncRender, new_BaseJSONRenderer)

    def parseStartDt(self, start_dt):
        if not start_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        if len(start_dt) > 10:
            return parse_datetime(start_dt)
        return parse_date(start_dt)

    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return parse_datetime(end_dt)
        return parse_date(end_dt)

    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        start_dt = content.get('df', '').strip()
        end_dt = content.get('dt', '').strip()
        shop_id = content.get('shop_id')
        p_outer_id = content.get('outer_id', '')
        sc_by = content.get('sc_by', 'pay')
        wait_send = content.get('wait_send', '0')
        is_sale = content.get('is_sale', '')
        action = content.get('action', '')

        start_dt = self.parseStartDt(start_dt)
        end_dt = self.parseEndDt(end_dt)
        shopers = serializers.UserSerializer(
            User.objects.filter(status=User.NORMAL),
            many=True).data
        task_id = task_Gen_Product_Statistic.delay(
            shop_id, sc_by, wait_send, p_outer_id, start_dt, end_dt, is_sale)
        return Response({"task_id": task_id,
                         'df': format_datetime(start_dt),
                         'dt': format_datetime(end_dt),
                         'sc_by': sc_by,
                         'is_sale': is_sale,
                         'outer_id': p_outer_id,
                         'wait_send': wait_send,
                         'shops': shopers,
                         'shop_id': shop_id and int(shop_id) or ''})


from django.forms.models import model_to_dict
from shopback.trades.service import TradeService
from flashsale.signals import signal_kefu_operate_record
from flashsale.kefu.models import KefuPerformance


class CheckOrderView(APIView):
    # serializer_class = serializers. ItemListTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)  #
    renderer_classes = (CheckOrderRenderer, new_BaseJSONRenderer,
                        BrowsableAPIRenderer)

    def get(self, request, id, *args):
        # print "进入get"
        try:
            trade = MergeTrade.objects.get(id=id)
            # print trade.inuse_orders
        except MergeTrade.DoesNotExist:
            return Response('该订单不存在'.decode('utf8'))

        # rule_signal.send(sender='payment_rule',trade_id=trade.id)
        # logistics = LogisticsCompany.objects.filter(status=True)
        logistics = serializers.LogisticsCompanySerializer(
            LogisticsCompany.objects.filter(status=True),
            many=True).data
        order_nums = trade.inuse_orders.aggregate(
            total_num=Sum('num')).get('total_num')
        trade_dict = model_to_dict(trade)
        trade_dict.update(
            {'id': trade.id,
             'seller_nick': trade.user.nick,
             # 'used_orders':trade.inuse_orders,   2015-7-25
             'used_orders': serializers.MergeOrderSerializer(trade.inuse_orders,
                                                             many=True).data,
             'total_num': order_nums,
             'logistics_company': serializers.LogisticsCompanySerializer(
                 trade.logistics_company).data,
             'out_of_logistic': trade.has_reason_code(pcfg.LOGISTIC_ERROR_CODE),
             'has_rule_match': (trade.has_rule_match and trade.has_reason_code(
                 pcfg.RULE_MATCH_CODE)),
             'is_product_defect': (trade.has_rule_match and
                                   trade.has_reason_code(
                                       pcfg.TRADE_DEFECT_CODE)),
             'is_ware_match': trade.ware_by != trade.get_trade_assign_ware(),
             'need_manual_merge': trade.has_reason_code(
                 pcfg.MULTIPLE_ORDERS_CODE),
             'shippings': dict(SHIPPING_TYPE_CHOICE),
             'ware_list': WARE_CHOICES})
        return Response({"object": {'trade': trade_dict,
                                    'logistics': logistics}})
        # 'shippings33':dict(SHIPPING_TYPE_CHOICE)  }

    def post(self, request, id, *args, **kwargs):
        user_id = request.user.id
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return Response(u'该订单不存在')
        content = request.REQUEST
        priority = content.get('priority')
        logistic_code = content.get('logistic_code')
        shipping_type = content.get('shipping_type')
        action_code = content.get('action')
        ware_by = int(content.get('ware_by', '0'))
        logistics_company = None

        if logistic_code:
            logistics_company = LogisticsCompany.objects.get(code=logistic_code)
        elif shipping_type != pcfg.EXTRACT_SHIPPING_TYPE:
            # 如果没有选择物流也非自提订单，则提示
            return Response(u'请选择物流公司')

        is_logistic_change = trade.logistics_company != logistics_company
        trade.logistics_company = logistics_company
        trade.priority = priority
        trade.shipping_type = shipping_type
        trade.ware_by = ware_by
        trade.save()

        if action_code == 'check':
            check_msg = []
            if trade.has_refund:
                check_msg.append(u"有待退款")
            if trade.has_out_stock:
                check_msg.append(u"有缺货")
            if (trade.has_rule_match or
                    MergeTrade.objects.isTradeDefect(trade)):
                check_msg.append(u"订单商品编码与库存商品编码不一致")
            if trade.is_force_wlb:
                check_msg.append(u"订单由物流宝发货")
            if trade.ware_by == WARE_NONE:
                check_msg.append(u"请选择仓库")
            if trade.sys_status not in (pcfg.WAIT_AUDIT_STATUS,
                                        pcfg.WAIT_PREPARE_SEND_STATUS):
                check_msg.append(u"订单不在审单状态")
            if trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE):
                check_msg.append(u"需手动合单")
            if trade.has_sys_err:
                check_msg.append(u"订单需管理员审核")
            orders = trade.inuse_orders.exclude(
                refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
            if orders.count() == 0:
                check_msg.append(u"订单没有商品信息")
            if check_msg:
                return Response(','.join(check_msg))
            if trade.status == pcfg.WAIT_PREPARE_SEND_STATUS:
                pass
            elif trade.type == pcfg.EXCHANGE_TYPE:
                change_orders = trade.merge_orders.filter(
                    gift_type=pcfg.CHANGE_GOODS_GIT_TYPE,
                    sys_status=pcfg.IN_EFFECT)
                if change_orders.count() > 0:
                    # 订单为自提
                    if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE:
                        trade.sys_status = pcfg.FINISHED_STATUS
                        trade.status = pcfg.TRADE_FINISHED
                        trade.consign_time = datetime.datetime.now()
                        # 更新退换货库存
                        trade.update_inventory()
                    # 订单需物流
                    else:
                        trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                        trade.status = pcfg.WAIT_SELLER_SEND_GOODS
                    trade.reason_code = ''
                    trade.save()
                else:
                    # 更新退货库存
                    trade.update_inventory()
                    trade.sys_status = pcfg.FINISHED_STATUS
                    trade.status = pcfg.TRADE_FINISHED
                    trade.save()
            elif trade.type in (pcfg.DIRECT_TYPE, pcfg.REISSUE_TYPE):
                # 订单为自提
                if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE:
                    trade.sys_status = pcfg.FINISHED_STATUS
                    trade.status = pcfg.TRADE_FINISHED
                    trade.consign_time = datetime.datetime.now()
                    # 更新库存
                    trade.update_inventory()
                # 订单需物流
                else:
                    trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                    trade.status = pcfg.WAIT_SELLER_SEND_GOODS
                trade.reason_code = ''
                trade.save()
            else:
                if shipping_type == pcfg.EXTRACT_SHIPPING_TYPE:
                    try:
                        trade.out_sid = '1111111111'
                        trade.is_picking_print = True
                        trade.is_express_print = True
                        trade.company_code = pcfg.EXTRACT_COMPANEY_CODE
                        trade.logistics_company = LogisticsCompany.getNoPostCompany(
                        )
                        trade.save()

                        ts = TradeService(trade.user.id, trade)
                        ts.sendTrade()
                    except Exception, exc:
                        trade.append_reason_code(pcfg.POST_MODIFY_CODE)
                        trade.sys_status = pcfg.WAIT_AUDIT_STATUS
                        trade.sys_memo = exc.message
                        trade.save()
                        log_action(request.user.id, trade, CHANGE, u'订单发货失败')
                    else:
                        trade.sys_status = pcfg.FINISHED_STATUS
                        trade.consign_time = datetime.datetime.now()
                        trade.save()
                        log_action(request.user.id, trade, CHANGE, u'订单发货成功')
                    # 更新库存
                    trade.update_inventory()
                else:
                    MergeTrade.objects.filter(id=id, sys_status=pcfg.WAIT_AUDIT_STATUS) \
                        .update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS, reason_code='', out_sid='')
            log_action(user_id, trade, CHANGE, u'审核成功')

            signal_kefu_operate_record.send(sender=KefuPerformance,
                                            kefu_id=user_id,
                                            trade_id=id,
                                            operation="check")
        elif action_code == 'review':
            if trade.sys_status not in pcfg.WAIT_SCAN_CHECK_WEIGHT:
                return Response(u'订单不在待扫描状态')

            if is_logistic_change:
                trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)

            MergeTrade.objects.filter(id=id).update(can_review=True)
            log_action(user_id, trade, CHANGE, u'订单复审')
            signal_kefu_operate_record.send(sender=KefuPerformance,
                                            kefu_id=user_id,
                                            trade_id=id,
                                            operation="review")

        return Response({'success': True})


import re


class OrderPlusView(APIView):
    """ docstring for class OrderPlusView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)  #
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q').strip()
        if not q:
            return Response('没有输入查询关键字'.decode('utf8'))

        product_set = set()
        if re.compile('\w+').match(q):
            product_set.update(Product.objects.getProductByBarcode(q))

        queryset = Product.objects.filter(
            Q(outer_id=q) | Q(name__contains=q),
            status__in=(pcfg.NORMAL, pcfg.REMAIN))
        product_set.update(list(queryset))

        prod_list = [(prod.outer_id, prod.name, prod.std_sale_price,
                      [(sku.outer_id, sku.name, sku.quantity)
                       for sku in prod.pskus]) for prod in product_set]
        return Response(prod_list)

    def post(self, request, *args, **kwargs):
        CONTENT = request.REQUEST
        # print "post搜索条件",CONTENT.get('trade_id')
        user_id = request.user.id
        #  trade_id = request.POST.get('trade_id')
        trade_id = CONTENT.get('trade_id')
        # outer_id = request.POST.get('outer_id')
        outer_id = CONTENT.get('outer_id')
        # outer_sku_id = request.POST.get('outer_sku_id')
        outer_sku_id = CONTENT.get('outer_sku_id')
        # num      = int(request.POST.get('num',1))
        num = int(CONTENT.get('num', 1))
        # type     = request.POST.get('type',pcfg.CS_PERMI_GIT_TYPE)
        type = CONTENT.get('type', pcfg.CS_PERMI_GIT_TYPE)
        # print "你好"
        try:
            merge_trade = MergeTrade.objects.get(id=trade_id)
        except MergeTrade.DoesNotExist:
            return Response('该订单不存在'.decode('utf8'))
        try:
            Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExist:
            return Response('该商品不存在'.decode('utf8'))

        if outer_sku_id:
            try:
                ProductSku.objects.get(product__outer_id=outer_id,
                                       outer_id=outer_sku_id)
            except ProductSku.DoesNotExist:
                return Response('该商品规格不存在'.decode('utf8'))
        if not merge_trade.can_change_order:
            return HttpResponse(
                json.dumps({'code': 1,
                            "response_error": "订单不能修改！"}),
                content_type="application/json")

        is_reverse_order = False
        if merge_trade.can_reverse_order:
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
            is_reverse_order = True

        merge_order = MergeOrder.gen_new_order(
            trade_id,
            outer_id,
            outer_sku_id,
            num,
            gift_type=type,
            status=pcfg.WAIT_BUYER_CONFIRM_GOODS,
            is_reverse=is_reverse_order)
        # 组合拆分
        ruleMatchSplit(merge_trade)
        Product.objects.updateWaitPostNumByCode(
            merge_order.outer_id, merge_order.outer_sku_id, merge_order.num)
        log_action(user_id, merge_trade, ADDITION,
                   u'添加子订单(%d)' % merge_order.id)
        # print merge_order
        return Response(serializers.MergeOrderSerializer(merge_order).data)


def change_trade_addr(request):
    user_id = request.user.id
    # print "用户",user_id
    CONTENT = request.REQUEST
    # print "参数是",CONTENT.get('receiver_name')
    trade_id = CONTENT.get('trade_id')
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        "response_error": "订单不存在！"}),
            content_type="application/json")

    for (key, val) in CONTENT.items():
        setattr(trade, key, val.strip())
    trade.save()

    try:
        if trade.type in (pcfg.TAOBAO_TYPE,
                          pcfg.FENXIAO_TYPE,
                          pcfg.GUARANTEE_TYPE) \
                and trade.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                         pcfg.WAIT_CHECK_BARCODE_STATUS,
                                         pcfg.WAIT_SCAN_WEIGHT_STATUS):
            apis.taobao_trade_shippingaddress_update(
                # tid=trade.tid,
                receiver_name=trade.receiver_name,
                receiver_phone=trade.receiver_phone,
                receiver_mobile=trade.receiver_mobile,
                receiver_state=trade.receiver_state,
                receiver_city=trade.receiver_city,
                receiver_district=trade.receiver_district,
                receiver_address=trade.receiver_address,
                receiver_zip=trade.receiver_zip,
                # tb_user_id=trade.user.visitor_id
            )
    except Exception, exc:
        logger.debug(u'订单地址更新失败：%s' % exc.message)

    # 通知其他APP，订单地址已修改
    change_addr_signal.send(sender=MergeTrade, tid=trade.id)

    trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)

    if MergeTrade.objects.isTradeMergeable(trade):
        trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)

    log_action(user_id, trade, CHANGE,
               u'修改地址,修改前（%s）' % trade.buyer_full_address)

    ret_params = {'code': 0, 'success': True}

    return HttpResponse(json.dumps(ret_params), content_type="application/json")


def change_trade_order(request, id):
    user_id = request.user.id
    CONTENT = request.REQUEST
    outer_sku_id = CONTENT.get('outer_sku_id')
    order_num = int(CONTENT.get('order_num', 0))

    try:
        order = MergeOrder.objects.get(id=id)
    except MergeOrder.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        "response_error": "订单不存在！"}),
            content_type="application/json")

    try:
        prod = Product.objects.get(outer_id=order.outer_id)
    except Product.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        "response_error": "商品不存在！"}),
            content_type="application/json")

    try:
        prod_sku = ProductSku.objects.get(product__outer_id=order.outer_id,
                                          outer_id=outer_sku_id)
    except ProductSku.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        "response_error": "商品规格不存在！"}),
            content_type="application/json")

    merge_trade = order.merge_trade

    if not merge_trade.can_change_order:
        return HttpResponse(
            json.dumps({'code': 1,
                        "response_error": "商品规格不能修改！"}),
            content_type="application/json")

    old_sku_id = order.outer_sku_id
    order.outer_sku_id = prod_sku.outer_id
    order.sku_properties_name = prod_sku.name
    order.is_rule_match = False
    order.out_stock = False
    order.is_reverse_order = False

    if merge_trade.can_reverse_order:
        if order.outer_sku_id != old_sku_id or order.num != order_num:
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
        order.is_reverse_order = True
    else:
        order.out_stock = not Product.objects.isProductOutingStockEnough(
            order.outer_id, order.outer_sku_id, order_num)
    order.num = order_num
    order.save()
    merge_trade.remove_reason_code(pcfg.RULE_MATCH_CODE)

    if old_sku_id != order.outer_sku_id:
        Product.objects.reduceWaitPostNumByCode(order.outer_id, old_sku_id,
                                                order.num)
        Product.objects.updateWaitPostNumByCode(order.outer_id,
                                                order.outer_sku_id, order.num)

    log_action(user_id, merge_trade, CHANGE, u'修改子订单(%d)' % order.id)

    ret_params = {'code': 0,
                  'response_content': {
                      'id': order.id,
                      'outer_id': order.outer_id,
                      'title': prod.name,
                      'sku_properties_name': order.sku_properties_name,
                      'num': order.num,
                      'out_stock': order.out_stock,
                      'price': order.price,
                      'gift_type': order.gift_type,
                  }}

    return HttpResponse(json.dumps(ret_params), content_type="application/json")


def delete_trade_order(request, id):
    user_id = request.user.id
    try:
        merge_order = MergeOrder.objects.get(id=id, sys_status=pcfg.IN_EFFECT)
        merge_trade = merge_order.merge_trade
        is_reverse_order = False
        if merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                      pcfg.WAIT_SCAN_WEIGHT_STATUS):
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
            is_reverse_order = True

        merge_order.sys_status = pcfg.INVALID_STATUS
        merge_order.is_reverse_order = is_reverse_order
        merge_order.save()

        if merge_order.is_merge:
            iorders = MergeOrder.objects.filter(
                oid=merge_order.oid,
                sys_status=MergeOrder.NORMAL,
                merge_trade__sys_status=MergeTrade.ON_THE_FLY_STATUS)
            if iorders.exists():
                iorder = iorders[0]
                iorder.sys_status = MergeOrder.DELETE
                iorder.save()
                log_action(user_id, iorder.merge_trade, CHANGE,
                           u'飞行模式订单(oid:%s)作废' % iorder.id)

        Product.objects.reduceWaitPostNumByCode(
            merge_order.outer_id, merge_order.outer_sku_id, merge_order.num)

        log_action(user_id, merge_trade, CHANGE,
                   u'子订单(oid:%d)作废' % merge_order.id)

    except MergeOrder.DoesNotExist:
        ret_params = {'code': 1, 'response_error': u'订单不存在'}

    except Exception, exc:
        ret_params = {'code': 1, 'response_error': u'系统操作失败'}
        logger.error(u'子订单(%s)删除失败:%s' % (id, exc.message), exc_info=True)

    else:
        ret_params = {'code': 0, 'response_content': {'success': True}}

    return HttpResponse(json.dumps(ret_params), content_type="application/json")


############################### 订单复审 #################################
class ReviewOrderView(APIView):
    """ docstring for class ReviewOrderView """
    # serializer_class = serializers. ItemListTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (ReviewOrderRenderer,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, id, *args, **kwargs):

        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return Response('该订单不存在'.decode('utf8'))

        logistics = serializers.LogisticsCompanySerializer(
            LogisticsCompany.objects.filter(status=True),
            many=True).data
        order_nums = trade.inuse_orders.aggregate(
            total_num=Sum('num')).get('total_num')

        trade_dict = model_to_dict(trade)

        trade_dict.update(
            {'id': trade.id,
             'seller_nick': trade.user.nick,
             'used_orders': serializers.MergeOrderSerializer(
                 trade.inuse_orders,
                 many=True).data,  # trade.inuse_orders,
             'order_nums': order_nums,
             'logistics_company': serializers.LogisticsCompanySerializer(
                 trade.logistics_company).data,  # trade.logistics_company,
             'can_review_status': trade.sys_status in
                                  pcfg.WAIT_SCAN_CHECK_WEIGHT,
             'out_of_logistic': trade.has_reason_code(pcfg.LOGISTIC_ERROR_CODE),
             'has_rule_match': (trade.has_rule_match and trade.has_reason_code(
                 pcfg.RULE_MATCH_CODE)),
             'is_product_defect': (trade.has_rule_match and
                                   trade.has_reason_code(
                                       pcfg.TRADE_DEFECT_CODE)),
             'need_manual_merge': trade.has_reason_code(
                 pcfg.MULTIPLE_ORDERS_CODE),
             'status_name': dict(TAOBAO_TRADE_STATUS).get(trade.status, u'未知'),
             'sys_status_name': dict(SYS_TRADE_STATUS).get(trade.sys_status,
                                                           u'未知'),
             'new_memo': trade.has_reason_code(pcfg.NEW_MEMO_CODE),
             'new_refund': (trade.has_reason_code(pcfg.WAITING_REFUND_CODE) or
                            trade.has_reason_code(pcfg.NEW_REFUND_CODE)),
             'order_modify': trade.has_reason_code(pcfg.ORDER_ADD_REMOVE_CODE),
             'addr_modify': trade.has_reason_code(pcfg.ADDR_CHANGE_CODE),
             'new_merge': trade.has_reason_code(pcfg.NEW_MERGE_TRADE_CODE),
             'wait_merge': trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE),})
        print serializers.MergeOrderSerializer(trade.inuse_orders,
                                               many=True).data
        # print trade_dict
        return Response({"object": {'trade': trade_dict,
                                    'logistics': logistics}})


def review_order(request, id):
    # 仓库订单复审
    user_id = request.user.id
    try:
        merge_trade = MergeTrade.objects.get(id=id)
    except MergeTrade.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'该订单不存在'}),
            content_type="application/json")

    if not merge_trade.can_review and merge_trade.sys_status \
            not in (pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS):
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'该订单不能复审'}),
            content_type="application/json")
    MergeTrade.objects.filter(id=id).update(reason_code='')

    log_action(user_id, merge_trade, CHANGE, u'复审通过')
    return HttpResponse(
        json.dumps({'code': 0,
                    'response_content': {'success': True}}),
        content_type="application/json")


def change_order_stock_status(request, id):
    content = request.REQUEST
    out_stock = content.get('out_stock', '0')
    user_id = request.user.id

    try:
        merge_order = MergeOrder.objects.get(id=id)
    except MergeOrder.DoesNotExist:
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'该订单不存在'}),
            content_type="application/json")

    merge_trade = merge_order.merge_trade
    if merge_trade.sys_status not in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                      pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                      pcfg.FINISHED_STATUS):
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'该订单不能修改缺货状态'}),
            content_type="application/json")

    merge_order.out_stock = out_stock == '1' and True or False
    merge_order.save()

    if merge_order.out_stock:
        merge_trade.append_reason_code(pcfg.OUT_GOOD_CODE)

    log_action(user_id, merge_trade, CHANGE, u'设置订单(%d)缺货状态:%s' %
               (merge_order.id, str(merge_order.out_stock)))
    return HttpResponse(
        json.dumps({'code': 0,
                    'response_content': {'out_stock': merge_order.out_stock}}),
        content_type="application/json")


def change_logistic_and_outsid(request):
    user_id = request.user.id
    CONTENT = request.REQUEST
    trade_id = CONTENT.get('trade_id')
    out_sid = CONTENT.get('out_sid')
    logistic_code = CONTENT.get('logistic_code', '').upper()
    is_qrcode = logistic_code.endswith('QR')

    if not trade_id or (not is_qrcode and (not out_sid or not logistic_code)):
        ret_params = {'code': 1, 'response_error': u'请填写快递名称及单号'}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
    except:
        ret_params = {'code': 1, 'response_error': u'未找到该订单'}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")

    origin_logistic_code = merge_trade.logistics_company and merge_trade.logistics_company.code
    origin_out_sid = merge_trade.out_sid
    try:
        logistic = LogisticsCompany.objects.get(code=logistic_code)
        logistic_regex = re.compile(logistic.reg_mail_no)
        if not is_qrcode and not logistic_regex.match(out_sid):
            raise Exception(u'快递单号不合规则')

        real_logistic_code = logistic_code.split('_')[0]
        dt = datetime.datetime.now()
        if merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                      pcfg.WAIT_SCAN_WEIGHT_STATUS):

            try:
                if not is_qrcode and merge_trade.consign_time and (
                            dt - merge_trade.consign_time).days < 1:
                    response = apis.taobao_logistics_consign_resend(
                        tid=merge_trade.tid,
                        out_sid=out_sid,
                        company_code=real_logistic_code,
                        tb_user_id=merge_trade.user.visitor_id)
                    if not response['logistics_consign_resend_response'][
                        'shipping']['is_success']:
                        raise Exception(u'重发失败')
            except Exception, exc:
                dt = datetime.datetime.now()
                merge_trade.sys_memo = u'%s,修改快递单号[%s]:(%s)%s' % (
                    merge_trade.sys_memo, dt.strftime('%Y-%m-%d %H:%M'),
                    logistic_code, out_sid)
                logger.error(exc.message, exc_info=True)

            merge_trade.logistics_company = logistic
            merge_trade.out_sid = out_sid
            merge_trade.save()
            log_action(user_id, merge_trade, CHANGE, u'修改快递及单号(修改前:%s,%s)' %
                       (origin_logistic_code, origin_out_sid))
        elif merge_trade.sys_status == pcfg.FINISHED_STATUS:
            try:
                if not is_qrcode and merge_trade.consign_time and (
                            dt - merge_trade.consign_time).days < 1:
                    apis.taobao_logistics_consign_resend(
                        tid=merge_trade.tid,
                        out_sid=out_sid,
                        company_code=real_logistic_code,
                        tb_user_id=merge_trade.user.visitor_id)
            except:
                pass
            dt = datetime.datetime.now()
            merge_trade.sys_memo = u'%s,退回重发单号[%s]:(%s)%s' % (
                merge_trade.sys_memo, dt.strftime('%Y-%m-%d %H:%M'),
                logistic_code, out_sid)
            merge_trade.logistics_company = logistic
            merge_trade.out_sid = out_sid
            merge_trade.save()
            log_action(user_id, merge_trade, CHANGE, u'修改单号(修改前:%s,%s)' %
                       (origin_logistic_code, origin_out_sid))
        else:
            raise Exception(u'该订单不能修改')

    except Exception, exc:
        ret_params = {'code': 1, 'response_error': exc.message}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")

    ret_params = {'code': 0,
                  'response_content': {'logistic_company_name': logistic.name,
                                       'logistic_company_code': logistic.code,
                                       'out_sid': out_sid}}
    return HttpResponse(json.dumps(ret_params), content_type="application/json")


def change_package_logistic_and_outsid(request):
    CONTENT = request.REQUEST
    trade_id = CONTENT.get('trade_id')
    out_sid = CONTENT.get('out_sid')
    logistic_code = CONTENT.get('logistic_code', '').upper()
    is_qrcode = logistic_code.endswith('QR')

    if not trade_id or (not is_qrcode and (not out_sid or not logistic_code)):
        ret_params = {'code': 1, 'response_error': u'请填写快递名称及单号'}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")
    try:
        package_order = PackageOrder.objects.get(pid=trade_id)
    except:
        ret_params = {'code': 1, 'response_error': u'未找到该订单'}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")
    try:
        logistic = LogisticsCompany.objects.get(code=logistic_code)
        logistic_regex = re.compile(logistic.reg_mail_no)
        if not is_qrcode and not logistic_regex.match(out_sid):
            raise Exception(u'快递单号不合规则')
        if package_order.sys_status in (PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                        PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                                        PackageOrder.WAIT_SCAN_WEIGHT_STATUS):

            package_order.logistics_company = logistic
            package_order.out_sid = out_sid
            package_order.save()
        elif package_order.sys_status == pcfg.FINISHED_STATUS:
            dt = datetime.datetime.now()
            package_order.sys_memo = u'%s,退回重发单号[%s]:(%s)%s' % (
                package_order.sys_memo, dt.strftime('%Y-%m-%d %H:%M'),
                logistic_code, out_sid)
            package_order.logistics_company = logistic
            package_order.out_sid = out_sid
            package_order.save()
        else:
            raise Exception(u'该包裹不能修改')

    except Exception, exc:
        ret_params = {'code': 1, 'response_error': exc.message}
        return HttpResponse(json.dumps(ret_params), content_type="application/json")

    ret_params = {'code': 0,
                  'response_content': {'logistic_company_name': logistic.name,
                                       'logistic_company_code': logistic.code,
                                       'out_sid': out_sid}}
    return HttpResponse(json.dumps(ret_params), content_type="application/json")


def change_package_ware_by(request):
    CONTENT = request.REQUEST
    package_order_pid = CONTENT.get('package_order_pid')
    ware_by = int(CONTENT.get('ware_by'))
    p = PackageOrder.objects.get(pid=package_order_pid)
    p.ware_by = ware_by
    p.save()
    ret_params = {'code': 0,
                  'response_content': {'ware_by': p.get_ware_by_display(), 'ware_by_id': p.ware_by}}
    return HttpResponse(json.dumps(ret_params), content_type="application/json")

############################### 退换货订单 #################################
class ExchangeOrderView(APIView):
    """ docstring for class ExchangeOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    # authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (ExchangeOrderRender, new_BaseJSONRenderer,
                        BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):

        origin_no = MergeTrade._meta.get_field_by_name('tid')[0].get_default()
        sellers = serializers.UserSerializer(User.objects.all(), many=True).data

        return Response({'object': {'origin_no': origin_no,
                                    'sellers': sellers}})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        trade_id = content.get('tid')
        seller_id = content.get('sellerId')

        try:
            merge_trade, state = MergeTrade.objects.get_or_create(
                user_id=seller_id,
                tid=trade_id)
        except Exception, exc:
            return Response(u'退换货单创建异常:%s' % exc.message)

        if merge_trade.sys_status not in ('', pcfg.WAIT_AUDIT_STATUS):
            return Response(u'订单状态已改变')

        dt = datetime.datetime.now()
        for key, val in content.iteritems():
            hasattr(merge_trade, key) and setattr(merge_trade, key, val)

        merge_trade.type = pcfg.EXCHANGE_TYPE
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.status = pcfg.WAIT_SELLER_SEND_GOODS
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.created = dt
        merge_trade.pay_time = dt
        merge_trade.modified = dt
        merge_trade.save()

        log_action(request.user.id, merge_trade, CHANGE, u'订单创建')

        return HttpResponseRedirect(reverse('exchange_order_instance',
                                            kwargs={'id': merge_trade.id}))


class ExchangeOrderInstanceView(APIView):
    """ docstring for class ExchangeOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (ExchangeOrderRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, id, *args, **kwargs):

        merge_trade = MergeTrade.objects.get(id=id)
        # print merge_trade.user,serializers.MergeTradeSerializer(merge_trade).data['user']
        #         return  Response({ 'object':{'trade':merge_trade,
        #                 'sellers':User.objects.all()}})
        return Response(
            {'object':
                 {'trade': serializers.MergeTradeSerializer(merge_trade).data,
                  'sellers': serializers.UserSerializer(User.objects.all(),
                                                        many=True).data}})

    def post(self, request, id, *args, **kwargs):

        content = request.REQUEST
        try:
            merge_trade = MergeTrade.objects.get(id=id)
            print merge_trade
        except MergeTrade.DoesNotExist:
            return Response(u'退换货单创建异常')

        if merge_trade.sys_status not in ('', pcfg.WAIT_AUDIT_STATUS):
            return Response(u'订单状态已改变')

        for key, val in content.iteritems():
            hasattr(merge_trade, key) and setattr(merge_trade, key, val)

        merge_trade.type = pcfg.EXCHANGE_TYPE
        merge_trade.user_id = content.get('sellerId')
        merge_trade.status = pcfg.WAIT_SELLER_SEND_GOODS
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.save()

        log_action(request.user.id, merge_trade, CHANGE, u'订单修改')

        return Response(
            {'object':
                 {'trade': serializers.MergeTradeSerializer(merge_trade).data,
                  'type': merge_trade.type,
                  'sellers': serializers.UserSerializer(User.objects.all(),
                                                        many=True).data}})


############################### 内售订单 #################################
class DirectOrderView(APIView):
    """ docstring for class DirectOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (DirectOrderRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        type = content.get('type', '')
        origin_no = MergeTrade._meta.get_field_by_name('tid')[0].get_default()
        sellers = User.objects.all()

        return Response(
            {'object': {'origin_no': origin_no,
                        'trade_type': type,
                        'sellers': serializers.UserSerializer(sellers,
                                                              many=True).data}})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        trade_id = content.get('tid')
        seller_id = content.get('sellerId')
        trade_type = content.get('trade_type')

        if trade_type not in (pcfg.DIRECT_TYPE, pcfg.REISSUE_TYPE):
            return Response(u'订单类型异常')
        try:
            merge_trade, state = MergeTrade.objects.get_or_create(
                user_id=seller_id,
                tid=trade_id)
        except Exception, exc:
            return Response(u'退换货单创建异常:%s' % exc.message)

        if merge_trade.sys_status not in ('', pcfg.WAIT_AUDIT_STATUS):
            return Response(u'订单状态已改变')

        dt = datetime.datetime.now()
        for key, val in content.iteritems():
            hasattr(merge_trade, key) and setattr(merge_trade, key, val)

        merge_trade.type = trade_type
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.status = pcfg.WAIT_SELLER_SEND_GOODS
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.created = dt
        merge_trade.pay_time = dt
        merge_trade.modified = dt
        merge_trade.save()

        log_action(request.user.id, merge_trade, CHANGE, u'订单创建')

        return HttpResponseRedirect(reverse('direct_order_instance',
                                            kwargs={'id': merge_trade.id}))


class DirectOrderInstanceView(APIView):
    """ docstring for class DirectOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (DirectOrderRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, id, *args, **kwargs):

        merge_trade = MergeTrade.objects.get(id=id)
        sellers = User.objects.all()

        return Response(
            {'object': {'trade': serializers.MergeTradeSerializer(
                merge_trade).data,
                        'trade_type': merge_trade.type,
                        'sellers': serializers.UserSerializer(sellers,
                                                              many=True).data}})

    def post(self, request, id, *args, **kwargs):

        content = request.REQUEST
        type = content.get('trade_type')

        if type not in (pcfg.DIRECT_TYPE, pcfg.REISSUE_TYPE):
            return Response(u'订单类型异常')
        try:
            merge_trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return Response(u'内售单创建异常')

        if merge_trade.sys_status not in ('', pcfg.WAIT_AUDIT_STATUS):
            return Response(u'订单状态已改变')

        for key, val in content.iteritems():
            hasattr(merge_trade, key) and setattr(merge_trade, key, val)

        merge_trade.user_id = content.get('sellerId')
        merge_trade.status = pcfg.WAIT_SELLER_SEND_GOODS
        merge_trade.sys_status = merge_trade.sys_status or pcfg.WAIT_AUDIT_STATUS
        merge_trade.save()

        log_action(request.user.id, merge_trade, CHANGE, u'订单修改')

        #         return {'trade':merge_trade,
        #                 'trade_type':merge_trade.type,
        #                 'sellers':User.objects.all()}
        return Response(
            {'object':
                 {'trade': serializers.MergeTradeSerializer(merge_trade).data,
                  'trade_type': merge_trade.type,
                  'sellers': serializers.UserSerializer(User.objects.all(),
                                                        many=True).data}})


def update_sys_memo(request):
    user_id = request.user.id
    content = request.REQUEST
    trade_id = content.get('trade_id', '')
    sys_memo = content.get('sys_memo', '')
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
    except:
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'订单未找到'}),
            content_type="application/json")
    else:
        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        merge_trade.sys_memo = sys_memo
        merge_trade.save()
        MergeTrade.objects.filter(id=merge_trade.id, sys_status=pcfg.WAIT_PREPARE_SEND_STATUS, out_sid='') \
            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        log_action(user_id, merge_trade, CHANGE, u'系统备注:%s' % sys_memo)
        return HttpResponse(
            json.dumps({'code': 0,
                        'response_content': {'success': True}}),
            content_type="application/json")


def regular_trade(request, id):
    regular_days = request.REQUEST.get('days', '1')
    if not regular_days.isdigit() or int(regular_days) <= 0:
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'定时时间不合法'}),
            content_type="application/json")

    regular_days = int(regular_days)
    user_id = request.user.id
    try:
        merge_trade = MergeTrade.objects.get(id=id,
                                             sys_status=pcfg.WAIT_AUDIT_STATUS)
    except:
        return HttpResponse(
            json.dumps({'code': 1,
                        'response_error': u'订单不在问题单'}),
            content_type="application/json")
    else:
        dt = datetime.datetime.now() + datetime.timedelta(regular_days, 0, 0)
        merge_trade.sys_status = pcfg.REGULAR_REMAIN_STATUS
        merge_trade.remind_time = dt
        merge_trade.save()
        log_action(user_id, merge_trade, CHANGE,
                   u'定时(%s)提醒' % dt.strftime('%Y-%m-%d %H:%M'))
        signal_kefu_operate_record.send(sender=KefuPerformance,
                                        kefu_id=user_id,
                                        trade_id=id,
                                        operation="delay")
        return HttpResponse(
            json.dumps({'code': 0,
                        'response_content': {'success': True}}),
            content_type="application/json")


def replay_trade_send_result(request, id):
    try:
        replay_trade = ReplayPostTrade.objects.get(id=id)
    except:
        return HttpResponse(
            '<body style="text-align:center;"><h1>发货结果未找到</h1></body>')
    else:
        from shopback.trades.tasks import get_replay_results
        try:
            reponse_result = get_replay_results(replay_trade)
        except Exception, exc:
            logger.error('trade post callback error:%s' % exc.message,
                         exc_info=True)
        reponse_result['post_no'] = reponse_result.get('post_no',
                                                       None) or replay_trade.id

        return render_to_response('trades/trade_post_success.html',
                                  reponse_result,
                                  context_instance=RequestContext(request),
                                  content_type="text/html")


def replay_package_send_result(request, id):
    try:
        replay_trade = ReplayPostTrade.objects.get(id=id)
    except:
        return HttpResponse(
            '<body style="text-align:center;"><h1>发货结果未找到</h1></body>')
    else:
        from shopback.trades.tasks import get_replay_package_results
        reponse_result = {}
        try:
            reponse_result = get_replay_package_results(replay_trade)
        except Exception, exc:
            logger.error('trade post callback error:%s' % exc.message,
                         exc_info=True)
        reponse_result['post_no'] = reponse_result.get('post_no',
                                                       None) or replay_trade.id

        return render_to_response('trades/trade_post_success.html',
                                  reponse_result,
                                  context_instance=RequestContext(request),
                                  content_type="text/html")


class TradeSearchView(APIView):
    """ docstring for class ExchangeOrderView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        trade_list = []
        q = request.REQUEST.get('q')
        if not q:
            return Response(u'请输入查询字符串')

        if q.isdigit():
            # trades = MergeTrade.objects.filter(Q(id=q) | Q(tid=q) | Q(
            #     buyer_nick=q) | Q(receiver_mobile=q))
            # print PackageSkuItem.objects.filter(outer_id = 822289700121).count()
            trades = PackageSkuItem.objects.filter(Q(receiver_mobile=q) | Q(package_order_pid=q) | Q(outer_id=q))
        else:
            return Response(trade_list)

        for trade in trades:
            if trade.package_order_pid:
                package_order = PackageOrder.objects.get(pid=trade.package_order_pid)
                trade_dict = {}
                trade_dict['id'] = trade.id
                trade_dict['tid'] = trade.sale_trade_id  # 原单ＩＤ
                trade_dict['oid'] = trade.oid
                trade_dict['seller_id'] = "未知"
                trade_dict['outer_id'] = trade.outer_id
                trade_dict['buyer_nick'] = package_order.buyer_nick  # 购买者昵称
                trade_dict['post_fee'] = package_order.post_cost  # 物流费用
                trade_dict['payment'] = trade.payment  # 实付款
                trade_dict['total_num'] = trade.num  # 单数
                trade_dict['pay_time'] = trade.pay_time  # 付款日期
                trade_dict['consign_time'] = '未知'  # 预售日期
                trade_dict['receiver_name'] = package_order.receiver_name   # 收货人
                trade_dict['receiver_state'] = package_order.receiver_state  # 收货人省
                trade_dict['receiver_city'] = package_order.receiver_city  # 收货人市
                trade_dict['receiver_district'] = package_order.receiver_district  # 区
                trade_dict['receiver_address'] = package_order.receiver_address  # 详细地址
                trade_dict['receiver_mobile'] = trade.receiver_mobile  # 收货人手机
                trade_dict['receiver_phone'] = package_order.receiver_phone  # 收货人电话
                trade_dict['receiver_zip'] = package_order.receiver_zip  # 收货人邮编
                trade_dict['package_order_pid'] = trade.package_order_pid
                # trade_dict['status'] = dict(TAOBAO_TRADE_STATUS).get(trade.status,
                #                                                      u'其他') #订单状态
                trade_dict['status'] = trade.get_assign_status_display()
                # trade_dict['sys_status'] = dict(SYS_TRADE_STATUS).get(
                #     trade.sys_status, u'其他')                                #系统状态
                trade_dict['sys_status'] = trade.get_assign_status_display()
                trade_list.append(trade_dict)
        return Response(trade_list)

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        cp_tid = content.get('cp_tid')
        pt_tid = content.get('pt_tid')
        type = content.get('type', '')

        if not cp_tid or not pt_tid or not type.isdigit():
            return Response(u'请输入订单编号及退换货类型')

        try:
            cp_trade = MergeTrade.objects.get(id=cp_tid)
        except MergeTrade.DoesNotExist:
            return Response(u'订单未找到')

        try:
            pt_trade = MergeTrade.objects.get(id=pt_tid)
        except MergeTrade.DoesNotExist:
            return u'订单未找到'

        can_post_orders = cp_trade.merge_orders.all()
        for order in can_post_orders:
            try:
                MergeOrder.gen_new_order(pt_trade.id,
                                         order.outer_id,
                                         order.outer_sku_id,
                                         order.num,
                                         gift_type=type)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)

        orders = pt_trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)
        order_list = []
        for order in orders:
            try:
                prod = Product.objects.get(outer_id=order.outer_id)
            except Exception, exc:
                prod = None
            try:
                prod_sku = ProductSku.objects.get(
                    outer_id=order.outer_sku_id,
                    product__outer_id=order.outer_id)
            except:
                prod_sku = None
            order_dict = {
                'id': order.id,
                'outer_id': order.outer_id,
                'title': prod.name if prod else order.title,
                'sku_properties_name': (prod_sku.properties_name if prod_sku
                                        else order.sku_properties_name),
                'num': order.num,
                'out_stock': order.out_stock,
                'price': order.price,
                'gift_type': order.gift_type,
            }
            order_list.append(order_dict)

        return Response(order_list)

# class OrderListView(APIView):
#     """ docstring for class OrderListView """
#     permission_classes = (permissions.IsAuthenticated,)
#     authentication_classes = (authentication.SessionAuthentication,
#                               authentication.BasicAuthentication,)
#     renderer_classes = (OrderListRender,
#                         new_BaseJSONRenderer,
#                         BrowsableAPIRenderer,)
#
#     def get(self, request, id, *args, **kwargs):
#
#         order_list = []
#         try:
#             trade = MergeTrade.objects.get(id=id)
#         except:
#             return HttpResponseNotFound('<h1>订单未找到</h1>')
#         for order in trade.merge_orders.all():
#             try:
#                 prod = Product.objects.get(outer_id=order.outer_id)
#             except:
#                 prod = None
#             order_dict = {}
#             order_dict['id'] = order.id
#             order_dict['tid'] = order.merge_trade.tid
#             order_dict['outer_id'] = order.outer_id
#             order_dict['outer_sku_id'] = order.outer_sku_id
#             order_dict['total_fee'] = order.total_fee
#             order_dict['payment'] = order.payment
#             order_dict['title'] = prod and prod.name or order.title
#             order_dict['num'] = order.num
#             order_dict['sku_properties_name'] = order.sku_properties_name
#             order_dict['refund_status'] = dict(REFUND_STATUS).get(
#                 order.refund_status, u'其他')
#             order_dict['seller_nick'] = order.seller_nick
#             order_dict['buyer_nick'] = order.buyer_nick
#             order_dict['receiver_name'] = trade.receiver_name
#             order_dict['pay_time'] = order.pay_time
#             order_dict['status'] = dict(TAOBAO_ORDER_STATUS).get(order.status,
#                                                                  u'其他')
#             order_list.append(order_dict)
#
#         return Response({"object": {'order_list': order_list}})
############################### 交易订单商品列表 #################################
class OrderListView(APIView):
    """ docstring for class OrderListView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (OrderListRender,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, id, *args, **kwargs):

        order_list = []
        try:
            order = PackageSkuItem.objects.get(id=id)
        except:
            return HttpResponseNotFound('<h1>订单未找到</h1>')

        try:
            prod = Product.objects.get(outer_id=order.outer_id)
        except:
            prod = None
        order_dict = {}
        order_dict['id'] = order.id     #PackageSkuItem的id
        order_dict['tid'] = order.sale_trade_id      #PackageSkuItem的原单id
        order_dict['oid'] = order.oid
        order_dict['outer_id'] = order.outer_id     #PackageSkuItem的商品编码
        order_dict['outer_sku_id'] = order.outer_sku_id     #PackageSkuItem的规格ＩＤ
        order_dict['total_fee'] = order.total_fee       #PackageSkuItem的总费用
        order_dict['payment'] = order.payment       #PackageSkuItem的实付款
        order_dict['title'] = prod and prod.name or order.title     #PackageSkuItem的商品名字
        order_dict['num'] = order.num       #PackageSkuItem的件数
        order_dict['sku_properties_name'] = SaleOrder.objects.get(id = order.sale_order_id).sku_name        #SaleＯrder的sku名字
        # order_dict['refund_status'] = dict(REFUND_STATUS).get(
        #     order.refund_status, u'其他')
        # order_dict['seller_nick'] = order.seller_nick
        order_dict['refund_status'] = order.get_refund_status_display()     #PackageSkuItem退款状态
        order_dict['buyer_nick'] = PackageOrder.objects.get(pid=order.package_order_pid).buyer_nick     #PackageOrder的买家昵称
        order_dict['receiver_name'] = PackageOrder.objects.get(pid = order.package_order_pid).receiver_name     #PackageOrder的收货人
        order_dict['pay_time'] = order.pay_time     #PackageSkuItem的付款时间
        order_dict['status'] = order.get_assign_status_display()        #PackageSkuItem的状态
        order_list.append(order_dict)

        return Response({"object": {'order_list': order_list}})


############################### 关联销售商品 #################################


class RelatedOrderStateView(APIView):
    """ docstring for class RelatedOrderStateView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (RelatedOrderRenderer,
                        new_BaseJSONRenderer,
                        BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        df = content.get('df')
        dt = content.get('dt')
        outer_id = content.get('outer_id', '')
        outer_sku_ids = content.get('sku_ids')
        limit = content.get('limit', 10)

        if df and dt:
            start_dt = parse_date(df)
            end_dt = parse_date(dt)
            start_dt = datetime.datetime(start_dt.year, start_dt.month,
                                         start_dt.day, 0, 0, 0)
            end_dt = datetime.datetime(end_dt.year, end_dt.month, end_dt.day,
                                       23, 59, 59)
        else:
            dt = datetime.datetime.now()
            start_dt = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)
            end_dt = datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)

        order_item_list = []
        if outer_id:
            merge_orders = MergeOrder.objects.filter(
                outer_id=outer_id,
                created__gte=start_dt,
                created__lte=end_dt).exclude(
                status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,
                            pcfg.WAIT_BUYER_PAY, pcfg.TRADE_CLOSED))
            if outer_sku_ids:
                sku_ids = outer_sku_ids.split(',')
                merge_orders = merge_orders.filter(outer_sku_id__in=sku_ids)

            buyer_set = set()
            relative_orders_dict = {}
            for order in merge_orders:
                receiver_mobile = order.merge_trade.receiver_mobile
                try:
                    buyer_set.remove(receiver_mobile)
                except:
                    buyer_set.add(receiver_mobile)
                    relat_orders = MergeOrder.objects.filter(
                        merge_trade__receiver_mobile=receiver_mobile,
                        is_merge=False,
                        created__gte=start_dt,
                        created__lte=end_dt).exclude(
                        status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,
                                    pcfg.WAIT_BUYER_PAY, pcfg.TRADE_CLOSED))
                    for o in relat_orders:
                        relat_outer_id = o.outer_id
                        if relative_orders_dict.has_key(relat_outer_id):
                            relative_orders_dict[relat_outer_id][
                                'cnum'] += o.num
                        else:
                            relative_orders_dict[relat_outer_id] = {'pic_path':
                                                                        o.pic_path,
                                                                    'title':
                                                                        o.title,
                                                                    'cnum':
                                                                        o.num}
                else:
                    buyer_set.add(receiver_mobile)

            relat_order_list = sorted(relative_orders_dict.items(),
                                      key=lambda d: d[1]['cnum'],
                                      reverse=True)

            for order in relat_order_list[0:int(limit)]:
                pic_path = order[1]['pic_path']
                try:
                    product = Product.objects.get(outer_id=order[0])
                except Product.DoesNotExist:
                    pass
                else:
                    pic_path = pic_path or product.pic_path
                order_item = []
                order_item.append(order[0])
                order_item.append(pic_path)
                order_item.append(order[1]['title'])
                order_item.append(order[1]['cnum'])
                order_item_list.append(order_item)

        return Response({"object": {'df': format_date(start_dt),
                                    'dt': format_date(end_dt),
                                    'outer_id': outer_id,
                                    'limit': limit,
                                    'order_items': order_item_list}})

    post = get


############################### 订单物流信息列表 #################################
class TradeLogisticView(APIView):
    """ docstring for class TradeLogisticView """
    # serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (TradeLogisticRender, new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        q = content.get('q')
        df = content.get('df')
        dt = content.get('dt')
        trade_list = []
        weight_list = []
        TOTAL_count = 0

        if q:
            mergetrades = MergeTrade.objects.filter(out_sid=q.strip('\' '),
                                                    is_express_print=True)
            for trade in mergetrades:
                trade_dict = {"tid": trade.tid,
                              "seller_nick": trade.user.nick,
                              "buyer_nick": trade.buyer_nick,
                              "out_sid": trade.out_sid,
                              "logistics_company": trade.logistics_company.name,
                              "receiver_name": trade.receiver_name,
                              "receiver_state": trade.receiver_state,
                              "receiver_city": trade.receiver_city,
                              "receiver_district": trade.receiver_district,
                              "receiver_address": trade.receiver_address,
                              "receiver_zip": trade.receiver_zip,
                              "receiver_phone": trade.receiver_phone,
                              "receiver_mobile": trade.receiver_mobile,
                              "weight": trade.weight}

                trade_list.append(trade_dict)

        if df:
            df = parse_date(df).date()
            queryset = MergeTrade.objects.filter(
                sys_status=pcfg.FINISHED_STATUS,
                weight_time__gt=df,
                logistics_company__code__in=("YUNDA", "YUNDA_QR"))
            if dt:
                dt = parse_date(dt).date()
                queryset = queryset.filter(weight_time__lt=dt)

            TOTAL_count = queryset.count()

            SH_weight = queryset.filter(receiver_state=u'上海').aggregate(
                wt=Sum('weight')).get('wt')
            SH_count = queryset.filter(receiver_state=u'上海').count()
            JZA_weight = queryset.filter(
                receiver_state__in=(u'江苏省', u'浙江省', u'安徽省')).aggregate(
                wt=Sum('weight')).get('wt')
            JZA_count = queryset.filter(
                receiver_state__in=(u'江苏省', u'浙江省', u'安徽省')).count()
            OTHER_weight = queryset.exclude(
                receiver_state__in=(u'上海', '江苏省', u'浙江省', u'安徽省')).aggregate(
                wt=Sum('weight')).get('wt')
            OTHER_count = queryset.exclude(
                receiver_state__in=(u'上海', '江苏省', u'浙江省', u'安徽省')).count()

            weight_list.append((SH_weight, SH_count))
            weight_list.append((JZA_weight, JZA_count))
            weight_list.append((OTHER_weight, OTHER_count))

        return Response({'logistics': trade_list,
                         'df': df or '',
                         'dt': dt or '',
                         'yunda_count': TOTAL_count,
                         'weights': weight_list})

    post = get


def calFenxiaoInterval(fdt, tdt):
    fenxiao_array = []
    fenxiao_dict = {}
    fenxiao_sum = 0
    fenxiao = MergeTrade.objects.filter(pay_time__gte=fdt,
                                        pay_time__lte=tdt,
                                        type=pcfg.FENXIAO_TYPE,
                                        sys_status=pcfg.FINISHED_STATUS)
    # buyer_nick elf,
    for f in fenxiao:

        buyer_nick = f.buyer_nick
        if fenxiao_dict.has_key(buyer_nick):
            fenxiao_dict[buyer_nick] = fenxiao_dict[buyer_nick] + float(
                f.payment or 0)
        else:
            fenxiao_dict[buyer_nick] = float(f.payment or 0)
    fenxiao_array = fenxiao_dict.items()

    fenxiao_array.sort(lambda x, y: cmp(x[1], y[1]))
    for key in fenxiao_array:
        fenxiao_sum = fenxiao_sum + key[1]
    fenxiao_array.append(["sum", fenxiao_sum])

    return fenxiao_array


def countFenxiaoAcount(request):
    content = request.POST
    fromDate = content.get('fromDate')
    toDate = content.get('endDate')

    toDate = (toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or
              datetime.datetime.now().date())

    fromDate = (fromDate and
                datetime.datetime.strptime(fromDate, '%Y%m%d').date() or
                toDate - datetime.timedelta(days=1))
    fromDateShow = fromDate.strftime('%Y%m%d')
    toDateShow = toDate.strftime('%Y%m%d')
    fenxiaoDict = calFenxiaoInterval(fromDate, toDate)
    print 'fromDateShow', fromDateShow

    return render_to_response('trades/trade_fenxiao_count.html',
                              {'data': fenxiaoDict,
                               'fromDateShow': fromDateShow,
                               'toDateShow': toDateShow,},
                              context_instance=RequestContext(request))


def showFenxiaoDateilFilter(fenxiao, fdt, tdt):
    fenxiao = MergeTrade.objects.filter(buyer_nick=fenxiao,
                                        pay_time__gte=fdt,
                                        pay_time__lte=tdt,
                                        type=pcfg.FENXIAO_TYPE,
                                        sys_status=pcfg.FINISHED_STATUS)
    #    print "fenxiao",fenxiao[2].tid
    return fenxiao


def showFenxiaoDetail(request):
    content = request.GET
    fenxiao = content.get('fenxiao')

    fromDate = content.get('fdt').replace('-', '')
    oneday = datetime.timedelta(days=1)
    toDate = content.get('tdt')

    if toDate:
        toDate = datetime.date.today().strftime('%Y%m%d')
    else:
        toDate = toDate.replace('-', '')

    toDate = (toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or
              datetime.datetime.now().date())
    toDate = toDate + oneday
    fromDate = (fromDate and
                datetime.datetime.strptime(fromDate, '%Y%m%d').date() or
                toDate - datetime.timedelta(days=1))
    # date  over
    iid = []
    tid = []
    created = []
    buyer_nick = []
    receiver_name = []
    receiver_mobile = []
    receiver_state = []
    receiver_city = []
    receiver_district = []
    receiver_address = []
    payment = []

    fenxiao_render_data = []

    FenxiaoDateil = showFenxiaoDateilFilter(fenxiao, fromDate, toDate)
    #    FenxiaoDateil=showFenxiaoDateilFilter('爱生活791115','20140526','20140527')
    for c in FenxiaoDateil:
        tid.append(c.tid)
        iid.append(c.id)
        created.append(c.created)
        buyer_nick.append(c.buyer_nick)
        receiver_name.append(c.receiver_name)
        receiver_mobile.append(c.receiver_mobile)
        receiver_state.append(c.receiver_state)
        receiver_city.append(c.receiver_city)
        receiver_district.append(c.receiver_district)
        receiver_address.append(c.receiver_address)
        payment.append(c.payment)

    for i, v in enumerate(tid):
        fenxiao_render_data.append((buyer_nick[i], tid[i], receiver_name[
            i], receiver_mobile[i], receiver_state[i], receiver_city[
                                        i], receiver_district[i], receiver_address[i], payment[i], iid[
                                        i]))

    return render_to_response('trades/trade_fenxiao_detail.html',
                              {'FenxiaoDateil': FenxiaoDateil,
                               'fenxiao_render_data': fenxiao_render_data,},
                              context_instance=RequestContext(request))


########################## 提升订单优先级 ###########################
class ImprovePriorityView(APIView):
    """ docstring for class OrderListView """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def post(self, request, id, *args, **kwargs):
        row = MergeTrade.objects.filter(id=id).update(
            priority=pcfg.PRIORITY_HIG)

        return Response({'success': row > 0})


########################## 提升订单优先级 ###########################


# fang  将django中的方法提取出来
# 获取订单备注，几乎是自己重新写的方法   2015-7-29
class InstanceModelView_new(APIView):
    # print "zheli"
    serializer_class = serializers.MergeTradeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    authentication_classes = (authentication.SessionAuthentication,
                              authentication.BasicAuthentication,)
    renderer_classes = (CheckOrderRenderer, new_BaseJSONRenderer,)

    def get(self, request, id, *args, **kwargs):
        # print "zheli44",id
        trade = MergeTrade.objects.get(id=id)
        serializer = serializers.MergeTradeSerializer(trade).data
        # return Response({"example":"get__function"})
        return Response(serializer)


########################## 订单重量入库 ###########################
class PackageScanCheckView(APIView):
    """ 订单扫描验货 """
    #     permission_classes = (permissions.IsAuthenticated,)
    #     authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    #    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (new_BaseJSONRenderer,)

    def isValidYundaId(self, package_no):
        if len(package_no) < 13:
            return False

        yunda_company = LogisticsCompany.objects.get(code='YUNDA')
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])

    def parsePackageNo(self, package_no):

        if not self.isValidYundaId(package_no):
            return package_no

        return package_no[0:13]

    def getOrderItemsFromTrade(self, trade):

        order_items = []
        for order in trade.print_orders:

            barcode = Product.objects.getBarcodeByOuterid(order.outer_id,
                                                          order.outer_sku_id)
            product = Product.objects.getProductByOuterid(order.outer_id)
            product_sku = None
            if order.outer_sku_id:
                product_sku = Product.objects.getProductSkuByOuterid(
                    order.outer_id, order.outer_sku_id)
            is_need_check = product_sku and product_sku.post_check or product.post_check

            order_dict = {'barcode': barcode,
                          'order_id': order.id,
                          'outer_id': order.outer_id,
                          'outer_sku_id': order.outer_sku_id,
                          'title': order.title,
                          'sku_properties_name': order.sku_properties_name,
                          'sku_name': product_sku and product_sku.name or '',
                          'pic_path': product.pic_path,
                          'num': order.num,
                          'post_check': is_need_check,
                          'status': order.get_status_display()}

            order_items.append(order_dict)

        return order_items

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        package_no = content.get('package_no', '').strip()
        if not package_no:
            return Response(u'运单号不能为空')

        package_id = self.parsePackageNo(package_no)
        try:
            mt = MergeTrade.objects.get(
                out_sid=package_id,
                reason_code='',
                sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        except MergeTrade.DoesNotExist:
            return Response(u'运单号未找到订单')
        except MergeTrade.MultipleObjectsReturned:
            return Response(u'结果返回多个订单')

        order_items = self.getOrderItemsFromTrade(mt)

        return Response({'package_no': package_id,
                         'trade_id': mt.id,
                         'order_items': order_items})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        package_no = content.get('package_no', '').strip()

        if not package_no:
            return Response(u'运单号不能为空')

        package_id = self.parsePackageNo(package_no)
        try:
            mt = MergeTrade.objects.get(
                out_sid=package_id,
                reason_code='',
                sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS)
        except MergeTrade.DoesNotExist:
            return Response(u'运单号未找到订单或被拦截')

        except MergeTrade.MultipleObjectsReturned:
            return Response(u'运单号返回多个订单')

        mt.sys_status = pcfg.WAIT_SCAN_WEIGHT_STATUS
        mt.scanner = request.user.username
        mt.save()
        package = mt.get_package()
        if package:
            package.set_out_sid(mt.out_sid, mt.logistics_company_id)
        log_action(mt.user.user.id, mt, CHANGE, u'扫描验货')

        return Response({'isSuccess': True})


from core.options import get_systemoa_user
from flashsale.dinghuo.tasks import task_stats_paytopack
from shopback.trades.tasks import uploadTradeLogisticsTask


########################## 订单重量入库 ###########################
class PackageScanWeightView(APIView):
    """ 订单扫描称重 """
    #     permission_classes = (permissions.IsAuthenticated,)
    #     authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,)

    def isValidYundaId(self, package_no):
        if len(package_no) < 13:
            return False

        yunda_company = LogisticsCompany.objects.get(code='YUNDA')
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])

    def parsePackageNo(self, package_no):

        if not self.isValidYundaId(package_no):
            return package_no

        return package_no[0:13]

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        package_no = content.get('package_no', '').strip()
        if not package_no:
            return Response(u'运单号不能为空')

        package_id = self.parsePackageNo(package_no)

        try:
            mt = MergeTrade.objects.get(
                out_sid=package_id,
                reason_code='',
                sys_status__in=(pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                pcfg.WAIT_CHECK_BARCODE_STATUS))
        except MergeTrade.DoesNotExist:
            return Response(u'运单号未找到订单或被拦截')
        except MergeTrade.MultipleObjectsReturned:
            return Response(u'运单号返回多个订单')

        return Response({'package_no': package_id,
                         'trade_id': mt.id,
                         'seller_nick': mt.user.nick,
                         'trade_type': mt.get_type_display(),
                         'buyer_nick': mt.buyer_nick,
                         'sys_status': mt.get_sys_status_display(),
                         'company_name': mt.logistics_company.name,
                         'receiver_mobile': mt.receiver_mobile,
                         'receiver_name': mt.receiver_name,
                         'receiver_state': mt.receiver_state,
                         'receiver_city': mt.receiver_city,
                         'receiver_district': mt.receiver_district,
                         'receiver_address': mt.receiver_address})

    def post(self, request, *args, **kwargs):
        from flashsale.pay.models import SaleOrder
        content = request.REQUEST
        package_no = content.get('package_no', '').strip()
        package_weight = content.get('package_weight', '').strip()

        if not package_no:
            return Response(u'运单号不能为空')

        try:
            if float(package_weight) > 100000:
                return Response(u'重量超过100千克')
        except:
            return Response(u'重量异常:%s' % package_weight)

        package_id = self.parsePackageNo(package_no)
        try:
            mt = MergeTrade.objects.get(
                out_sid=package_id,
                reason_code='',
                sys_status__in=(pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                pcfg.WAIT_CHECK_BARCODE_STATUS))

        except MergeTrade.DoesNotExist:
            return Response(u'运单号未找到订单')
        except MergeTrade.MultipleObjectsReturned:
            return Response(u'结果返回多个订单')

        MergeTrade.objects.updateProductStockByTrade(mt)

        mt.weight = package_weight
        mt.sys_status = pcfg.FINISHED_STATUS
        mt.weight_time = datetime.datetime.now()
        mt.weighter = request.user.username
        mt.save()
        # 上传单号
        uploadTradeLogisticsTask.delay(mt.id, get_systemoa_user().id)
        log_action(mt.user.user.id, mt, CHANGE, u'扫描称重')

        mo = mt.normal_orders
        for entry in mo:
            pay_date = entry.pay_time.date()
            sku_num = 1  # not entry.num, intentionally ignore sku_num effect
            time_delta = mt.weight_time - entry.pay_time
            total_days = sku_num * (time_delta.total_seconds() / 86400.0)

            task_stats_paytopack.delay(pay_date, sku_num, total_days)
        return Response({'isSuccess': True})


####fang   发现这个函数没有被调用
class SaleMergeOrderListView(APIView):
    """ docstring for class SaleMergeOrderListView """

    def parseStartDt(self, start_dt):

        if not start_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

        if len(start_dt) > 10:
            return parse_datetime(start_dt)

        return parse_date(start_dt)

    def parseEndDt(self, end_dt):

        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)

        if len(end_dt) > 10:
            return parse_datetime(end_dt)

        return parse_date(end_dt)

    def getSourceTrades(self, order_qs):

        trade_ids = [t[0] for t in order_qs.values_list('merge_trade__id')]

        return MergeTrade.objects.filter(id__in=trade_ids)

    def getEffectOrdersId(self, order_qs):

        return [o[0] for o in order_qs.values_list('oid') if len(o) > 0]

    def getProductByOuterId(self, outer_id):

        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None

    def getProductSkuByOuterId(self, outer_id, outer_sku_id):

        try:
            return ProductSku.objects.get(outer_id=outer_sku_id,
                                          product__outer_id=outer_id)
        except:
            return None

    def getProductAndSku(self, outer_id, outer_sku_id):

        self.prod_map = {}
        outer_key = '-'.join((outer_id, outer_sku_id))
        if self.prod_map.has_key(outer_key):
            return self.prod_map.get(outer_key)

        prod = self.getProductByOuterId(outer_id)
        prod_sku = self.getProductSkuByOuterId(outer_id, outer_sku_id)
        self.prod_map[outer_key] = (prod, prod_sku)
        return (prod, prod_sku)

    def getTradeSortedItems(self, order_qs, is_sale=False):

        order_dict_list = order_qs.values('outer_id', 'outer_sku_id', 'payment',
                                          'title', 'sku_properties_name', 'num',
                                          'num_iid', 'sku_id')
        trade_items = {}
        for order in order_dict_list:

            outer_id = order['outer_id'] or str(order['num_iid'])
            outer_sku_id = order['outer_sku_id'] or str(order['sku_id'])
            payment = float(order['payment'] or 0)
            order_num = order['num'] or 0
            order_title = order['title']
            order_sku_name = order['sku_properties_name']
            prod, prod_sku = self.getProductAndSku(outer_id, outer_sku_id)

            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order_num
                skus = trade_items[outer_id]['skus']

                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order_num
                    skus[outer_sku_id]['cost'] += skus[outer_sku_id][
                                                      'std_purchase_price'] * order_num
                    skus[outer_sku_id]['sales'] += payment
                    # 累加商品成本跟销售额
                    trade_items[outer_id]['cost'] += skus[outer_sku_id][
                                                         'std_purchase_price'] * order_num
                    trade_items[outer_id]['sales'] += payment
                else:
                    prod_sku_name = prod_sku.name if prod_sku else order_sku_name
                    purchase_price = float(prod_sku.cost) if prod_sku else 0
                    # 累加商品成本跟销售额
                    trade_items[outer_id]['cost'] += purchase_price * order_num
                    trade_items[outer_id]['sales'] += payment

                    skus[outer_sku_id] = {
                        'sku_name': prod_sku_name,
                        'num': order_num,
                        'cost': purchase_price * order_num,
                        'sales': payment,
                        'std_purchase_price': purchase_price
                    }
            else:
                prod_sku_name = prod_sku.name if prod_sku else order_sku_name
                purchase_price = float(
                    prod_sku.cost) if prod_sku else payment / order_num
                trade_items[outer_id] = {
                    'product_id': prod and prod.id or None,
                    'num': order_num,
                    'title': prod.name if prod else order_title,
                    'cost': purchase_price * order_num,
                    'pic_path': prod and prod.PIC_PATH or '',
                    'sales': payment,
                    'sale_charger': prod and prod.sale_charger or '',
                    'storage_charger': prod and prod.storage_charger or '',
                    'sales': payment,
                    'skus': {outer_sku_id: {
                        'sku_name': prod_sku_name,
                        'num': order_num,
                        'cost': purchase_price * order_num,
                        'sales': payment,
                        'std_purchase_price': purchase_price
                    }}
                }

        if is_sale:
            order_items = sorted(trade_items.items(), key=lambda d: d[0])
        else:
            order_items = sorted(trade_items.items(),
                                 key=lambda d: d[1]['num'],
                                 reverse=True)

        total_cost = 0
        total_sales = 0
        total_num = 0
        for trade in order_items:
            total_cost += trade[1]['cost']
            total_sales += trade[1]['sales']
            total_num += trade[1]['num']
            trade[1]['skus'] = sorted(trade[1]['skus'].items(),
                                      key=lambda d: d[0])

        order_items.append(total_sales)
        order_items.append(total_cost)
        order_items.append(total_num)

        return order_items

    def getTotalRefundFee(self, order_qs):

        return 0

    #         effect_oids = self.getEffectOrdersId(order_qs)

    #         return Refund.objects.filter(oid__in=effect_oids,status__in=(
    #                     pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_CONFIRM_GOODS,pcfg.REFUND_SUCCESS))\
    #                     .aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee') or 0

    def responseCSVFile(self, request, order_items):

        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1
        pcsv = []
        pcsv.append(("商品编码", "商品名称", "总数量", "成本", "销售额", "规格编码", "商品规格    ",
                     "数量", "成本", "销售额"))

        for order in order_items:
            first_loop = True
            for item in order:
                pcsv.append((first_loop and order[0] or '',
                             first_loop and order[1]['title'] or '',
                             first_loop and str(order[1]['num']) or '',
                             first_loop and str(order[1]['cost']) or '',
                             first_loop and str(order[1]['sales']) or '',
                             item[0],
                             item[1]['title'],
                             str(item[1]['num']),
                             str(item[1]['cost']),
                             str(item[1]['sales']),))
                first_loop = False

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile,
                                  encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(),
                                content_type='application/octet-stream')
        tmpfile.close()

        dt = datetime.datetime.now()

        response[
            'Content-Disposition'] = 'attachment;filename=wx-sale-%s.csv' % dt.strftime(
            "%Y%m%d%H")

        return response

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        start_dt = content.get('df', '').strip()
        end_dt = content.get('dt', '').strip()
        shop_id = content.get('shop_id')
        p_outer_id = content.get('outer_id', '')
        sc_by = content.get('sc_by', 'pay')
        wait_send = content.get('wait_send', '0')
        is_sale = content.get('is_sale', '')
        action = content.get('action', '')

        start_dt = self.parseStartDt(start_dt)
        end_dt = self.parseEndDt(end_dt)

        order_qs = self.getSourceOrders(shop_id=shop_id,
                                        sc_by=sc_by,
                                        wait_send=wait_send,
                                        p_outer_id=p_outer_id,
                                        start_dt=start_dt,
                                        end_dt=end_dt,
                                        is_sale=is_sale)

        trade_qs = self.getSourceTrades(order_qs)

        buyer_nums = trade_qs.values_list('buyer_nick').distinct().count()
        trade_nums = trade_qs.count()
        total_post_fee = trade_qs.aggregate(
            total_post_fee=Sum('post_fee')).get('total_post_fee') or 0

        refund_fees = self.getTotalRefundFee(order_qs)

        trade_list = self.getTradeSortedItems(order_qs, is_sale=is_sale)

        total_num = trade_list.pop()
        total_cost = trade_list.pop()
        total_sales = trade_list.pop()

        if action == "download":
            return self.responseCSVFile(request, trade_list)

        shopers = User.objects.filter(status=User.NORMAL)

        return {'df': format_datetime(start_dt),
                'dt': format_datetime(end_dt),
                'sc_by': sc_by,
                'is_sale': is_sale,
                'outer_id': p_outer_id,
                'wait_send': wait_send,
                'shops': shopers,
                'trade_items': trade_list,
                'shop_id': shop_id and int(shop_id) or '',
                'total_cost': total_cost and round(total_cost, 2) or 0,
                'total_sales': total_sales and round(total_sales, 2) or 0,
                'total_num': total_num,
                'refund_fees': refund_fees and round(refund_fees, 2) or 0,
                'buyer_nums': buyer_nums,
                'trade_nums': trade_nums,
                'post_fees': total_post_fee}

    post = get


def detail(request):
    """fangkaineng 2015-6-2 diingdanxiangxi """
    return render(request, 'trades/order_detail.html')


def detail22(request):
    today = datetime.datetime.utcnow()
    # startcount=MergeTrade.objects.all().count()
    # startcount=
    print '开始'
    # trade_info=MergeTrade.objects.raw('SELECT id,tid FROM shop_trades_mergetrade where id=75225 ')
    trade_info = MergeTrade.objects.raw(
        'SELECT id,count(*) as nuee  from shop_trades_mergetrade')
    print trade_info[0].tid
    # endcount=startcount-10
    # print endcount
    # trade_info=MergeTrade.objects.filter(id__gte=endcount)
    # trade_info=MergeTrade.objects.all().order_by('-created')[0:100]
    rec1 = []
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print ' 物流信息',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.merge_orders.all():
            sum = {}
            sum['order'] = order_info
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            sum['product'] = product_info
            info['detail'].append(sum)
        rec1.append(info)
        # print rec1
    return render(request, 'trades/order_detail.html', {'info': rec1,
                                                        'time': today})


ORDER_NOT_SEND_STATUS = (pcfg.TRADE_NO_CREATE_PAY, pcfg.WAIT_BUYER_PAY,
                         pcfg.WAIT_SELLER_SEND_GOODS,
                         pcfg.TRADE_CLOSED_BY_TAOBAO)
ORDER_SEND_STATUS = (pcfg.WAIT_BUYER_CONFIRM_GOODS, pcfg.TRADE_BUYER_SIGNED,
                     pcfg.TRADE_FINISHED, pcfg.TRADE_CLOSED)


def search_trade(request):
    """搜索订单 根据商品编码 订单内容"""
    today = datetime.datetime.today()

    if request.method == "POST":
        rec1 = []
        number1 = request.POST.get('condition')
        status = request.POST.get('status')
        product = request.POST.get('product').strip()
        number = number1.strip()
        moqs = MergeOrder.objects.all().order_by("pay_time")
        if status:
            if status == u'1':
                moqs = moqs.filter(
                    merge_trade__status__in=ORDER_NOT_SEND_STATUS)
            elif status == u'2':
                moqs = moqs.filter(merge_trade__status__in=ORDER_SEND_STATUS)
        if product == "":
            rec1 = []
        else:
            product_split = product.split(" ")
            if len(product_split) > 1:
                all_order = moqs.filter(Q(outer_id=product_split[0],
                                          outer_sku_id=product_split[1],
                                          sys_status=pcfg.IN_EFFECT))
            else:
                all_order = moqs.filter(Q(outer_id=product,
                                          sys_status=pcfg.IN_EFFECT))
            all_trade_id = set()
            for one_order in all_order:
                trade_id = one_order.merge_trade_id
                one_trade = one_order.merge_trade
                if trade_id in all_trade_id:
                    continue
                else:
                    all_trade_id.add(one_order.merge_trade_id)
                info = {}
                try:
                    # a = getLogisticTrace(one_trade.out_sid, one_trade.logistics_company.code)
                    a = []
                except:
                    a = []
                info['trans'] = a
                info['trade'] = one_trade
                info['detail'] = []
                for order_info in one_trade.merge_orders.filter(
                        sys_status=pcfg.IN_EFFECT):
                    sum = {}
                    sum['order'] = order_info
                    try:
                        product_info = Product.objects.get(
                            outer_id=order_info.outer_id)
                    except:
                        product_info = []
                    sum['product'] = product_info
                    info['detail'].append(sum)
                rec1.append(info)
            if len(rec1) > 0:
                return render(request, 'trades/order_detail.html',
                              {'info': rec1,
                               'time': today,
                               'number': number,
                               'product': product,
                               'status': status})

        if number == "":
            rec1 = []
        else:
            trade_info = MergeTrade.objects.filter(Q(
                receiver_mobile=number) | Q(tid=number) | Q(
                out_sid=number)).order_by("pay_time")
            if status:
                if status == u'1':
                    trade_info = trade_info.filter(
                        status__in=ORDER_NOT_SEND_STATUS)
                elif status == u'2':
                    trade_info = trade_info.filter(status__in=ORDER_SEND_STATUS)
            for item in trade_info:
                info = {}
                try:
                    # a = getLogisticTrace(item.out_sid, item.logistics_company.code)
                    a = []
                except:
                    a = []
                info['trans'] = a
                info['trade'] = item
                info['detail'] = []
                for order_info in item.merge_orders.filter(
                        sys_status=pcfg.IN_EFFECT):
                    sum = {}
                    sum['order'] = order_info
                    try:
                        product_info = Product.objects.get(
                            outer_id=order_info.outer_id)
                    except:
                        product_info = []
                    sum['product'] = product_info
                    info['detail'].append(sum)
                rec1.append(info)
            return render(request, 'trades/order_detail.html',
                          {'info': rec1,
                           'time': today,
                           'number': number,
                           'product': product,
                           'status': status})
    else:
        rec1 = []

    return render(request, 'trades/order_detail.html', {'info': rec1,
                                                        'time': today})

def search_package_sku_item(request):
    package_pid = request.REQUEST.get("package_pid",None)
    print package_pid
    try:
        package_sku_item = PackageSkuItem.objects.get(package_order_pid = package_pid)
        print package_sku_item.sale_order_id
        package_sku_item_oid = SaleOrder.objects.get(id = package_sku_item.sale_order_id).oid
        print package_sku_item_oid
        package_sku_item = {package_sku_item}
        shishi = {"a" : 1, "b" : 2}
        return HttpResponse(json.dumps({"res" : True,"data": [shishi],"desc":""}))
    except Exception,msg:
        print "包裹号不存在或包裹号不唯一"
        print msg
        return HttpResponse(json.dumps({"res" : False,"data": ["包裹号不存在或包裹号不唯一"],"desc":""}))
1
def manybeizhu(request):
    return render(request, 'trades/manybeizhu.html')


def beizhu(request):
    user_id = request.user.id
    content = request.REQUEST
    a = content.get("a", None)
    c = content.get("b", None)
    tid_list = a.split('\n')
    tids = []
    for i in tid_list:
        tids.append(i.strip())
    not_handler = []
    muti_handler = []
    for tid in tids:
        try:
            merge_trade = MergeTrade.objects.get(tid=tid)
        except MergeTrade.DoesNotExist:
            not_handler.append(tid)
            continue
        except MergeOrder.MultipleObjectsReturned:
            muti_handler.append(tid)
            continue
        else:
            merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
            merge_trade.sys_memo = merge_trade.sys_memo + c
            merge_trade.save()
            MergeTrade.objects.filter(id=merge_trade.id, sys_status=pcfg.WAIT_PREPARE_SEND_STATUS, out_sid='') \
                .update(sys_status=pcfg.WAIT_AUDIT_STATUS)  # 切换到＂等待人工审核状态＂
            log_action(user_id, merge_trade, CHANGE, u'系统备注:%s' % c)
    return HttpResponse(
        json.dumps({'code': 0,
                    'not_handler': not_handler,
                    "muti_handler": muti_handler}),
        content_type="application/json")


def test(request):
    return render(request, 'trades/test.html')


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def select_Stock(request):
    if 'tid' in request.POST and 'stock' in request.POST:
        tid = request.REQUEST.get('tid')
        stock = request.REQUEST.get('stock')
        try:
            megobj = MergeTrade.objects.get(id=tid)
        except Exception:
            return HttpResponse('error')
        if str(stock) is '0':  # 表示缺货
            megobj.has_out_stock = False
            megobj.save()
        elif str(stock) is '1':
            megobj.has_out_stock = True
            megobj.save()
        return HttpResponse('ok')
    else:
        return HttpResponse('error')


class DirtyOrderListAPIView(APIView):
    def get(self, request):
        # mapping
        from .models import TRADE_TYPE, SYS_TRADE_STATUS
        trade_type_mapping = dict(TRADE_TYPE)
        trade_sys_status_mapping = dict(SYS_TRADE_STATUS)
        status_mapping = dict([(0, '待清洗'), (1, '已处理')])

        threshold_datetime = datetime.datetime(2016, 1, 1)
        items = []
        trade_ids = set()
        for order in DirtyMergeOrder.objects.all().order_by('-id'):
            trade_ids.add(order.merge_trade.id)
            items.append({
                'order_id': order.id,
                'order_sn': order.oid,
                'trade_id': order.merge_trade.id,
                'trade_sn': order.merge_trade.tid,
                'order_type': trade_type_mapping.get(
                    order.merge_trade.type) or '未知',
                'product_name': order.title,
                'product_outer_id': order.outer_id,
                'num': order.num,
                'sku_properties_name': order.sku_properties_name,
                'payment': round(order.payment, 2),
                'payment_time': {
                    'display': order.pay_time.strftime('%Y%m%d %H:%M:%S'),
                    'timestamp': time.mktime(order.pay_time.timetuple())
                },
                'created_time': {
                    'display': order.created.strftime('%Y%m%d %H:%M:%S'),
                    'timestamp': time.mktime(order.created.timetuple())
                },
                'sys_status': trade_sys_status_mapping.get(
                    order.merge_trade.sys_status) or '未知',
                'receiver_name': order.merge_trade.receiver_name or '未知',
                'receiver_address': '%s%s%s%s' % (
                    order.merge_trade.receiver_state,
                    order.merge_trade.receiver_city,
                    order.merge_trade.receiver_district,
                    order.merge_trade.receiver_address),
                'receiver_mobile': order.merge_trade.receiver_mobile,
                'sys_memo': order.merge_trade.sys_memo
            })

        trades = {}
        for trade in MergeTrade.objects.filter(pk__in=list(trade_ids)):
            trades[trade.id] = trade_sys_status_mapping.get(
                trade.sys_status) or '未知'

        for item in items:
            item['old_sys_status'] = trades.get(item['trade_id']) or '未知'
        return Response({'data': items})


class DirtyOrderListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = 'trades/dirty_orders.html'

    def get(self, request):
        return Response({})


class DirtyOrderViewSet(viewsets.GenericViewSet):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = 'trades/dirty_orders2.html'

    def list(self, request, format='json'):
        from .models import TRADE_TYPE, SYS_TRADE_STATUS
        pay_time_start, pay_time_end = None, None
        form = forms.PayTimeRangeForm(request.GET)

        if form.is_valid() and form.cleaned_attrs.pay_time_start and form.cleaned_attrs.pay_time_end:
            pay_time_start = datetime.datetime.combine(form.cleaned_attrs.pay_time_start, datetime.time.min)
            pay_time_end = datetime.datetime.combine(form.cleaned_attrs.pay_time_end, datetime.time.max)
        if not re.search(r'application/json', request.META['HTTP_ACCEPT']):
            return Response({'form': form.json})

        trade_type_mapping = dict(TRADE_TYPE)
        trade_sys_status_mapping = dict(SYS_TRADE_STATUS)

        orders = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT)

        if pay_time_start and pay_time_end and pay_time_start <= pay_time_end:
            orders = orders.filter(pay_time__gte=pay_time_start, pay_time__lte=pay_time_end)

        items = []
        now = datetime.datetime.now()
        for order in orders:
            if not order.pay_time:
                continue
            items.append({
                'order_id': order.id,
                'order_sn': order.oid,
                'trade_id': order.merge_trade.id,
                'trade_sn': order.merge_trade.tid,
                'order_type': trade_type_mapping.get(
                    order.merge_trade.type) or '未知',
                'product_name': order.title,
                'product_outer_id': order.outer_id,
                'num': order.num,
                'sku_properties_name': order.sku_properties_name,
                'payment': round(order.payment, 2),
                'payment_date': {
                    'display': order.pay_time.strftime('%Y-%m-%d'),
                    'timestamp': time.mktime(order.pay_time.timetuple()),
                    'up_to_today': (now - order.pay_time).days
                },
                'payment_time': order.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
                'sys_status': trade_sys_status_mapping.get(
                    order.merge_trade.sys_status) or '未知',
                'receiver_name': order.merge_trade.receiver_name or '未知',
                'receiver_address': '%s%s%s%s' % (
                    order.merge_trade.receiver_state,
                    order.merge_trade.receiver_city,
                    order.merge_trade.receiver_district,
                    order.merge_trade.receiver_address),
                'receiver_mobile': order.merge_trade.receiver_mobile,
                'sys_memo': order.merge_trade.sys_memo
            })
        return Response({'data': items})
