# coding: utf-8
import cStringIO as StringIO
import datetime
import logging
import re
from django.db.models import Q, Sum
from django.forms.models import model_to_dict
from shopback import paramconfig as pcfg
from shopback.base.new_renders import new_BaseJSONRenderer
from shopback.logistics.models import LogisticsCompany
from shopback.trades.models import PackageSkuItem, PackageOrder, SYS_TRADE_STATUS, TAOBAO_TRADE_STATUS
from shopback.trades import serializers
from shopback.warehouse.renderers import ReviewOrderRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from shopapp.smsmgr.tasks import task_notify_package_post
from flashsale.pay.models import SaleOrder
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
        for package_order in PackageOrder.objects.filter(pid__in=package_order_ids.split(','), is_locked=True):
            package_order.is_express_print = False
            package_order.is_picking_print = False
            package_order.out_sid = ''
            package_order.save()
        return Response({'isSuccess': True})

    get = post


class PackagOrderExpressView(APIView):
    """ 订单打单 """

    def post(self, request, *args, **kwargs):
        # def setOutSid(package_order_id, out_sid, is_qrcode=False, qrcode_msg=''):
        content = request.REQUEST
        package_order_id = content.get('package_order_id')
        out_sid = content.get('out_sid', '')
        is_qrcode = content.get('is_qrcode', False)
        qrcode_msg = content.get('qrcode_msg', '')

        PackageOrder.objects.filter(pid=package_order_id).update(out_sid=out_sid, is_qrcode=is_qrcode,
                                                                 qrcode_msg=qrcode_msg)
        package_order = PackageOrder.objects.get(pid=package_order_id)
        from shopback.trades.models import MergeOrder
        for package_sku_item in PackageSkuItem.objects.filter(package_order_id=package_order.id, assign_status=1):
            MergeOrder.objects.filter(sale_order_id=package_sku_item.sale_order_id).update(sys_status=MergeOrder.DELETE)
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

    def get_item_from_package(self, package):
        order_items = []
        for order in package.package_sku_items.filter(assign_status=1):
            product_sku = order.product_sku
            product = order.product_sku.product
            barcode = product_sku and product_sku.BARCODE or product.BARCODE
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
            package = PackageOrder.objects.get(
                out_sid=package_id,
                sys_status=PackageOrder.WAIT_CHECK_BARCODE_STATUS)
        except PackageOrder.DoesNotExist:
            return Response(u'运单号未找到订单')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'结果返回多个订单')
        order_items = self.get_item_from_package(package)

        return Response({'package_no': package.out_sid,
                         'trade_id': package.pid,
                         'order_items': order_items})

    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_id = content.get('package_no', '').strip()
        if not package_id:
            return Response(u'单号不能为空')
        package_id = self.parsePackageNo(package_id)
        try:
            package_order = PackageOrder.objects.get(
                out_sid=package_id,
                sys_status=PackageOrder.WAIT_CHECK_BARCODE_STATUS)
        except PackageOrder.DoesNotExist:
            return Response(u'单号未找到')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'单号返回多个订单')
        if not package_order.is_picking_print:
            return Response(u'需重打发货单')
        if not package_order.is_express_print:
            return Response(u'需重打物流单')
        if not PackageScanCheckView.check_address_right(package_order):
            return Response(u'地址错误不予放行')
        oids = [p.oid for p in package_order.package_sku_items.filter(assign_status=1)]
        for s in SaleOrder.objects.filter(oid__in=oids):
            if not s.is_pending():
                logger.error(u'有订单已被取消仍要求发货:' + str(s.id))
                return Response(u'有订单已被取消：' + str(s.id))
        package_order.sys_status = PackageOrder.WAIT_SCAN_WEIGHT_STATUS
        package_order.scanner = request.user.username
        package_order.save()
        return Response({'isSuccess': True})

    @staticmethod
    def check_address_right(package_order):
        from flashsale.pay.models import SaleTrade
        from shopback.trades.models.package import get_sale_trade_address_dict, get_package_address_dict
        try:
            for item in package_order.package_sku_items.all():
                tid = item.sale_trade_id
                trade = SaleTrade.objects.get(tid=tid)
                if get_sale_trade_address_dict(trade) != get_package_address_dict(package_order):
                    logger.error(u'地址错误:' + str(package_order.pid) + '|' + tid)
                    return False
            return True
        except:
            return False

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
                out_sid=package_id,
                sys_status=PackageOrder.WAIT_SCAN_WEIGHT_STATUS)
        except PackageOrder.DoesNotExist:
            return Response(u'运单号未找到订单或被拦截')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'运单号返回多个订单')

        return Response({'package_no': package_id,
                         'trade_id': package_order.pid,
                         'seller_nick': package_order.seller.nick,
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
        package_weight = content.get('package_weight', '').strip()
        if not out_sid:
            return Response(u'包裹运单号不能为空')
        try:
            if float(package_weight) > 100000:
                return Response(u'重量超过100千克')
        except:
            return Response(u'重量异常:%s' % package_weight)
        try:
            package = PackageOrder.objects.get(out_sid=out_sid,
                    sys_status=PackageOrder.WAIT_SCAN_WEIGHT_STATUS)
        except PackageOrder.DoesNotExist:
            return Response(u'运单号未找到订单')
        except PackageOrder.MultipleObjectsReturned:
            return Response(u'结果返回多个订单')
        if not package.is_picking_print:
            return Response(u'需重打发货单')
        if not package.is_express_print:
            return Response(u'需重打物流单')
        package.weight = package_weight
        package.weighter = request.user.username
        package.save()
        package.finish_scan_weight()
        task_notify_package_post.delay(package)
        return Response({'isSuccess': True})


class PackagePrintPostView(APIView):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        package_order_ids = package_order_ids.split(',')
        package_orders = PackageOrder.objects.filter(pid__in=package_order_ids,
                                                     status=PackageOrder.WAIT_PREPARE_SEND_STATUS, is_picking_print=True,
                                                     is_express_print=True)
        num = package_orders.count()
        if num != len(package_order_ids):
            return Response({'isSuccess': False, 'response_error': u'部分包裹不存在或者未准备好'})
        for package_order in package_orders:
            package_order.status = PackageOrder.WAIT_CHECK_BARCODE_STATUS
            package_order.save()
        return Response({'isSuccess': True})
    get = post


class PackagePrintExpressView(APIView):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        package_order_ids = package_order_ids.split(',')
        package_orders = PackageOrder.objects.filter(pid__in=package_order_ids)
        package_orders.update(is_express_print=True)
        return Response({'isSuccess': True})
    get = post


class PackagePrintPickingView(APIView):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_ids = content.get('package_order_ids')
        package_order_ids = package_order_ids.split(',')
        package_orders = PackageOrder.objects.filter(pid__in=package_order_ids)
        package_orders.update(is_picking_print=True)
        return Response({'isSuccess': True})
    get = post


class PackageReviewView(APIView):
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
            package_order = PackageOrder.objects.get(pid=id)
        except PackageOrder.DoesNotExist:
            return Response('该订单不存在'.decode('utf8'))

        logistics = serializers.LogisticsCompanySerializer(
            LogisticsCompany.objects.filter(status=True),
            many=True).data
        return Response({"object": {'package_order': package_order,
                                    'logistics': logistics}})


class PackageClearRedoView(APIView):
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        package_order_pid = content.get('package_order_pid')
        package_order = PackageOrder.objects.get(pid=package_order_pid)
        package_order.redo_sign = False
        package_order.save(update_fields=['redo_sign'])
        return Response({'isSuccess': True})
    get = post