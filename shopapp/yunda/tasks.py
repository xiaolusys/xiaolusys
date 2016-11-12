# -*- coding:utf8 -*-
import time
import datetime
import json
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO
from celery import Task
from django.core.paginator import Paginator
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade
from shopback.users.models import User as Seller
from shopapp.yunda.qrcode import cancel_order, search_order, parseTreeID2MailnoMap
from shopapp.yunda.models import LogisticOrder, YundaCustomer, TodaySmallPackageWeight, \
    YUNDA_CODE, NORMAL, DELETE
from common.utils import valid_mobile, format_datetime
import logging

logger = logging.getLogger('celery.handler')
######################## 韵达录单任务 ########################
YUNDA_ADDR_URL = 'http://qz.yundasys.com:18080/ws/opws.jsp'
YUNDA_SCAN_URL = 'http://qz.yundasys.com:9900/ws/ws.jsp'

SID_CANCEL_LIMIT = 500
ADDR_UPLOAD_LIMIT = 100
WEIGHT_UPLOAD_LIMIT = 30
RETRY_INTERVAL = 60

STATE_CODE_MAP = {
    u"陕西": "610000",
    u"宁夏": "640000",
    u"上海": "310000",
    u"广东": "440000",
    u"山西": "140000",
    u"湖北": "420000",
    u"贵州": "520000",
    u"湖南": "430000",
    u"浙江": "330000",
    u"天津": "120000",
    u"安徽": "340000",
    u"四川": "510000",
    u"内蒙": "150000",
    u"河北": "130000",
    u"海南": "460000",
    u"甘肃": "620000",
    u"重庆": "500000",
    u"山东": "370000",
    u"福建": "350000",
    u"黑龙": "230000",
    u"江西": "360000",
    u"江苏": "320000",
    u"云南": "530000",
    u"北京": "110000",
    u"广西": "450000",
    u"辽宁": "210000",
    u"吉林": "220000",
    u"河南": "410000",
    u"西藏": "540000",
    u"新疆": "650000",
    u"青海": "630000"
}


def post_yunda_service(req_url, data='', headers=None):
    """
    <dta st="ok" res="0" op="op02putdan">
    <h><ver>3.0</ver><time>2013-09-07 17:20:48</time></h>
    </dta>
    """

    # data = urllib.urlencode(data)
    req = urllib2.Request(req_url, data=data,
                          headers=headers or {'Content-Type': 'text/xml; charset=UTF-8',
                                              'Accept': '*/*',
                                              'Accept-Language': 'zh-cn',
                                              'Connection': 'Keep-Alive',
                                              'Cache-Control': 'no-cache'})
    r = urllib2.urlopen(req)
    res = r.read()

    parser = etree.XMLParser()
    tree = etree.parse(StringIO(res), parser)

    ds = tree.xpath('/dta')

    status = ds[0].attrib['st']
    if status.lower() != 'ok':
        raise Exception(res)

    return res


class CancelUnsedYundaSidTask(Task):
    """ 取消韵达二维码打单但未发出单号 """
    max_retries = 3
    interval_days = 10

    def getCustomerBySeller(self, seller):
        return YundaCustomer.objects.filter(code=seller.user_code)

    def getSourceIDList(self, seller, ware_by):

        dt = datetime.datetime.now()
        df = dt - datetime.timedelta(days=self.interval_days)

        trades = MergeTrade.objects.filter(user=seller,
                                           is_qrcode=True,
                                           ware_by=ware_by,
                                           pay_time__gte=df,
                                           pay_time__lte=dt)

        return [t.id for t in trades]

    def isCancelable(self, order_serial_no, mail_no, status):

        if status != '1' and not mail_no:
            return False

        trade = MergeTrade.objects.get(id=order_serial_no)
        if trade.out_sid.strip() != mail_no or \
                not trade.is_qrcode or \
                        trade.sys_status in pcfg.CANCEL_YUNDASID_STATUS:
            return True

        return False

    def getCancelIDList(self, seller, yd_customer):

        source_ids = self.getSourceIDList(seller, ware_by=yd_customer.ware_by)
        if not source_ids:
            return []

        cancel_ids = []
        doc = search_order(source_ids,
                           partner_id=yd_customer.qr_id,
                           secret=yd_customer.qr_code)

        orders = doc.xpath('/responses/response')
        for order in orders:
            status = order.xpath('status')[0].text
            mail_no = order.xpath('mailno')[0].text
            order_serial_no = order.xpath('order_serial_no')[0].text

            if self.isCancelable(order_serial_no, mail_no, status):
                cancel_ids.append(order_serial_no)

        return cancel_ids

    def run(self):

        sellers = Seller.objects.all()
        try:
            for seller in sellers:
                yd_customers = self.getCustomerBySeller(seller)
                for yd_customer in yd_customers:
                    cancel_ids = self.getCancelIDList(seller, yd_customer)
                    cancel_order(cancel_ids,
                                 partner_id=yd_customer.qr_id,
                                 secret=yd_customer.qr_code)
        except Exception, exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)


class UpdateYundaOrderAddrTask(Task):
    max_retries = 3
    pg = []

    def initial_data(self):
        self.pg = Paginator(self.getSourceData(), ADDR_UPLOAD_LIMIT)

    def getSourceData(self):
        return LogisticOrder.objects.filter(is_charged=True, sync_addr=False, status=NORMAL)

    def getYundaYJSMData(self, obj):
        return [obj.out_sid,
                u'互一网络',
                '310000',
                None,
                None,
                '0',
                '0',
                u'上海市松江区洞厍路398弄7号楼2楼',
                '02137698479',
                '200135',
                cgi.escape(obj.receiver_name or 'NONE'),
                self.getStateCode(obj),
                None,
                None,
                '0',
                '0',
                cgi.escape(obj.receiver_city + obj.receiver_district + obj.receiver_address),
                obj.receiver_mobile,
                None,
                '001',
                '101342',
                None,
                '0',
                '0',
                None,
                '0',
                'taobao',
                None,
                None]

    def getYJSMXmlData(self, objs):

        content = []
        header = """<req op="op02putdan">
                    <h>
                        <ver>3.0</ver>
                        <company>101342</company>
                        <user>001</user>
                        <pass>202cb962ac59075b964b07152d234b70</pass>
                        <dev1>excel20110330</dev1>
                        <dev2>1001</dev2>
                    </h><data>"""
        footer = "</data></req>"

        content.append(header)

        for obj in objs:

            kvs = self.getYundaYJSMData(obj)

            o = ["<o>"]
            for im in kvs:
                o.append(im == None and '<d></d>' or '<d>%s</d>' % im)
            o.append("</o>")

            content.append("".join(o))

        content.append(footer)

        return "".join(content)

    def getStateCode(self, order):

        state = len(order.receiver_state) >= 2 and order.receiver_state[0:2] or ''
        return STATE_CODE_MAP.get(state)

    def isOrderValid(self, order):
        return self.getStateCode(order) != None and order.receiver_mobile \
               and valid_mobile(order.receiver_mobile.strip())

    def getValidOrders(self, orders):

        return [order for order in orders if self.isOrderValid(order)]

    def uploadAddr(self, orders):

        if not orders:
            return []
        try:

            post_xml = self.getYJSMXmlData(orders)
            post_yunda_service(YUNDA_ADDR_URL, data=post_xml.encode('utf8'))

            return [o.id for o in orders]
        except Exception, exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)

    def run(self):

        self.initial_data()

        if self.pg.count == 0:
            return

        update_oids = []
        try:
            for i in range(1, self.pg.num_pages + 1):
                update_oids.extend(self.uploadAddr(
                    self.getValidOrders(self.pg.page(i).object_list)))
        finally:
            LogisticOrder.objects.filter(id__in=update_oids).update(sync_addr=True)


class SyncYundaScanWeightTask(Task):
    max_retries = 3
    pg = []

    def initial_data(self):
        self.pg = Paginator(self.getSourceData(), WEIGHT_UPLOAD_LIMIT)

    def getSourceData(self):

        dt = datetime.datetime.now()
        f_dt = dt - datetime.timedelta(days=2)
        return MergeTrade.objects.filter(
            logistics_company__code__in=YUNDA_CODE,
            sys_status=pcfg.FINISHED_STATUS,
            is_express_print=True,
            is_charged=False,
            weight_time__gte=f_dt,
            weight_time__lte=dt,
        ).exclude(out_sid='')

    def getYundaYJSWData(self, obj):
        return [obj.valid_code,
                obj.out_sid,
                None,
                '20',
                self.parseTradeWeight(obj.weight),
                '0',
                '199886',
                None,
                '199886',
                None,
                None,
                200000,
                None,
                '199886',
                '0',
                '14',
                format_datetime(obj.weighted)]

    def getYJSWXmlData(self, objs):

        content = []
        header = """<req op="op04chz">
                    <h>
                        <ver>1.0</ver>
                        <company>199886</company>
                        <user>199886</user>
                        <pass>37c7a1dd2ce069cf370dd30daf881850</pass>
                        <dev1>53201233834363</dev1>
                        <dev2>14781926904</dev2>
                    </h><data>"""
        footer = "</data></req>"

        content.append(header)

        for obj in objs:
            kvs = self.getYundaYJSWData(obj)

            o = ["<o>"]
            for im in kvs:
                o.append(im and '<d>%s</d>' % im or '<d />')
            o.append("</o>")

            content.append("".join(o))

        content.append(footer)

        return "".join(content)

    def parseTradeWeight(self, weight):

        try:
            float(weight)
        except:
            return '0.2'

        if weight == '' or float(weight) < 0.2 or weight.rfind('.') == 0:
            return '0.2'

        if weight.rfind('.') < 0:
            return str(round(int(weight) * 0.90 / 1000.0, 2))

        return weight

    def createYundaOrder(self, trade):

        yd_customer = YundaCustomer.objects.get(code="QIYUE")
        order, state = LogisticOrder.objects.get_or_create(
            out_sid=trade.out_sid,
            yd_customer=yd_customer)
        order.cus_oid = trade.id
        order.receiver_name = trade.receiver_name
        order.receiver_state = trade.receiver_state.strip()
        order.receiver_city = trade.receiver_city.strip()
        order.receiver_district = trade.receiver_district.strip()
        order.receiver_address = trade.receiver_address
        order.receiver_zip = trade.receiver_zip
        order.receiver_mobile = trade.receiver_mobile.strip()
        order.receiver_phone = trade.receiver_phone.strip()

        order.weight = self.parseTradeWeight(trade.weight)
        order.weighted = trade.weight_time
        order.dc_code = trade.reserveo
        order.valid_code = trade.reserveh
        order.save()

        return order

    def getValidOrders(self, orders):

        cus_orders = []
        for order in orders:
            o = self.createYundaOrder(order)
            if not o.is_charged:
                cus_orders.append(o)

        return cus_orders

    def uploadWeight(self, orders):

        try:
            cus_oids = [o.id for o in orders]

            valid_orders = self.getValidOrders(orders)

            post_xml = self.getYJSWXmlData(valid_orders)
            post_yunda_service(YUNDA_SCAN_URL, data=post_xml.encode('utf8'))

            LogisticOrder.objects.filter(cus_oid__in=cus_oids).update(is_charged=True)

            return cus_oids
        except Exception, exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)

    def run(self):

        self.initial_data()

        if self.pg.count == 0:
            return

        update_oids = []
        try:
            for i in range(1, self.pg.num_pages + 1):
                update_oids.extend(self.uploadWeight(self.pg.page(i).object_list))

        finally:
            MergeTrade.objects.filter(id__in=update_oids).update(
                is_charged=True, charge_time=datetime.datetime.now())


class PushYundaPackageWeightTask(Task):
    max_retries = 3

    def getSourceData(self):

        dt = datetime.datetime.now()
        f_dt = dt - datetime.timedelta(days=2)
        return MergeTrade.objects.filter(
            logistics_company__code__in=YUNDA_CODE,
            sys_status=pcfg.FINISHED_STATUS,
            is_express_print=True,
            is_charged=False,
            weight_time__gte=f_dt,
            weight_time__lte=dt,
        ).exclude(out_sid='')

    def parseTradeWeight(self, weight):

        try:
            float(weight)
        except:
            return '0.2'

        if weight == '' or float(weight) < 0.1 or weight.rfind('.') == 0:
            return '0.1'

        if weight.rfind('.') < 0:
            return '%.2f' % (int(weight) / 1000.0)

        return weight

    def createYundaOrder(self, trade):

        yd_customer = YundaCustomer.objects.get(code="QIYUE")
        order, state = LogisticOrder.objects.get_or_create(
            out_sid=trade.out_sid,
            yd_customer=yd_customer
        )

        order.cus_oid = trade.id
        order.receiver_name = trade.receiver_name
        order.receiver_state = trade.receiver_state.strip()
        order.receiver_city = trade.receiver_city.strip()
        order.receiver_district = trade.receiver_district.strip()
        order.receiver_address = trade.receiver_address
        order.receiver_zip = trade.receiver_zip
        order.receiver_mobile = trade.receiver_mobile.strip()
        order.receiver_phone = trade.receiver_phone.strip()

        order.weight = self.parseTradeWeight(trade.weight)
        order.weighted = trade.weight_time
        order.dc_code = trade.reserveo
        order.valid_code = trade.reserveh
        order.save()

        return order

    def createSmallPackage(self, order):

        tspw, state = TodaySmallPackageWeight.objects.get_or_create(
            package_id=order.out_sid)
        tspw.is_jzhw = order.isJZHW()
        tspw.weight = 0
        tspw.save()

    def run(self):

        source_list = self.getSourceData()
        for trade in list(source_list):

            yd_order = self.createYundaOrder(trade)

            if not yd_order.is_charged:
                self.createSmallPackage(yd_order)

            trade.is_charged = True
            trade.save()
