#-*- coding:utf8 -*-
import time
import datetime
import json
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from django.core.paginator import Paginator
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade
from shopapp.yunda.qrcode import cancel_order,search_order,parseTreeID2MailnoMap
from shopapp.yunda.models import LogisticOrder,NORMAL,DELETE
from common.utils import valid_mobile,format_datetime
import logging

logger = logging.getLogger('celery.handler')
######################## 韵达录单任务 ########################
YUNDA_ADDR_URL = 'http://qz.yundasys.com:18080/ws/opws.jsp'
YUNDA_SCAN_URL = 'http://qz.yundasys.com:9900/ws/ws.jsp'
YUNDA_CODE     = ('YUNDA','YUNDA_QR')
SID_CANCEL_LIMIT    = 500
ADDR_UPLOAD_LIMIT   = 100
WEIGHT_UPLOAD_LIMIT = 30
RETRY_INTERVAL      = 60


STATE_CODE_MAP = {
                u"陕西":"610000",
                u"宁夏":"640000",
                u"上海":"310000",
                u"广东":"440000",
                u"山西":"140000",
                u"湖北":"420000",
                u"贵州":"520000",
                u"湖南":"430000",
                u"浙江":"330000",
                u"天津":"120000",
                u"安徽":"340000",
                u"四川":"510000",
                u"内蒙":"150000",
                u"河北":"130000",
                u"海南":"460000",
                u"甘肃":"620000",
                u"重庆":"500000",
                u"山东":"370000",
                u"福建":"350000",
                u"黑龙":"230000",
                u"江西":"360000",
                u"江苏":"320000",
                u"云南":"530000",
                u"北京":"110000",
                u"广西":"450000",
                u"辽宁":"210000",
                u"吉林":"220000",
                u"河南":"410000",
                u"西藏":"540000",
                u"新疆":"650000",
                u"青海":"630000"
                }


    
def post_yunda_service(req_url,data='',headers=None):
    """
    <dta st="ok" res="0" op="op02putdan">
    <h><ver>3.0</ver><time>2013-09-07 17:20:48</time></h>
    </dta>
    """
    
    #data = urllib.urlencode(data) 
    req  = urllib2.Request(req_url, data=data, 
                           headers=headers or {'Content-Type': 'text/xml; charset=UTF-8',
                                               'Accept': '*/*',
                                               'Accept-Language': 'zh-cn',
                                               'Connection': 'Keep-Alive',
                                               'Cache-Control': 'no-cache'})
    r = urllib2.urlopen(req)
    res = r.read()
    
    parser = etree.XMLParser()
    tree   = etree.parse(StringIO(res), parser)
    
    ds = tree.xpath('/dta')
    
    status = ds[0].attrib['st']
    if status.lower() != 'ok':
        raise Exception(res)
    
    return res


class CancelUnsedYundaSidTask(Task):
    
    max_retries = 3
    
    def __init__(self,interval_days=7):
        
        self.interval_days = interval_days
        
    def getSourceIDList(self):
        
        dt  = datetime.datetime.now()
        df  = dt - datetime.timedelta(days=self.interval_days)
        
        trades = MergeTrade.objects.filter(is_qrcode=True,
                                           is_charged=False,
                                           pay_time__gte=df,
                                           pay_time__lte=dt)
        
        
        return [t.id for t in trades]
    
    def getCancelIDList(self):
        
        source_ids = self.getSourceIDList()
        if not source_ids:
            return []
            
        cancel_ids = []
        
        doc   = search_order(source_ids)
        orders = doc.xpath('/responses/response')
        for order in orders:
            status = order.xpath('status')[0].text
            mail_no = order.xpath('mailno')[0].text
            order_serial_no = order.xpath('order_serial_no')[0].text
            
            trade = MergeTrade.objects.get(id=order_serial_no)
            lgc   = trade.logistics_company
            
            if  status != '1' and not mail_no :
                continue
            
            if  trade.out_sid.strip() != mail_no or \
                (lgc and lgc.code not in YUNDA_CODE) or \
                trade.sys_status in pcfg.CANCEL_YUNDASID_STATUS:
                cancel_ids.append(order_serial_no)
                
        return cancel_ids
    
    def run(self):
        
        try:
            cancel_ids = self.getCancelIDList()
            cancel_order(cancel_ids)
            
            LogisticOrder.objects.filter(cus_oid__in=cancel_ids).update(status=DELETE)
        except Exception,exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)
        
    

class UpdateYundaOrderAddrTask(Task):
    
    max_retries = 3
    
    def __init__(self):
        
        self.pg = Paginator(self.getSourceData(), ADDR_UPLOAD_LIMIT)
    
    def getSourceData(self):
        return LogisticOrder.objects.filter(is_charged=True,sync_addr=False,status=NORMAL)
    
    def getYundaYJSMData(self,obj):
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
                cgi.escape(obj.receiver_name),
                self.getStateCode(obj),
                None,
                None,
                '0',
                '0',
                cgi.escape(obj.receiver_city+obj.receiver_district+obj.receiver_address),
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
        
    def getYJSMXmlData(self,objs):
    
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
                o.append(im==None and '<d></d>'or '<d>%s</d>'%im)
            o.append("</o>")
            
            content.append("".join(o))
            
        content.append(footer)
        
        return "".join(content)
    
    def getStateCode(self,order):
        
        state = len(order.receiver_state)>=2 and order.receiver_state[0:2] or ''
        return STATE_CODE_MAP.get(state)
    
    def isOrderValid(self,order):
        return self.getStateCode(order) != None and order.receiver_mobile \
                and valid_mobile(order.receiver_mobile.strip())
    
    def getValidOrders(self,orders):
        
        return [order for order in orders if self.isOrderValid(order)]
    
    def uploadAddr(self,orders):

        if not orders:
            return []
        try:
            
            post_xml = self.getYJSMXmlData(orders)
            post_yunda_service(YUNDA_ADDR_URL,data=post_xml.encode('utf8'))
                      
            return [o.id for o in orders]
        except Exception,exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)
    
    def run(self):
        
        if self.pg.count == 0:
            return 
        
        update_oids = []
        try:
            for i in range(1,self.pg.num_pages+1):
                update_oids.extend(self.uploadAddr(self.getValidOrders(self.pg.page(i).object_list)))
        finally:
            LogisticOrder.objects.filter(id__in=update_oids).update(sync_addr=True)


class SyncYundaScanWeightTask(Task):
    
    max_retries = 3
    
    def __init__(self):
        
        self.pg = Paginator(self.getSourceData(), WEIGHT_UPLOAD_LIMIT)
    
    def getSourceData(self):
        
        return MergeTrade.objects.filter(
                       logistics_company__code__in=YUNDA_CODE,
                       sys_status=pcfg.FINISHED_STATUS,
                       is_express_print=True,
                       is_charged=False,
                       ).exclude(out_sid='').exclude(receiver_name='')
    
    
    def getYundaYJSWData(self,obj):
        return [obj.valid_code,
                obj.out_sid,
                None,
                '20',
                self.parseTradeWeight(obj.weight),
                '0',
                '101342',
                None,
                '101342',
                None,
                None,
                200000,
                None,
                '101342',
                '0',
                '14',
                format_datetime(obj.created)]     
           
    def getYJSWXmlData(self,objs):
    
        content = []
        header = """<req op="op04chz">
                    <h>
                        <ver>1.0</ver>
                        <company>101342</company>
                        <user>101342</user>
                        <pass>3334822cbf5f6c33637f5eaa54e8c4c4</pass>
                        <dev1>53201409003566</dev1>
                        <dev2>14782083740</dev2>
                    </h><data>"""
        footer = "</data></req>"
        
        content.append(header)
        
        for obj in objs:
            kvs = self.getYundaYJSWData(obj) 
            
            o = ["<o>"]
            for im in kvs:
                o.append(im and '<d>%s</d>'%im or '<d />')
            o.append("</o>")
            
            content.append("".join(o))
            
        content.append(footer)
        
        return "".join(content)
    
    def parseTradeWeight(self,weight):
        
        try:
            float(weight)
        except:
            return '0.2'
        
        if weight == '' or float(weight) == 0 or weight.rfind('.') == 0:
            return '0.2'
        
        if weight.rfind('.') < 0:
            return str(round(int(weight)*0.9/1000.0,2))
        
        return weight
    
    def createYundaOrder(self,trade):
        
        order,state             = LogisticOrder.objects.get_or_create(cus_oid=trade.id)
        order.out_sid           = trade.out_sid
        
        order.receiver_name     = trade.receiver_name
        order.receiver_state    = trade.receiver_state.strip()
        order.receiver_city     = trade.receiver_city.strip()
        order.receiver_district = trade.receiver_district.strip()
        order.receiver_address  = trade.receiver_address
        order.receiver_zip      = trade.receiver_zip
        order.receiver_mobile   = trade.receiver_mobile.strip()
        order.receiver_phone    = trade.receiver_phone.strip()
        
        order.weight            = self.parseTradeWeight(trade.weight)
        order.dc_code           = trade.reserveo
        order.valid_code        = trade.reserveh
        order.save()
        
        return order
    
    
    def saveYundaOrder(self,orders):
        
        order_ids = [o.id for o in orders]
        for order in orders:
            self.createYundaOrder(order)
        return LogisticOrder.objects.filter(cus_oid__in=order_ids)
        
    def uploadWeight(self,orders):
        
        try:
            cus_oids  = [o.id for o in orders]
            
            cus_orders = self.saveYundaOrder(orders)
            
            post_xml  = self.getYJSWXmlData(cus_orders)
            post_yunda_service(YUNDA_SCAN_URL,data=post_xml.encode('utf8'))
            
            LogisticOrder.objects.filter(cus_oid__in=cus_oids).update(is_charged=True)
            
            return cus_oids
        except Exception,exc:
            raise self.retry(exc=exc, countdown=RETRY_INTERVAL)
        
                
    def run(self):
        if self.pg.count == 0:
            return 
        
        update_oids = []
        try:
            for i in range(1,self.pg.num_pages+1):
                update_oids.extend(self.uploadWeight(self.pg.page(i).object_list))
        
        finally:
            MergeTrade.objects.filter(id__in=update_oids).update(
                    is_charged=True,charge_time=datetime.datetime.now())
                
