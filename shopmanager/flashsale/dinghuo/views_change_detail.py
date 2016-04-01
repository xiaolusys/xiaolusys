# coding: utf-8
__author__ = 'yann'

from cStringIO import StringIO
import datetime
import decimal
import io
import logging
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
from flashsale.dinghuo import log_action, CHANGE
from flashsale.dinghuo.models import OrderDetail, OrderList, orderdraft
import functions
from shopback.items.models import Product, ProductSku
from supplychain.supplier.models import SaleProduct, SaleSupplier


class ChangeDetailView(View):

    @staticmethod
    def get(request, order_detail_id):
        order_list = OrderList.objects.get(id=order_detail_id)
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)
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
            order_dict['supplier_outer_id'] = product_sku.outer_id
            order_dict['wait_post_num'] = product_sku.wait_post_num
            if product.sale_product:
                try:
                    saleproduct = SaleProduct.objects.get(
                        id=product.sale_product)
                    order_dict['product_link'] = saleproduct.product_link or ''
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
        if order_list.status == "草稿":
            flag_of_status = True
        elif order_list.status == u'有问题' or order_list.status == u'5' or order_list.status == u'6':
            flag_of_question = True
        if order_list.status == u'7':
            flag_of_sample = True
        buyer_name = ''
        if order_list.buyer:
            buyer_name = '%s%s' % (order_list.buyer.last_name, order_list.buyer.first_name)
            buyer_name = buyer_name or order_list.buyer.username
        return render_to_response("dinghuo/changedetail.html",
                                  {"orderlist": order_list,
                                   "flagofstatus": flag_of_status,
                                   "flagofquestion": flag_of_question,
                                   "flag_of_sample": flag_of_sample,
                                   "orderdetails": order_list_list,
                                   'product_link': product_link, 'buyer_name': buyer_name},
                                  context_instance=RequestContext(request))

    @staticmethod
    def post(request, order_detail_id):
        post = request.POST
        order_list = OrderList.objects.get(id=order_detail_id)
        status = post.get("status", "").strip()
        remarks = post.get("remarks", "").strip()
        if len(status) > 0 and len(remarks) > 0:
            if status == '已处理(需收款)':
                order_list.pay_status = '需收款'
            order_list.status = status
            order_list.note = order_list.note + "\n" + "-->" + datetime.datetime.now(
            ).strftime('%m月%d %H:%M') + request.user.username + ":" + remarks
            order_list.save()
            log_action(request.user.id, order_list, CHANGE,
                       u'%s 订货单' % (u'添加备注'))
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)
        order_list_list = []
        for order in order_details:
            order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity - order.inferior_quantity
            order.save()
            order_dict = model_to_dict(order)
            order_dict['pic_path'] = Product.objects.get(
                id=order.product_id).pic_path
            order_list_list.append(order_dict)
        if order_list.status == "草稿":
            flag_of_status = True
        else:
            flag_of_status = False
        flag_of_sample = False
        if order_list.status == u'7':
            flag_of_sample = True
        #是否到货商品关联订单
        try:
            from shopback.items.tasks import releaseProductTradesTask
            distinct_pids = [
                p['product_id']
                for p in order_details.values('product_id').distinct()
            ]
            outer_ids = [p['outer_id']
                         for p in Product.objects.filter(
                             id__in=distinct_pids).values('outer_id')]
            releaseProductTradesTask.s(outer_ids)()
        except Exception, exc:
            logger = logging.getLogger('django.request')
            logger.error(exc.message, exc_info=True)

        return render_to_response("dinghuo/changedetail.html",
                                  {"orderlist": order_list,
                                   "flagofstatus": flag_of_status,
                                   "orderdetails": order_list_list,
                                   "flag_of_sample": flag_of_sample},
                                  context_instance=RequestContext(request))


class AutoNewOrder(View):

    @staticmethod
    def get(request, order_list_id):
        user = request.user
        functions.save_draft_from_detail_id(order_list_id, user)
        all_drafts = orderdraft.objects.all().filter(buyer_name=user)
        return render_to_response("dinghuo/shengchengorder.html",
                                  {"orderdraft": all_drafts},
                                  context_instance=RequestContext(request))


@csrf_exempt
def change_inferior_num(request):
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
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity') - F(
                'inferior_quantity'))
        OrderDetail.objects.filter(id=order_detail_id).update(
            arrival_quantity=F('arrival_quantity') + 1)
        Product.objects.filter(id=order_detail.product_id).update(
            collect_num=F('collect_num') + 1)
        ProductSku.objects.filter(id=order_detail.chichu_id).update(
            quantity=F('quantity') + 1)
        log_action(request.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'次品减一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(request.user.id, order_detail, CHANGE, u'%s' % (u'次品减一'))
        return HttpResponse("OK")
    elif flag == "1":
        OrderDetail.objects.filter(id=order_detail_id).update(
            inferior_quantity=F('inferior_quantity') + 1)
        OrderDetail.objects.filter(id=order_detail_id).update(
            non_arrival_quantity=F('buy_quantity') - F('arrival_quantity') - F(
                'inferior_quantity'))
        OrderDetail.objects.filter(id=order_detail_id).update(
            arrival_quantity=F('arrival_quantity') - 1)
        Product.objects.filter(id=order_detail.product_id).update(
            collect_num=F('collect_num') - 1)
        ProductSku.objects.filter(id=order_detail.chichu_id).update(
            quantity=F('quantity') - 1)
        log_action(request.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'次品加一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(request.user.id, order_detail, CHANGE, u'%s' % (u'次品加一'))
        return HttpResponse("OK")
    return HttpResponse("false")


class ChangeDetailExportView(View):

    @staticmethod
    def get_old(request, order_detail_id):
        headers = [u'商品编码', u'供应商编码', u'商品名称', u'规格', u'购买数量', u'买入价格', u'单项价格',
                   u'已入库数', u'次品数']
        order_list = OrderList.objects.get(id=order_detail_id)
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)
        items = []
        for o in order_details:
            item = model_to_dict(o)
            item['pic_path'] = Product.objects.get(id=o.product_id).pic_path
            item['supplier_outer_id'] = ProductSku.objects.get(
                id=o.chichu_id).get_supplier_outerid()
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
                                mimetype='application/octet-stream')
        response[
            'Content-Disposition'] = 'attachment;filename=dinghuodetail-%s.csv' % order_detail_id
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

        image_width = 25
        image_height = 125

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('E:E', image_width)

        worksheet.write('A1', '供应商名称:', bold)
        worksheet.write('A2', '供应商账号:', bold)
        worksheet.write('A3', '供应商姓名:', bold)
        worksheet.write('A4', '供应商联系方式:', bold)

        order_list = OrderList.objects.get(id=order_detail_id)
        buyer_name = order_list.buyer_name or ''

        supplier_name = ''
        supplier_contactor = ''
        supplier_contact = ''
        order_details = OrderDetail.objects.filter(orderlist_id=order_detail_id)

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
            print repr(product.pic_path)
            products[product.id] = {
                'sale_product_id': product.sale_product,
                'pic_path':
                ('%s?imageMogr2/thumbnail/560/crop/560x480/format/jpg' %
                 common.utils.url_utf8_quote(product.pic_path.encode('utf-8')))
                if product.pic_path else ''
            }

        sale_products = {}
        for sale_product in SaleProduct.objects.filter(pk__in=[product[
                'sale_product_id'] for product in products.values()]):
            sale_products[sale_product.id] = sale_product.product_link

        skus = {}
        for sku in ProductSku.objects.filter(
                pk__in=[order_detail.chichu_id for order_detail in order_details
                       ]):
            skus[sku.id] = sku.outer_id

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
        worksheet.write('C6', '颜色', bold)
        worksheet.write('D6', '规格', bold)
        worksheet.write('E6', '图片', bold)
        worksheet.write('F6', '购买数量', bold)
        worksheet.write('G6', '入库数量', bold)
        worksheet.write('H6', '次品数量', bold)
        worksheet.write('I6', '单项价格', bold)
        worksheet.write('J6', '总价', bold)

        row = 6
        all_price = decimal.Decimal('0')
        all_quantity = 0
        for order_detail in order_details:
            name, color = _parse_name(order_detail.product_name)
            sku_outer_id = skus.get(int(order_detail.chichu_id)) or ''
            product = products.get(int(order_detail.product_id)) or {}
            pic_path = product.get('pic_path') or ''
            product_link = sale_products.get(product.get(
                'sale_product_id')) or ''

            worksheet.write(row, 0, name)
            worksheet.write(row, 1, sku_outer_id.rsplit('-')[0])
            worksheet.write(row, 2, color)
            worksheet.write(row, 3, order_detail.product_chicun)
            if pic_path:
                opt = {'image_data':
                       io.BytesIO(urllib.urlopen(pic_path).read()),
                       'x_scale': 0.25,
                       'y_scale': 0.25}
                if product_link:
                    opt['url'] = product_link
                worksheet.set_row(row, image_height)
                worksheet.insert_image(row, 4, pic_path, opt)

            worksheet.write(row, 5, order_detail.buy_quantity)
            worksheet.write(row, 6, order_detail.arrival_quantity)
            worksheet.write(row, 7, order_detail.inferior_quantity)
            worksheet.write(row, 8, order_detail.buy_unitprice, money)
            worksheet.write(row, 9, order_detail.total_price, money)
            all_quantity += order_detail.buy_quantity
            all_price += decimal.Decimal(str(order_detail.total_price))
            row += 1


        worksheet.write(row, 4, '总数:', bold)
        worksheet.write(row, 5, all_quantity)
        worksheet.write(row, 8, '总计:', bold)
        worksheet.write(row, 9, order_list.order_amount, money)

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
            mimetype=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response
