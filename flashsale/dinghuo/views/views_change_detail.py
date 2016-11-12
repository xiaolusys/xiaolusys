# coding: utf-8
__author__ = 'yann'

from cStringIO import StringIO
import datetime
import decimal
import io
import logging
import json
import xlsxwriter
import urllib

from django.db.models import F
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

import common.utils
from common.utils import CSVUnicodeWriter
from core.options import log_action, CHANGE, ADDITION
from flashsale.dinghuo.models import OrderDetail, OrderList, OrderDraft, OrderDetailInBoundDetail, InBoundDetail, \
    InBound, ReturnGoods
from .. import functions
from shopback.items.models import Product, ProductSku, ProductStock
from shopback.warehouse.constants import WARE_THIRD
from supplychain.supplier.models import SaleProduct, SaleSupplier
from flashsale.finance.models import Bill, BillRelation  # 财务记录model
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Q
from shopback.trades.models import PackageOrder, PackageSkuItem
from shopback.warehouse.models import StockAdjust
from rest_framework import exceptions
import logging

logger = logging.getLogger(__name__)


class ChangeDetailView(View):
    @staticmethod
    def get(request, order_detail_id):
        order_list = OrderList.objects.get(id=order_detail_id)
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id, buy_quantity__gt=0).order_by(
            'outer_id')
        flag_of_status = False
        flag_of_question = False
        flag_of_sample = False
        order_list_list = []
        product_links = []
        for order in order_details:
            product = Product.objects.get(id=order.product_id)
            order_dict = model_to_dict(order)
            order_dict['pic_path'] = product.pic_path
            product_sku = ProductSku.objects.get(id=order.chichu_id)
            order_dict['supplier_outer_id'] = ''
            order_dict['wait_post_num'] = product_sku.wait_post_num
            order_dict['not_assign_num'] = product_sku.not_assign_num
            order_dict['get_all_inferior_quantity'] = product_sku.real_inferior_quantity
            order_dict['get_receive_status'] = order.get_receive_status()
            if product.sale_product:
                try:
                    saleproduct = SaleProduct.objects.get(
                        id=product.sale_product)
                    order_dict['product_link'] = saleproduct.product_link or ''
                    order_dict['supplier_outer_id'] = saleproduct.supplier_sku or '#'
                    order_dict['memo'] = saleproduct.memo if saleproduct.orderlist_show_memo else ''
                except:
                    pass
            order_list_list.append(order_dict)

        def _sort(x):
            _M = {
                'XS': 1001,
                'S': 1002,
                'M': 1003,
                'L': 1004,
                'XL': 1005,
                'XXL': 1006,
                '3XL': 1007,
                '4XL': 1008,
                u'均码': 9999
            }
            chicun = x.get('product_chicun') or ''
            try:
                w = float(chicun)
            except:
                w = _M.get(chicun) or chicun
            return x.get('product_id') or 0, w

        order_list_list = sorted(order_list_list, key=_sort)

        product_link = product_links[0] if product_links else ''

        if order_list.status == OrderList.SUBMITTING:
            flag_of_status = True
        elif order_list.status in [OrderList.QUESTION, OrderList.CIPIN, OrderList.QUESTION_OF_QUANTITY,
                                   OrderList.TO_BE_PAID, OrderList.TO_PAY, OrderList.CLOSED]:
            flag_of_question = True
        if order_list.status == u'7':
            flag_of_sample = True
        buyer_name = ''
        if order_list.buyer_id:
            buyer_name = '%s%s' % (order_list.buyer.last_name, order_list.buyer.first_name)
            buyer_name = buyer_name or order_list.buyer.username

        inbounddetail_ids = set()
        for record in OrderDetailInBoundDetail.objects.filter(orderdetail_id__in=[x['id'] for x in order_list_list],
                                                              status=OrderDetailInBoundDetail.NORMAL):
            inbounddetail_ids.add(record.inbounddetail_id)
        inbound_ids = set()
        for inbounddetail in InBoundDetail.objects.filter(id__in=list(inbounddetail_ids)):
            inbound_ids.add(inbounddetail.inbound_id)
        inbound_dicts = []
        # for inbound in InBound.objects.filter(id__in=list(inbound_ids), status__in=[InBound.COMPLETED, InBound.WAIT_CHECK, InBound.PENDING]).order_by('id'):
        for inbound in order_list.get_inbounds():
            inbound_dicts.append({
                'id': inbound.id,
                'memo': inbound.memo,
                'info': inbound.get_easy_info()
            })
        return render_to_response("dinghuo/changedetail.html",
                                  {"orderlist": order_list,
                                   "flagofstatus": flag_of_status,
                                   "flagofquestion": flag_of_question,
                                   "flag_of_sample": flag_of_sample,
                                   "orderdetails": order_list_list,
                                   'product_link': product_link, 'buyer_name': buyer_name,
                                   'inbounds': inbound_dicts},
                                  context_instance=RequestContext(request))

    @staticmethod
    def post(request, order_detail_id):
        post = request.POST
        order_list = OrderList.objects.get(id=order_detail_id)
        status = post.get("status", "").strip()
        remarks = post.get("remarks", "").strip()
        if len(status) > 0 and len(remarks) > 0:
            if status == OrderList.COMPLETED:
                order_list.completed_time = datetime.datetime.now()
                if order_list.is_postpay:
                    order_list.status = OrderList.TO_PAY
                else:
                    order_list.status = OrderList.CLOSED
            else:
                order_list.status = status
            order_list.note = order_list.note + "\n" + "-->" + datetime.datetime.now(
            ).strftime('%m月%d %H:%M') + request.user.username + ":" + remarks
            order_list.save()
            log_action(request.user.id, order_list, CHANGE,
                       u'%s 订货单' % (u'添加备注'))
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id, buy_quantity__gt=0)
        order_list_list = []
        for order in order_details:
            order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity
            order.save()
            product = Product.objects.get(id=order.product_id)
            order_dict = model_to_dict(order)
            order_dict['pic_path'] = product.pic_path
            product_sku = ProductSku.objects.get(id=order.chichu_id)
            order_dict['wait_post_num'] = product_sku.wait_post_num
            order_dict['not_assign_num'] = product_sku.not_assign_num
            order_dict['supplier_outer_id'] = ''
            if product.sale_product:
                try:
                    saleproduct = SaleProduct.objects.get(
                        id=product.sale_product)
                    order_dict['product_link'] = saleproduct.product_link or ''
                    order_dict['supplier_outer_id'] = saleproduct.supplier_sku or '#'
                    order_dict['memo'] = saleproduct.memo if saleproduct.orderlist_show_memo else ''
                except:
                    pass
            order_list_list.append(order_dict)

        def _sort(x):
            _M = {
                'XS': 1001,
                'S': 1002,
                'M': 1003,
                'L': 1004,
                'XL': 1005,
                'XXL': 1006,
                '3XL': 1007,
                '4XL': 1008,
                u'均码': 9999
            }
            chicun = x.get('product_chicun') or ''
            try:
                w = float(chicun)
            except:
                w = _M.get(chicun) or chicun
            return x.get('product_id') or 0, w

        order_list_list = sorted(order_list_list, key=_sort)

        if order_list.status == "草稿":
            flag_of_status = True
        else:
            flag_of_status = False
        flag_of_sample = False
        if order_list.status == u'7':
            flag_of_sample = True
        # 是否到货商品关联订单
        flag_of_question = False
        if order_list.status in [OrderList.QUESTION, OrderList.CIPIN, OrderList.QUESTION_OF_QUANTITY,
                                 OrderList.TO_BE_PAID, OrderList.TO_PAY, OrderList.CLOSED]:
            flag_of_question = True

        try:
            from shopback.items.tasks import releaseProductTradesTask
            distinct_pids = [
                p['product_id']
                for p in order_details.values('product_id').distinct()
                ]
            outer_ids = [p['outer_id']
                         for p in Product.objects.filter(
                    id__in=distinct_pids).values('outer_id')]
            releaseProductTradesTask.delay(outer_ids)
        except Exception, exc:
            logger = logging.getLogger('django.request')
            logger.error(exc.message, exc_info=True)

        return render_to_response("dinghuo/changedetail.html",
                                  {"orderlist": order_list,
                                   "flagofstatus": flag_of_status,
                                   'flagofquestion': flag_of_question,
                                   "orderdetails": order_list_list,
                                   "flag_of_sample": flag_of_sample},
                                  context_instance=RequestContext(request))


class AutoNewOrder(View):
    @staticmethod
    def get(request, order_list_id):
        user = request.user
        functions.save_draft_from_detail_id(order_list_id, user)
        all_drafts = OrderDraft.objects.all().filter(buyer_name=user)
        return render_to_response("dinghuo/shengchengorder.html",
                                  {"OrderDraft": all_drafts},
                                  context_instance=RequestContext(request))


def update_dinghuo_part_information(request):
    content = request.POST
    dinghuo_id = int(content.get("dinghuo_id", None))
    express_company = content.get("express_company_id", None)
    express_no = content.get("express_no", None)
    pay_way = int(content.get("pay_way", None))
    supplier_name = content.get("supplier_name", None)
    try:
        item = OrderList.objects.get(id=dinghuo_id)
        item.express_company = express_company
        item.express_no = express_no
        item.supplier_name = supplier_name
        item.bill_method = pay_way
        item.save()
        sale_supplier = item.supplier
        if not sale_supplier.product_link:
            sale_supplier.product_link = supplier_name
            sale_supplier.save()
    except Exception, msg:
        print msg
        return HttpResponse(False)
    return HttpResponse(True)


def generate_return_goods(request):
    supplier = request.GET.get("supplier", None)
    stype = request.GET.get("type", 0)
    try:
        ss = SaleSupplier.objects.get(Q(supplier_name=supplier) | Q(id=supplier))
    except Exception, msg:
        return HttpResponse(json.dumps({"res": False, "data": [], "desc": "供应商不存在"}))
    try:
        rg = ReturnGoods.objects.create(supplier=ss, type=stype)
        rg.save()
        return HttpResponse(json.dumps({"res": True, "data": [rg.id], "desc": ""}))
    except Exception, msg:
        return HttpResponse(json.dumps({"res": False, "data": [], "desc": "创建退货单失败"}))


@csrf_exempt
def change_inferior_num(request):
    if not request.user.has_perm('dinghuo.change_orderdetail_quantity'):
        return HttpResponse(json.dumps({'error': True, 'msg': "权限不足"}), content_type='application/json')

    post = request.POST
    flag = post['flag']
    order_detail_id = post["order_detail_id"].strip()
    order_detail = OrderDetail.objects.get(id=order_detail_id)
    order_list = OrderList.objects.get(id=order_detail.orderlist_id)
    if flag == "0":
        if order_detail.inferior_quantity == 0:
            return HttpResponse("false")
        OrderDetail.objects.filter(id=order_detail_id).update(
            inferior_quantity=F('inferior_quantity') - 1)
        OrderDetail.objects.filter(id=order_detail_id).update(
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity'))
        OrderDetail.objects.filter(id=order_detail_id).update(
            arrival_quantity=F('arrival_quantity') + 1)
        ProductStock.add_order_detail(order_detail, 1)
        log_action(request.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'次品减一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(request.user.id, order_detail, CHANGE, u'%s' % (u'次品减一'))
        return HttpResponse("OK")
    elif flag == "1":
        OrderDetail.objects.filter(id=order_detail_id).update(
            inferior_quantity=F('inferior_quantity') + 1)
        OrderDetail.objects.filter(id=order_detail_id).update(
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity'))
        OrderDetail.objects.filter(id=order_detail_id).update(
            arrival_quantity=F('arrival_quantity') - 1)
        ProductStock.add_order_detail(order_detail, -1)
        log_action(request.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'次品加一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(request.user.id, order_detail, CHANGE, u'%s' % (u'次品加一'))
        return HttpResponse("OK")
    return HttpResponse("false")


class ChangeDetailExportView(View):
    @staticmethod
    def get_old(request, order_list_id):
        headers = [u'商品编码', u'供应商编码', u'商品名称', u'规格', u'购买数量', u'买入价格', u'单项价格',
                   u'已入库数', u'次品数']
        order_list = OrderList.objects.get(id=order_list_id)

        order_details = OrderDetail.objects.filter(orderlist_id=order_list_id, buy_quantity__gt=0)
        items = []
        for o in order_details:
            sku = ProductSku.objects.get(id=o.chichu_id)
            product = sku.product
            item = model_to_dict(o)
            item['pic_path'] = product.pic_path
            item['supplier_outer_id'] = sku.get_supplier_outerid()
            if product.sale_product:
                try:
                    saleproduct = SaleProduct.objects.get(id=product.sale_product)
                    item['memo'] = saleproduct.memo if saleproduct.orderlist_show_memo else ''
                except:
                    pass
            items.append(item)

        items = [map(unicode,
                     [i['outer_id'], i['supplier_outer_id'], i['product_name'],
                      i['product_chicun'], i['buy_quantity'],
                      i['buy_unitprice'], i['total_price'],
                      i['arrival_quantity'], i['inferior_quantity']])
                 for i in items]
        sum_of_total_price = round(sum(map(lambda x: float(x[-3]), items)), 2)
        items.append([''] * 5 + [u'总计', unicode(sum_of_total_price)] + [''] * 2)
        items.insert(0, headers)
        buff = StringIO()
        is_windows = request.META['HTTP_USER_AGENT'].lower().find(
            'windows') > -1
        writer = CSVUnicodeWriter(buff,
                                  encoding=is_windows and 'gbk' or 'utf-8')
        writer.writerows(items)
        response = HttpResponse(buff.getvalue(),
                                content_type='application/octet-stream')
        response[
            'Content-Disposition'] = 'attachment;filename=dinghuodetail-%s.csv' % order_list_id
        return response

    @staticmethod
    def get(request, order_detail_id):
        order_detail_id = int(order_detail_id)
        now = datetime.datetime.now()

        buff = StringIO()
        workbook = xlsxwriter.Workbook(buff)
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '0.00'})
        text_wrap = workbook.add_format({'text_wrap': True})

        image_width = 25
        image_height = 125

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('F:F', image_width)

        worksheet.write('A1', '供应商名称:', bold)
        worksheet.write('A2', '供应商账号:', bold)
        worksheet.write('A3', '供应商姓名:', bold)
        worksheet.write('A4', '供应商联系方式:', bold)

        order_list = OrderList.objects.get(id=order_detail_id)
        buyer_name = order_list.buyer_name or ''

        supplier_name = ''
        supplier_contactor = ''
        supplier_contact = ''
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id, buy_quantity__gt=0).order_by(
            'outer_id')

        receiver_address = '广州市白云区太和镇永兴村龙归路口悦博大酒店对面龙门公寓3楼' if order_list.p_district == '3' else \
            '上海市佘山镇吉业路245号5号楼'
        receiver_name = '小鹿美美%d号工作人员' % order_list.id
        receiver_contact = '15023333762' if order_list.p_district == '3' else '021-37698479, 15026869609'
        if order_details:
            supplier = None
            for order_detail in order_details:
                try:
                    product = Product.objects.get(pk=order_detail.product_id)
                    sale_product = SaleProduct.objects.get(
                        pk=product.sale_product)
                    supplier = sale_product.sale_supplier
                except:
                    continue
            if supplier:
                supplier_name = supplier.supplier_name
                supplier_contactor = supplier.contact
                supplier_contact = supplier.mobile or supplier.phone or supplier.email or ''
        worksheet.write('B1', supplier_name)
        worksheet.write('B3', supplier_contactor)
        worksheet.write('B4', supplier_contact)

        products = {}
        for product in Product.objects.filter(
                pk__in=[order_detail.product_id for order_detail in
                        order_details]):
            products[product.id] = {
                'sale_product_id': product.sale_product,
                'pic_path':
                    ('%s?imageMogr2/thumbnail/560/crop/560x480/format/jpg' %
                     common.utils.url_utf8_quote(product.pic_path.encode('utf-8')))
                    if product.pic_path else ''
            }

        sale_products = {}
        for sale_product in SaleProduct.objects.filter(pk__in=[product[
                                                                   'sale_product_id'] for product in
                                                               products.values()]):
            sale_products[sale_product.id] = {
                'product_link': sale_product.product_link,
                'supplier_sku': sale_product.supplier_sku or '',
                'memo': sale_product.memo if sale_product.orderlist_show_memo else ''
            }

        """
        skus = {}
        for sku in ProductSku.objects.filter(
                pk__in=[order_detail.chichu_id for order_detail in order_details
                        ]):
            skus[sku.id] = sku.supplier_sku
        """

        def _parse_name(product_name):
            name, color = ('-',) * 2
            parts = product_name.rsplit('/', 1)
            if len(parts) > 1:
                name, color = parts[:2]
            elif len(parts) == 1:
                name = parts[0]
            return name, color

        worksheet.write('A6', '商品名称', bold)
        worksheet.write('B6', '产品货号', bold)
        worksheet.write('C6', '选品备注', bold)
        worksheet.write('D6', '颜色', bold)
        worksheet.write('E6', '规格', bold)
        worksheet.write('F6', '图片', bold)
        worksheet.write('G6', '购买数量', bold)
        worksheet.write('H6', '入库数量', bold)
        worksheet.write('I6', '次品数量', bold)
        worksheet.write('J6', '单项价格', bold)
        worksheet.write('K6', '总价', bold)

        row = 6
        all_price = decimal.Decimal('0')
        all_quantity = 0
        for order_detail in order_details:
            name, color = _parse_name(order_detail.product_name)
            product = products.get(int(order_detail.product_id)) or {}
            pic_path = product.get('pic_path') or ''
            sale_product_dict = sale_products.get(product.get(
                'sale_product_id')) or {}
            product_link = sale_product_dict.get('product_link') or ''
            sku_outer_id = sale_product_dict.get('supplier_sku') or ''
            memo = sale_product_dict.get('memo') or ''

            worksheet.write(row, 0, name)
            worksheet.write(row, 1, sku_outer_id)
            worksheet.write(row, 2, memo, text_wrap)
            worksheet.write(row, 3, color)
            worksheet.write(row, 4, order_detail.product_chicun)
            # worksheet.write(row, 5, pic_path)

            if pic_path:
                opt = {'image_data':
                           io.BytesIO(urllib.urlopen(pic_path).read()),
                       'x_scale': 0.25,
                       'y_scale': 0.25}
                if product_link:
                    opt['url'] = product_link
                worksheet.set_row(row, image_height)
                worksheet.insert_image(row, 5, pic_path, opt)

            worksheet.write(row, 6, order_detail.buy_quantity)
            worksheet.write(row, 7, order_detail.arrival_quantity)
            worksheet.write(row, 8, order_detail.inferior_quantity)
            worksheet.write(row, 9, order_detail.buy_unitprice, money)
            worksheet.write(row, 10, order_detail.total_price, money)
            worksheet.write(row, 11, product_link)
            all_quantity += order_detail.buy_quantity
            all_price += decimal.Decimal(str(order_detail.total_price))
            row += 1

        worksheet.write(row, 5, '总数:', bold)
        worksheet.write(row, 6, all_quantity)
        worksheet.write(row, 9, '总计:', bold)
        worksheet.write(row, 10, order_list.order_amount, money)

        row += 1

        worksheet.write(row + 1, 0, '收货地址:', bold)
        worksheet.write(row + 2, 0, '联系人:', bold)
        worksheet.write(row + 3, 0, '联系电话:', bold)

        worksheet.write(row + 1, 1, receiver_address)
        worksheet.write(row + 2, 1, receiver_name)
        worksheet.write(row + 3, 1, receiver_contact)

        workbook.close()

        filename = '%s-%d.xlsx' % (order_list.created.strftime('%Y%m%d'), order_detail_id)
        response = HttpResponse(
            buff.getvalue(),
            content_type=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class DinghuoStatsExportView(View):
    @classmethod
    def get_status(cls, status):
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        status_display = status_mapping.get(status) or status
        buyer_status_display = '已完成' if status in \
                                        [OrderList.COMPLETED, OrderList.TO_BE_PAID, OrderList.CLOSED] else '未完成'
        return status_display, buyer_status_display

    def get(self, request):
        from common.utils import get_admin_name

        start_date = datetime.datetime.strptime(request.GET['start_date'], '%Y%m%d').date()
        end_date = datetime.datetime.strptime(request.GET['end_date'], '%Y%m%d').date()

        data = []
        for orderlist in OrderList.objects.filter(created__gte=start_date, created__lte=end_date).exclude(
                status=OrderList.ZUOFEI).order_by('id'):
            username = get_admin_name(orderlist.buyer)
            interval = (orderlist.updated - datetime.datetime.combine(orderlist.created, datetime.time.min)).days
            created_str = orderlist.created.strftime('%Y-%m-%d')
            updated_str = orderlist.updated.strftime('%Y-%m-%d %H:%M:%S')
            amount = orderlist.order_amount

            supplier_name = ''
            if orderlist.supplier_id and orderlist.supplier:
                supplier_name = orderlist.supplier.supplier_name

            num = 0
            product_ids = set()
            for orderdetail in orderlist.order_list.all():
                product_ids.add(orderdetail.product_id)
                num += orderdetail.buy_quantity
            status, buyer_status = self.get_status(orderlist.status)

            data.append((
                orderlist.id,
                username,
                status,
                buyer_status,
                created_str,
                updated_str,
                interval,
                supplier_name,
                len(product_ids),
                num,
                amount
            ))

        buff = StringIO()
        workbook = xlsxwriter.Workbook(buff)
        worksheet = workbook.add_worksheet()
        worksheet.write('A1', '订货单ID')
        worksheet.write('B1', '负责人')
        worksheet.write('C1', '状态')
        worksheet.write('D1', '是否完成')
        worksheet.write('E1', '创建日期')
        worksheet.write('F1', '更新时间')
        worksheet.write('G1', '间隔天数')
        worksheet.write('H1', '供应商名')
        worksheet.write('I1', '款数')
        worksheet.write('J1', '件数')
        worksheet.write('K1', '总金额')

        i = 1
        for row in data:
            for j, cell in enumerate(row):
                worksheet.write(i, j, cell)
            i += 1
        workbook.close()

        filename = '%s-%s.xlsx' % (start_date.strftime('%y年%m月%d'), end_date.strftime('%y年%m月%d'))
        response = HttpResponse(
            buff.getvalue(),
            content_type=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response
