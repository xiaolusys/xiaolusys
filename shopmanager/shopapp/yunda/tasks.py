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
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade
from shopapp.yunda.qrcode import cancel_order,search_order,parseTreeID2MailnoMap
from utils import valid_mobile
import logging

logger = logging.getLogger('yunda.handler')
######################## 韵达录单任务 ########################
YUNDA_ADDR_URL = 'http://qz.yundasys.com:18080/ws/opws.jsp'

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

def get_yunda_yjsm_data(out_sid,receiver,state_code,addr,mobile):
    return [out_sid,
            u'互一网络',
            '31000',
            '0',
            '0',
            u'上海市松江区洞厍路398弄7号楼2楼',
            '02137698479',
            '201601',
            cgi.escape(receiver),
            state_code,
            '0',
            '0',
            cgi.escape(addr),
            mobile,
            '001',
            '101342',
            '0',
            '0',
            '0',
            u'淘宝'
            ]
    
def get_combo_yjsm_xml(objs):
    
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
        o = ["<o>"]
        
        for im in obj:
            o.append('<d>%s</d>'%im)
        o.append("</o>")
        
        content.append("".join(o))
        
    content.append(footer)
    
    return "".join(content)
    
    
def post_yjsm_request(data):
    """
    <dta st="ok" res="0" op="op02putdan">
    <h><ver>3.0</ver><time>2013-09-07 17:20:48</time></h>
    </dta>
    """
    res = ''
    #data = urllib.urlencode(data) 
    req  = urllib2.Request(YUNDA_ADDR_URL, data=data, headers={'Content-Type': 'text/xml; charset=UTF-8',
                                                              'Accept-Language': 'zh-cn',
                                                              'Connection': 'Keep-Alive'})
    r = urllib2.urlopen(req)
    res = r.read()
    
    parser = etree.XMLParser()
    tree   = etree.parse(StringIO(res), parser)
    
    ds = tree.xpath('/dta')
    
    status = ds[0].attrib['st']
    if status.lower() != 'ok':
        raise Exception(res)
    
    return res
    
    
@task(max_retries=3)  
def updateYundaOrderAddrTask():
    
    yj_list  = []
    yj_ids   = set()
    index    = 0
    dt      = datetime.datetime.now()
    trades  = MergeTrade.objects.filter(logistics_company__code='YUNDA',
                                       sys_status=pcfg.FINISHED_STATUS,
                                       is_express_print=True,
                                       is_charged=False,
                                       ).exclude(out_sid='').exclude(receiver_name='')
    count    = trades.count()
    for trade in trades:
        
        state = len(trade.receiver_state)>=2 and trade.receiver_state[0:2] or ''
        state_code = STATE_CODE_MAP.get(state) 
        
        if state_code and trade.receiver_mobile and valid_mobile(trade.receiver_mobile):
            addr = trade.receiver_city+trade.receiver_district+trade.receiver_address
            yj_list.append(get_yunda_yjsm_data(trade.out_sid,trade.receiver_name,state_code,addr,trade.receiver_mobile))
            yj_ids.add(trade.id)
        
        index = index + 1
        if index >= count or len(yj_list) >=100:        
            
            post_xml = get_combo_yjsm_xml(yj_list) 
            try:
                response = post_yjsm_request(post_xml.encode('utf8'))
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                raise updateYundaOrderAddrTask.retry(exc=exc,countdown=60)
            
            MergeTrade.objects.filter(id__in=yj_ids).update(is_charged=True,charge_time=dt)
            
            yj_list = []
            yj_ids.clear() 
    
        
######################## 韵达二维码 ########################   
@task(max_retries=3)
def cancelUnusedYundaSid(cday=1):
    """ 取消系统内未使用的韵达二维码单号 """
    
    today    = datetime.datetime.now()
    last_day = today - datetime.timedelta(days=cday)
    
    #查询昨天到几天的所有订单
    trades = MergeTrade.objects.filter(pay_time__gt=last_day,pay_time__lt=today)
    #.filter(sys_status__in=(pcfg.WAIT_PREPARE_SEND_STATUS,pcfg.WAIT_AUDIT_STATUS))

    #获取订单编号，批量取消订单
    tradeids = [t.id for t in trades] 
    #print 'ids:',len(tradeids)
    if not tradeids:
        return            
    
    try:
        doc   = search_order(tradeids)
        
        cancelids = []
        orders = doc.xpath('/responses/response')
        for order in orders:
            status = order.xpath('status')[0].text
            mail_no = order.xpath('mailno')[0].text
            order_serial_no = order.xpath('order_serial_no')[0].text
            trade = MergeTrade.objects.get(id=order_serial_no)

            #if status=='1':print status,order_serial_no,mail_no,trade.out_sid
            
            if status != '1' and not mail_no:
                continue
                               
            lgc   = trade.logistics_company
            
            if trade.out_sid.strip() != mail_no or (lgc and lgc.code != 'YUNDA'):
                cancelids.append(order_serial_no)
        #print 'debug cancelids:',len(cancelids)
        if cancelids:
            cancel_order(cancelids)
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        raise cancelUnusedYundaSid.retry(exc=exc,countdown=30*60)
    
    
    
    
    
    
                
