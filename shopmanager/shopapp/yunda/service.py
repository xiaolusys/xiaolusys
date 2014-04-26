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
from shopapp.yunda.models import YundaCustomer,LogisticOrder,ParentPackageWeight,\
    TodaySmallPackageWeight,TodayParentPackageWeight,AnonymousYundaCustomer,YUNDA_CODE,NORMAL,DELETE
from common.utils import valid_mobile,format_datetime
import logging

logger = logging.getLogger('django.request')

YUNDA_ADDR_URL = 'http://qz.yundasys.com:18080/ws/opws.jsp'
YUNDA_SCAN_URL = 'http://qz.yundasys.com:9900/ws/ws.jsp'

ADDR_UPLOAD_LIMIT   = 100
WEIGHT_UPLOAD_LIMIT = 30
RETRY_INTERVAL      = 60

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
    
    return tree


class YundaService(object):
    
    yd_account = None
    
    def __init__(self,cus_code):
        
        self.yd_account = self.getAccount(cus_code)
    
    def getAccount(self,cus_code):
        try:
            return YundaCustomer.objects.get(code=cus_code)
        except:
            raise Exception(u'未找到编码(%s)对应的客户'%cus_code)
        
    def _getYundaYJSWData(self,obj):
            
        return [obj.get('valid_code',''),
                obj['package_id'],
                None,
                '20',
                obj['upload_weight'],
                '0',
                self.yd_account.cus_id,
                None,
                self.yd_account.cus_id,
                None,
                None,
                200000,
                None,
                self.yd_account.cus_id,
                '0',
                '14',
                format_datetime(obj['weighted'])]   
    
    def _getYJSWXmlData(self,objs):
    
        content = []
        header = """<req op="op04chz">
                    <h>
                        <ver>1.0</ver>
                        <company>%s</company>
                        <user>%s</user>
                        <pass>%s</pass>
                        <dev1>%s</dev1>
                        <dev2>%s</dev2>
                    </h><data>"""%(self.yd_account.cus_id,
                                   self.yd_account.lanjian_id,
                                   self.yd_account.lanjian_code,
                                   self.yd_account.sn_code,
                                   self.yd_account.device_code)
        footer = "</data></req>"
        
        content.append(header)
        
        for obj in objs:
            
            kvs = self._getYundaYJSWData(obj) 
            
            o = ["<o>"]
            for im in kvs:
                o.append(im and '<d>%s</d>'%im or '<d />')
            o.append("</o>")
            
            content.append("".join(o))
            
        content.append(footer)
        
        return "".join(content)
    
    
    def flushSmallPackageWeight(self,package):
        
        lo = LogisticOrder.objects.get(out_sid=package['package_id'])
        lo.upload_weight = package['upload_weight']
        lo.is_charged    = True
        lo.uploaded      = datetime.datetime.now()
        lo.save()    
        
        tspw = TodaySmallPackageWeight.objects.get(package_id=package['package_id'])
        tspw.delete()
        
    def flushParentPackageWeight(self,package):
        
        ppw  = ParentPackageWeight.objects.get(parent_package_id=package['package_id'])
        ppw.weight = package['weight']
        ppw.upload_weight = package['upload_weight']
        ppw.is_charged    = True
        ppw.uploaded      = datetime.datetime.now()
        ppw.save()    
        
        tppw = TodayParentPackageWeight.objects.get(parent_package_id=package['package_id'])
        tppw.delete()    
    
    def flushPackageWeight(self,yd_dict_list):
        
        for package in yd_dict_list:
            if package['is_parent']:
                self.flushParentPackageWeight(package)
                continue
            self.flushSmallPackageWeight(package)
        
        
    def validWeight(self,package_list):
        
        for package in package_list:
            if not package['upload_weight'] or float(package['upload_weight']) == 0:
                raise Exception(u'上传包裹(%s)重量不能小于0!'%package['package_id'])
            
        return True
        
    def uploadWeight(self,package_dict_list):
        
        self.validWeight(package_dict_list)
        
        post_xml  = self._getYJSWXmlData(package_dict_list)
        
        post_yunda_service(YUNDA_SCAN_URL,data=post_xml.encode('utf8'))
            
        
    
