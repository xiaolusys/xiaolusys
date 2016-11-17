# -*- encoding:utf8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app
from celery import Celery
from celery.app.task import Task

import sys
import os
import string
import zipfile
import types
import hashlib
import re
import datetime
import json
import urllib2
from os.path import basename
from urlparse import urlsplit
from django.conf import settings
from django.template.loader import render_to_string
from shopback.base.exception import NotImplement
from shopapp.asynctask.models import (TaobaoAsyncTaskModel,
                                      PrintAsyncTaskModel,
                                      TASK_ASYNCOK,
                                      TASK_INVALID,
                                      TASK_CREATED,
                                      TASK_SUCCESS,
                                      TASK_ASYNCCOMPLETE,
                                      TASK_DOWNLOAD)

from shopback.categorys.models import Category
from shopback.orders.models import Trade
from shopback.trades.models import MergeTrade, PackageOrder, PackageSkuItem
from shopback.items.models import Product, ProductSku

from shopapp.taobao import apis
import logging
logger = logging.getLogger('django.request')

TASK_STATUS = {
    'new': TASK_ASYNCOK,
    'done': TASK_ASYNCCOMPLETE,
    'fail': TASK_INVALID,
    'doing': TASK_ASYNCOK
}


def full_class_name(ins):
    return ins.__module__ + '.' + ins.__class__.__name__


@app.task()
def taobaoAsyncHandleTask():
    """ 淘宝异步任务处理核心类 """
    asynctasks = TaobaoAsyncTaskModel.objects.filter(status__in=(TASK_ASYNCOK, TASK_ASYNCCOMPLETE, TASK_DOWNLOAD))
    app = Celery()
    for asynctask in asynctasks:
        task_name = asynctask.task

        if not task_name:
            continue

        task_handler = app.tasks[task_name]
        if asynctask.status == TASK_ASYNCOK:
            task_handler.is_taobao_complete(asynctask.task_id)
            asynctask = TaobaoAsyncTaskModel.objects.get(task_id=asynctask.task_id)

        if asynctask.status == TASK_ASYNCCOMPLETE:
            task_handler.download_result_file(asynctask.task_id)

            asynctask = TaobaoAsyncTaskModel.objects.get(task_id=asynctask.task_id)

        if asynctask.status == TASK_DOWNLOAD:
            handlerresult = task_handler.handle_result_file(asynctask.task_id)
            if handlerresult:
                TaobaoAsyncTaskModel.objects.filter(task_id=asynctask.task_id).update(status=TASK_SUCCESS)


class TaobaoAsyncBaseTask(Task):
    """
        {
            "topats_itemcats_get_response": {
                "task": {
                    "download_url": "http://download.api.taobao.com/download?id=bacnoiewothoi",
                    "check_code": "efdbe2545a01aff317f0cbaad6663c7c",
                    "schedule": "2000-01-01 00:00:00",
                    "task_id": 12345,
                    "status": "done",
                    "method": "taobao.topats.trades.fullinfo.get",
                    "created": "2000-01-01 00:00:00"
                }
            }
        }
    """

    def run(self, *args, **kwargs):
        raise NotImplement("该方法没有实现")

    def after_return(self, status, result_dict, *args, **kwargs):

        try:
            async_task = TaobaoAsyncTaskModel.objects.create(task=full_class_name(self))
        except Exception, exc:
            raise exc
        else:
            user_id = result_dict['user_id']
            next_status = TASK_ASYNCOK if result_dict['success'] else TASK_INVALID
            result_json = json.dumps(result_dict['result']) if result_dict['success'] else result_dict['result']
            top_task_id = result_dict.get('top_task_id', '')
            params = json.dumps(result_dict.get('params', {}))
            TaobaoAsyncTaskModel.objects.filter(task_id=async_task.task_id) \
                .update(user_id=user_id, status=next_status, result=result_json, top_task_id=top_task_id, params=params)

    def is_taobao_complete(self, task_id):
        try:
            async_task = TaobaoAsyncTaskModel.objects.get(task_id=task_id)
        except:
            logger.error('the taobao async task(id:%s) is not exist' % task_id)
        else:
            try:
                response = apis.taobao_topats_result_get(task_id=async_task.top_task_id, tb_user_id=async_task.user_id)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
            else:
                task_status = response['topats_result_get_response']['task']['status']
                async_task_status = TASK_STATUS.get(task_status, TASK_INVALID)
                TaobaoAsyncTaskModel.objects.filter(task_id=task_id).update(status=async_task_status,
                                                                            result=json.dumps(response))

    def download_result_file(self, task_id):

        try:
            async_task = TaobaoAsyncTaskModel.objects.get(task_id=task_id)
        except:
            logger.error('the taobao async task(id:%s) is not exist' % task_id)
        else:
            result = json.loads(async_task.result)
            task = result['topats_result_get_response']['task']
            check_code = task['check_code']
            download_url = task['download_url']
            file_path = os.path.join(settings.ASYNC_FILE_PATH, task['method'], str(task['task_id']))
            try:
                self.dirCreate(file_path)
                success = self.download_file(download_url, check_code, file_path=file_path)
            except Exception, exc:
                logger.error('%s' % exc, exc_info=True)
            else:
                async_status = TASK_DOWNLOAD if success else TASK_ASYNCOK
                TaobaoAsyncTaskModel.objects.filter(task_id=task_id).update(status=async_status, file_path_to=file_path)

    def handle_result_file(self, task_id, result={}):
        raise NotImplement("该方法没有实现")

    def url2name(self, url):
        return basename(urlsplit(url)[2])

    def dirCreate(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    def download_file(self, url, valid_code, file_path=None):
        fileName = self.url2name(url)
        req = urllib2.Request(url)
        r = urllib2.urlopen(req)
        content = r.read()

        if valid_code != hashlib.md5(content).hexdigest():
            return False

        if r.info().has_key('Content-Disposition'):
            # If the response has Content-Disposition, we take file name from it
            fileName = r.info()['Content-Disposition'].split('filename=')[1]
            if fileName[0] == '"' or fileName[0] == "'":
                fileName = fileName[1:-1]
        elif r.url != url:
            # if we were redirected, the real file name we take from the final URL
            fileName = self.url2name(r.url)
        if file_path:
            # we can force to save the file as specified name
            fileName = os.path.join(file_path, fileName)

        with open(fileName, 'wb') as f:
            f.write(content)
        try:
            z = zipfile.ZipFile(fileName, 'r')
            for zf in z.namelist():
                fname = os.path.join(file_path, zf)
                if fname.endswith('/'):
                    fname = string.rstrip(fname, '/')
                    if not os.path.exists(fname):
                        os.mkdir(fname)
                        continue
                        # if sys.platform == 'win32':
                # fname = string.replace(fname, '/', '\\')
                file(fname, 'wb').write(z.read(zf))
        except Exception, exc:
            logger.error('%s' % exc, exc_info=True)
            return False
        else:
            os.remove(fileName)

        return True


# ========================== Async Category Task ============================
class AsyncCategoryTask(TaobaoAsyncBaseTask):
    def run(self, cids, user_id, seller_type='B', fetch_time=None, *args, **kwargs):

        try:
            response = apis.taobao_topats_itemcats_get(seller_type=seller_type, cids=cids, tb_user_id=user_id)
        except Exception, exc:
            logger.error('%s' % exc, exc_info=True)
            return {'user_id': user_id, 'success': False, 'result': '%s' % exc}
        else:
            top_task_id = response['topats_itemcats_get_response']['task']['task_id']
            return {'user_id': user_id,
                    'success': True,
                    'result': response,
                    'top_task_id': top_task_id,
                    'params': {'cids': cids, 'seller_type': seller_type}}

    def handle_result_file(self, task_id):
        try:
            async_task = TaobaoAsyncTaskModel.objects.get(task_id=task_id)
            task_files = os.listdir(async_task.file_path_to)
            for fname in task_files:
                fname = os.path.join(async_task.file_path_to, fname)
                with open(fname, 'r') as f:
                    content = f.read()
                content = json.loads(content)
                self.save_category(content)
            return True
        except Exception, exc:
            logger.error('async task result handle fail: %s' % exc, exc_info=True)
            return False

    def save_category(self, cat_json):
        cat, state = Category.objects.get_or_create(cid=cat_json['cid'])
        cat.parent_cid = cat_json['parentCid']
        cat.is_parent = cat_json['isParent']
        cat.name = cat_json['name']
        cat.sortOrder = cat_json['sortOrder']
        cat.save()

        sub_cat_jsons = cat_json['childCategoryList']
        if isinstance(sub_cat_jsons, (list, tuple)):
            for sub_cat_json in sub_cat_jsons:
                self.save_category(sub_cat_json)


# ================================ Async Order Task   ==================================
class AsyncOrderTask(TaobaoAsyncBaseTask):
    def run(self, start_time, end_time, user_id, fetch_time=None, *args, **kwargs):

        if start_time > end_time:
            return

        start_time = start_time.strftime("%Y%m%d")
        end_time = end_time.strftime("%Y%m%d")
        try:
            response = apis.taobao_topats_trades_sold_get(start_time=start_time,
                                                          end_time=end_time,
                                                          tb_user_id=user_id)
            # response = {u'topats_trades_sold_get_response': {u'task': {u'task_id': 37606086, u'created': u'2012-08-31 17:40:42'}}}
        except Exception, exc:
            logger.error('%s' % exc, exc_info=True)
            return {'user_id': user_id, 'success': False, 'result': '%s' % exc}
        else:
            top_task_id = response['topats_trades_sold_get_response']['task']['task_id']
            return {'user_id': user_id,
                    'success': True,
                    'result': response,
                    'top_task_id': top_task_id,
                    'params': {'start_time': start_time, 'end_time': end_time}}

    def handle_result_file(self, task_id):
        try:
            async_task = TaobaoAsyncTaskModel.objects.get(task_id=task_id)
            task_files = os.listdir(async_task.file_path_to)
            for fname in task_files:
                fname = os.path.join(async_task.file_path_to, fname)
                with open(fname, 'r') as f:
                    order_list = f.readlines()

                for order_str in order_list:
                    order_dict = json.loads(order_str)
                    Trade.save_trade_through_dict(async_task.user_id,
                                                  order_dict['trade_fullinfo_get_response']['trade'])

            return True
        except Exception, exc:
            logger.error('async task result handle fail: %s' % exc, exc_info=True)
            return False

@app.task
def task_async_order(*args, **kwargs):
    return AsyncOrderTask().run(*args, **kwargs)

from core.upload.upload import upload_data_to_remote, generate_private_url

class PrintAsyncTask(object):
    ignore_result = False

    def genExpressData(self, trade_list):
        pass

    def genInvoiceData(self, trade_list):

        picking_data_list = []
        for trade in trade_list:

            dt = datetime.datetime.now()
            trade_data = {'ins': trade,
                          'today': dt,
                          'juhuasuan': trade.trade_from,
                          'order_nums': 0,
                          'total_fee': 0,
                          'discount_fee': 0,
                          'payment': 0,}

            prompt_set = set()
            order_items = {}
            for order in trade.print_orders:

                trade_data['order_nums'] += order.num
                trade_data['discount_fee'] += float(order.discount_fee or 0)
                trade_data['total_fee'] += float(order.total_fee or 0)
                trade_data['payment'] += float(order.payment or 0)

                outer_id = order.outer_id or str(order.num_iid)
                outer_sku_id = order.outer_sku_id or str(order.sku_id)

                products = Product.objects.filter(outer_id=order.outer_id)
                product = products.count() > 0 and products[0] or None
                prod_skus = ProductSku.objects.filter(outer_id=order.outer_sku_id, product=product)
                prod_sku = prod_skus.count() > 0 and prod_skus[0] or None

                product_id = product and product.id or ''
                sku_id = prod_sku and prod_sku.id or ''

                promptmsg = (prod_sku and prod_sku.buyer_prompt) or (product and product.buyer_prompt) or ''
                if promptmsg:
                    prompt_set.add(promptmsg)

                product_location = product and product.get_districts_code() or ''
                product_sku_location = prod_sku and prod_sku.get_districts_code() or ''

                if order_items.has_key(outer_id):
                    order_items[outer_id]['num'] += order.num
                    skus = order_items[outer_id]['skus']
                    if skus.has_key(outer_sku_id):
                        skus[outer_sku_id]['num'] += order.num
                    else:
                        prod_sku_name = prod_sku and prod_sku.name or order.sku_properties_name
                        skus[outer_sku_id] = {'sku_name': prod_sku_name,
                                              'num': order.num,
                                              'location': product_sku_location}
                else:
                    prod_sku_name = prod_sku and prod_sku.name or order.sku_properties_name
                    order_items[outer_id] = {
                        'num': order.num,
                        'location': product_location,
                        'title': product.name if product else order.title,
                        'skus': {outer_sku_id: {
                            'sku_name': prod_sku_name,
                            'num': order.num,
                            'location': product_sku_location}
                        }
                    }
            if trade.is_part_consign:
                prompt_set.add(u'客官，您的订单已拆单分批发货，其它宝贝正在陆续赶来，请您耐心等候')

            trade_data['buyer_prompt'] = prompt_set and ','.join(list(prompt_set)) or ''
            order_list = sorted(order_items.items(), key=lambda d: d[1]['location'])
            for trade in order_list:
                skus = trade[1]['skus']
                trade[1]['skus'] = sorted(skus.items(), key=lambda d: d[1]['location'])

            trade_data['orders'] = order_list
            picking_data_list.append(trade_data)

        return picking_data_list

    def genHtmlPDF(self, file_path, html_text):

        import xhtml2pdf.pisa as pisa
        import cStringIO as StringIO

        with open(file_path, 'wb') as result:
            pdf = pisa.pisaDocument(StringIO.StringIO(html_text), result)
            if pdf.err:
                raise Exception(u'PDF 创建失败')

    def genHtmlPDFIostream(self, html_text):

        import xhtml2pdf.pisa as pisa
        import cStringIO as StringIO
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(StringIO.StringIO(html_text), result)
        if pdf.err:
            raise Exception(u'PDF 创建失败')
        return StringIO.StringIO(result.getvalue())

    def run(self, async_print_id, *args, **kwargs):

        print_async = PrintAsyncTaskModel.objects.get(pk=async_print_id)

        params_json = json.loads(print_async.params)
        trade_ids = [int(p.strip()) for p in params_json['trade_ids'].split(',')]
        user_code = params_json['user_code'].lower()

        trade_list = MergeTrade.objects.filter(id__in=trade_ids).order_by('out_sid')

        if print_async.task_type == PrintAsyncTaskModel.INVOICE:

            invoice_data = self.genInvoiceData(trade_list)
            invoice_html = render_to_string('asynctask/print/invoice_%s_template.html' % user_code,
                                            {'trade_list': invoice_data})
            #             invoice_path = os.path.join(settings.DOWNLOAD_ROOT,'print','invoice')
            #             if not os.path.exists(invoice_path):
            #                 os.makedirs(invoice_path)

            file_pathname = os.path.join('print', 'invoice', 'IN%d.pdf' % print_async.pk)
            #             self.genHtmlPDF(os.path.join(invoice_path, file_name), invoice_html.encode('utf-8'))
            file_stream = self.genHtmlPDFIostream(invoice_html.encode('utf-8'))
            upload_data_to_remote(file_pathname, file_stream)

            print_async.file_path_to = generate_private_url(file_pathname)
            print_async.status = PrintAsyncTaskModel.TASK_SUCCESS
            print_async.save()
            return print_async.file_path_to
        else:

            express_data = self.genExpressData(trade_list)
        return 0

@app.task
def task_print_async(*args, **kwargs):
    return PrintAsyncTask().run(*args, **kwargs)

class PrintAsyncTask2(object):
    ignore_result = False

    def genExpressData(self, trade_list):
        pass

    def genInvoiceData(self, package_orders):

        picking_data_list = []
        for trade in package_orders:

            dt = datetime.datetime.now()
            trade_data = {'ins': trade,
                          'today': dt,
                          'juhuasuan': False,
                          'order_nums': 0,
                          'total_fee': 0,
                          'discount_fee': 0,
                          'payment': 0,}

            prompt_set = set()
            order_items = {}
            for sku_item in trade.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED):

                trade_data['order_nums'] += sku_item.num
                trade_data['discount_fee'] += float(sku_item.discount_fee or 0)
                trade_data['total_fee'] += float(sku_item.total_fee or 0)
                trade_data['payment'] += float(sku_item.payment or 0)

                outer_id = sku_item.outer_id
                outer_sku_id = sku_item.outer_sku_id or str(sku_item.sku_id)

                prod_sku = sku_item.product_sku
                product = prod_sku.product

                promptmsg = (prod_sku and prod_sku.buyer_prompt) or (product and product.buyer_prompt) or ''
                if promptmsg:
                    prompt_set.add(promptmsg)

                product_location = product and product.get_districts_code() or ''
                product_sku_location = prod_sku and prod_sku.get_districts_code() or ''

                if order_items.has_key(outer_id):
                    order_items[outer_id]['num'] += sku_item.num
                    skus = order_items[outer_id]['skus']
                    if skus.has_key(outer_sku_id):
                        skus[outer_sku_id]['num'] += sku_item.num
                    else:
                        prod_sku_name = prod_sku and prod_sku.name or sku_item.sku_properties_name
                        skus[outer_sku_id] = {'sku_name': prod_sku_name,
                                              'num': sku_item.num,
                                              'location': product_sku_location}
                else:
                    prod_sku_name = prod_sku and prod_sku.name or sku_item.sku_properties_name
                    order_items[outer_id] = {
                        'num': sku_item.num,
                        'location': product_location,
                        'title': product.name if product else sku_item.title,
                        'skus': {outer_sku_id: {
                            'sku_name': prod_sku_name,
                            'num': sku_item.num,
                            'location': product_sku_location}
                        }
                    }
            # if:
            #    prompt_set.add(u'客官，您的订单已拆单分批发货，其它宝贝正在陆续赶来，请您耐心等候')

            trade_data['buyer_prompt'] = prompt_set and ','.join(list(prompt_set)) or ''
            order_list = sorted(order_items.items(), key=lambda d: d[1]['location'])
            for trade in order_list:
                skus = trade[1]['skus']
                trade[1]['skus'] = sorted(skus.items(), key=lambda d: d[1]['location'])

            trade_data['orders'] = order_list
            picking_data_list.append(trade_data)

        return picking_data_list

    def genHtmlPDF(self, file_path, html_text):

        import xhtml2pdf.pisa as pisa
        import cStringIO as StringIO

        with open(file_path, 'wb') as result:
            pdf = pisa.pisaDocument(StringIO.StringIO(html_text), result)
            if pdf.err:
                raise Exception(u'PDF 创建失败')

    def genHtmlPDFIostream(self, html_text):

        import xhtml2pdf.pisa as pisa
        import cStringIO as StringIO
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(StringIO.StringIO(html_text), result)
        if pdf.err:
            raise Exception(u'PDF 创建失败')
        return StringIO.StringIO(result.getvalue())

    def run(self, async_print_id, *args, **kwargs):

        print_async = PrintAsyncTaskModel.objects.get(pk=async_print_id)
        params_json = json.loads(print_async.params)
        trade_ids = [int(p.strip()) for p in params_json['trade_ids'].split(',')]
        user_code = params_json['user_code'].lower()
        package_orders = PackageOrder.objects.filter(pid__in=trade_ids).order_by('out_sid')
        if print_async.task_type == PrintAsyncTaskModel.INVOICE:

            invoice_data = self.genInvoiceData(package_orders)
            invoice_html = render_to_string('asynctask/print/invoice_%s_template2.html' % user_code,
                                            {'trade_list': invoice_data})
            #             invoice_path = os.path.join(settings.DOWNLOAD_ROOT,'print','invoice')
            #             if not os.path.exists(invoice_path):
            #                 os.makedirs(invoice_path)

            file_pathname = os.path.join('print', 'invoice', 'IN%d.pdf' % print_async.pk)
            #             self.genHtmlPDF(os.path.join(invoice_path, file_name), invoice_html.encode('utf-8'))
            file_stream = self.genHtmlPDFIostream(invoice_html.encode('utf-8'))
            upload_data_to_remote(file_pathname, file_stream)

            print_async.file_path_to = generate_private_url(file_pathname)
            print_async.status = PrintAsyncTaskModel.TASK_SUCCESS
            print_async.save()
            return print_async.file_path_to
        else:

            express_data = self.genExpressData(package_orders)
        return 0

@app.task
def task_print_async2(*args, **kwargs):
    return PrintAsyncTask2().run(*args, **kwargs)
