# coding: utf-8
import cStringIO as StringIO
import datetime
import json
import logging
import re
from shopback import paramconfig as pcfg
from shopback.base import log_action, ADDITION, CHANGE
from shopback.base.new_renders import new_BaseJSONRenderer
from shopback.items.models import Product
from shopback.logistics.models import LogisticsCompany
from shopback.trades.models import (MergeTrade, MergeOrder, PackageOrder)
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger('django.request')


class PackagOrderOperateView(APIView):
    """ 处理订单 """

    # def operate_package(self, package_order_id, operator):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        operator = content.get('operator', '')
        package_order_ids = package_order_ids.split(',')
        PackageOrder.objects.filter(pid__in=package_order_ids, is_locked=False).update(
            is_locked=True, operator=operator
        )
        # MergeTrade.sync_from_package(package_order)
        return Response({'isSuccess': True})

    get = post

    def revert_package(self, package_order_id):
        package_order = PackageOrder.objects.get(pid=package_order_id, is_locked=False)
        package_order.is_express_print = False
        package_order.is_picking_print = False
        package_order.out_sid = ''
        package_order.save()
        return Response({'isSuccess': True})

    def revert_packages(self, package_order_ids):
        package_order = PackageOrder.objects.get(pid=package_order_ids.split(','), is_locked=False)
        package_order.is_express_print = False
        package_order.is_picking_print = False
        package_order.out_sid = ''
        package_order.save()
        return Response({'isSuccess': True})


class PackagOrderExpressView(APIView):
    """ 订单打单 """

    def printYundaPdf(self, package_order_ids):
        PackageOrder.objects.filter(pid__in=package_order_ids.split(',')).update(is_express_print=True)
        return Response({'isSuccess': True})

    def post(self, request, *args, **kwargs):
        # def setOutSid(package_order_id, out_sid, is_qrcode=False, qrcode_msg=''):
        content = request.REQUEST
        package_order_id = content.get('package_order_id')
        out_sid = content.get('out_sid', '')
        is_qrcode = content.get('is_qrcode', False)
        qrcode_msg = content.get('qrcode_msg', '')

        PackageOrder.objects.filter(pid=package_order_id).update(out_sid=out_sid, is_qrcode=is_qrcode,
                                                                qrcode_msg=qrcode_msg)
        return Response({'isSuccess': True})

    get = post

    def printPicking(self, package_order_id):
        PackageOrder.objects.filter(pid=package_order_id).update(is_picking_print=True)
        return Response({'isSuccess': True})


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


from flashsale.dinghuo.tasks import task_stats_paytopack


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

        log_action(mt.user.user.id, mt, CHANGE, u'扫描称重')

        mo = mt.normal_orders
        for entry in mo:
            pay_date = entry.pay_time.date()
            sku_num = 1  # not entry.num, intentionally ignore sku_num effect
            time_delta = mt.weight_time - entry.pay_time
            total_days = sku_num * (time_delta.total_seconds() / 86400.0)

            task_stats_paytopack.s(pay_date, sku_num, total_days)()

        if mt.type == pcfg.SALE_TYPE:
            package = mt.get_package()
            mt.get_sale_orders().update(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
            if package:
                try:
                    package.finish(mt)
                    package.sync_merge_trade(mt)
                except Exception, exc:
                    logger.error(exc.message, exc_info=True)
        return Response({'isSuccess': True})
