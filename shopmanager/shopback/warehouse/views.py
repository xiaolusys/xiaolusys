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

    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        operator = content.get('operator', '')
        package_order_ids = package_order_ids.split(',')
        PackageOrder.objects.filter(pid__in=package_order_ids, is_locked=False).update(
            is_locked=True, operator=operator)
        return Response({'isSuccess': True})

    get = post


class PackagOrderRevertView(APIView):
    """ 处理订单 """

    # def revert_package(self, package_order_id):
    # package_order = PackageOrder.objects.get(pid=package_order_id, is_locked=False)
    # package_order.is_express_print = False
    # package_order.is_picking_print = False
    # package_order.out_sid = ''
    # package_order.save()
    # return Response({'isSuccess': True})
    # def revert_packages(self, package_order_ids):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        package_order = PackageOrder.objects.get(pid=package_order_ids.split(','), is_locked=False)
        package_order.is_express_print = False
        package_order.is_picking_print = False
        package_order.out_sid = ''
        package_order.save()
        return Response({'isSuccess': True})

    get = post


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
        package = PackageOrder.objects.get(pid=package_order_id)
        # MergeTrade.objects.filter
        # 同步mergeTrade与packageOrder
        from shopback.trades.models import sync_merge_trade_by_package_after_order_express
        sync_merge_trade_by_package_after_order_express(package)
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
        package_order_id = content.get('package_order_id', '').strip()
        if not package_order_id:
            return Response(u'单号不能为空')
        try:
            package_order = PackageOrder.objects.get(pid=package_order_id)
        except PackageOrder.DoesNotExist:
            return Response(u'单号未找到')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'单号返回多个订单')
        package_order.sys_status = pcfg.WAIT_SCAN_WEIGHT_STATUS
        package_order.scanner = request.user.username
        package_order.save()
        log_action(package_order.user.user.id, package_order, CHANGE, u'扫描验货')
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
            package_order = PackageOrder.objects.get(
                # id=package_order_id
                out_sid=package_id
            )
        except PackageOrder.DoesNotExist:
            return Response(u'运单号未找到订单或被拦截')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'运单号返回多个订单')

        return Response({'package_no': package_id,
                         'trade_id': package_order.id,
                         'seller_nick': package_order.user.nick,
                         'trade_type': package_order.get_type_display(),
                         'buyer_nick': package_order.buyer_nick,
                         'sys_status': package_order.get_sys_status_display(),
                         'company_name': package_order.logistics_company.name,
                         'receiver_mobile': package_order.receiver_mobile,
                         'receiver_name': package_order.receiver_name,
                         'receiver_state': package_order.receiver_state,
                         'receiver_city': package_order.receiver_city,
                         'receiver_district': package_order.receiver_district,
                         'receiver_address': package_order.receiver_address})

    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_no = content.get('package_no', '').strip()
        out_sid = self.parsePackageNo(package_no)
        # package_order_id = content.get('package_order_id', '').strip()
        package_weight = content.get('package_weight', '').strip()

        if not out_sid:
            return Response(u'包裹运单号不能为空')

        try:
            if float(package_weight) > 100000:
                return Response(u'重量超过100千克')
        except:
            return Response(u'重量异常:%s' % package_weight)

        # package_id = self.parsePackageNo(package_no)
        try:
            package = PackageOrder.objects.get(out_sid=out_sid)
        except PackageOrder.DoesNotExist:
            return Response(u'运单号未找到订单')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'结果返回多个订单')
        package.weight = package_weight
        package.sys_status = pcfg.FINISHED_STATUS
        package.weight_time = datetime.datetime.now()
        package.weighter = request.user.username
        package.save()
        package.finish_scan_weight()
        mo = package.sale_orders
        for entry in mo:
            pay_date = entry.pay_time.date()
            sku_num = 1  # not entry.num, intentionally ignore sku_num effect
            time_delta = package.weight_time - entry.pay_time
            total_days = sku_num * (time_delta.total_seconds() / 86400.0)
            task_stats_paytopack.s(pay_date, sku_num, total_days)()
        return Response({'isSuccess': True})


        # todo＠hy　回填单号


def package_order_print_pickle(request):
    content = request.REQUEST
    package_order_ids = content.get('package_order_ids')
    package_order_ids = package_order_ids.split(',')
    PackageOrder.objects.filter(pid__in=package_order_ids, status=PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                is_picking_print=True, is_express_print=True
                                ).update(status=PackageOrder.WAIT_CHECK_BARCODE_STATUS)
    return
