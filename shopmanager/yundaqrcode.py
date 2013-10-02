#-*- coding:utf8 -*-
import sys
import json
import hashlib
import base64
import time
import datetime
import urllib
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopapp.shipclassify.options import get_addr_zones
from shopback.trades.models import MergeTrade

#demon_url = 'http://orderdev.yundasys.com:10209/cus_order/order_interface/'
demon_url = 'http://order.yundasys.com:10235/cus_order/order_interface/'

RECEIVE   = 'receive'
MODIFY    = 'modify'
CANCEL    = 'cancel'
REPRINT   = 'reprint'
VALID     = 'valid'
ACCEPT    = 'accept'
TRANSITE  = 'transite'
ORDERINFO = 'orderinfo'

RECEIVE_ACTION = 'data'
CANCEL_ACTION = 'cancel_order'
REPRINT_ACTION = 'reprint_order'
VALID_ACTION = 'valid_order'
ACCEPT_ACTION = 'accept_order'
TRANSITE_ACTION = 'transite_info'

RECEIVE_API   = 'interface_receive_order.php' 
MODIFY_API    = 'interface_modify_order.php'
CANCEL_API    = 'interface_cancel_order.php'
TRANSITE_API  = 'interface_transite_search.php'
ORDERINFO_API = 'interface_order_info.php'
PRINTFILE_API = 'interface_print_file.php'


ACTION_DICT = {
               RECEIVE:RECEIVE_ACTION,
               MODIFY:RECEIVE_ACTION,
               CANCEL:CANCEL_ACTION,
               ORDERINFO:RECEIVE_ACTION,
               TRANSITE:TRANSITE_ACTION,
               VALID:VALID_ACTION,
               REPRINT:REPRINT_ACTION,
               }

API_DICT = {
               RECEIVE:RECEIVE_API,
               MODIFY:RECEIVE_API,
               CANCEL:CANCEL_API,
               ORDERINFO:RECEIVE_API,
               TRANSITE:TRANSITE_API,
               VALID:CANCEL_API,
               REPRINT:PRINTFILE_API,
               }

PARTNER_ID = "10134210001"
SECRET     = "123456"


################ 创建订单请求 ###############
def gen_orders_xml(objs):
    
    _xml_list = ['<order>']

    for obj in objs:
        _xml_list.append('<order>')
        _xml_list.append('<order_serial_no>%s</order_serial_no>'%obj['id'])
        _xml_list.append('<khddh>%s</khddh>'%obj['id'])
        _xml_list.append('<nbckh></nbckh>')
        _xml_list.append("""<sender><name>%s</name><company>%s</company>
                            <city>%s</city><address>%s</address>
                            <postcode>%s</postcode><phone>%s</phone>
                            <mobile>%s</mobile><branch></branch></sender>"""%(obj['sender_name'],
                                                                                obj['sender_company'],
                                                                                obj['sender_city'],
                                                                                obj['sender_address'],
                                                                                obj['sender_postcode'],
                                                                                obj['sender_phone'],
                                                                                obj['sender_mobile'],
                                                                                ))
        
        _xml_list.append("""<receiver><name>%s</name><company>%s</company>
                            <city>%s</city><address>%s</address>
                            <postcode>%s</postcode><phone>%s</phone>
                            <mobile>%s</mobile><branch></branch></receiver>"""%(obj['receiver_name'],
                                                                                obj['receiver_company'],
                                                                                obj['receiver_city'],
                                                                                obj['receiver_address'],
                                                                                obj['receiver_postcode'],
                                                                                obj['receiver_phone'],
                                                                                obj['receiver_mobile'],
                                                                                ))
 
        _xml_list.append('<weight></weight><size></size><value></value>')
        _xml_list.append('<collection_value></collection_value><special></special>')
        _xml_list.append('<item></item><remark></remark>')
        _xml_list.append(u'<cus_area1>订单号:%s</cus_area1>'%obj['id'])
        _xml_list.append('<cus_area2>%s</cus_area2>'%obj['zone'])
        _xml_list.append('<callback_id>abcdefg</callback_id>')
        _xml_list.append('<wave_no>abcdefg</wave_no></order>')
        
    _xml_list.append('</order>')
    
    return ''.join(_xml_list).encode('utf8')
    
def get_objs_from_trade(trades):
    
    objs = []
    for trade in trades:
        
        zone = get_addr_zones(trade.receiver_state,trade.receiver_city,trade.receiver_district)
        
        objs.append({"id":trade.id,
                     "sender_name":u"优尼世界",
                     "sender_company":u"优尼世界旗舰店",
                     "sender_city":u"上海,上海市",
                     "sender_address":u"",
                     "sender_postcode":u"",
                     "sender_phone":u"",
                     "sender_mobile":u"",
                     "receiver_name":trade.receiver_name,
                     "receiver_company":u'',
                     "receiver_city":','.join([trade.receiver_state,trade.receiver_city,trade.receiver_district]),
                     "receiver_address":','.join([trade.receiver_state,trade.receiver_city,trade.receiver_district+trade.receiver_address]),
                     "receiver_postcode":trade.receiver_zip,
                     "receiver_phone":trade.receiver_phone,
                     "receiver_mobile":trade.receiver_mobile,
                     "zone":zone and zone.code or ''
                     })
        
    return objs
       
def handle_demon(action,xml_data,partner_id,secret):
    
    xml_data  = base64.encodestring(xml_data).strip()
    validate = hashlib.md5(xml_data+partner_id+secret).hexdigest()
    
    params = {'partnerid':partner_id,
          'version':'1.0',
          'request':ACTION_DICT[action],
          'xmldata':xml_data,
          'validation':validate
          }
    
    req = urllib2.urlopen(demon_url+API_DICT[action], urllib.urlencode(params), timeout=60)
    rep = req.read()       
    
    parser = etree.XMLParser()
    tree   = etree.parse(StringIO(rep), parser)
    
    ds = tree.xpath('/responses/response/status')
    status = ds[0].text
    
    print 'rep',rep.decode('utf8')
    if status != '1':
        raise Exception(rep)
    
    return tree
     
     
def create_order(id):
    
    trade = MergeTrade.objects.get(id=id)
 
    objs  = get_objs_from_trade([trade])
    
    order_xml = gen_orders_xml(objs)
    
    tree = handle_demon(RECEIVE,order_xml,PARTNER_ID,SECRET)
    
    return tree

def modify_order(id):
    
    trade = MergeTrade.objects.get(id=id)
 
    objs  = get_objs_from_trade([trade])
    
    order_xml = gen_orders_xml(objs)
    
    tree = handle_demon(MODIFY,order_xml,PARTNER_ID,SECRET)
    
    return tree
    
def cancel_order(id):
    
    order_xml = "<orders><order><order_serial_no>%s</order_serial_no></order></orders>"%str(id)
    
    tree = handle_demon(CANCEL,order_xml,PARTNER_ID,SECRET)
    
    return tree
    
def search_order(id):
    
    order_xml = """<orders><order><order_serial_no>%s</order_serial_no></order></orders>"""%str(id)
    
    tree = handle_demon(ORDERINFO,order_xml,PARTNER_ID,SECRET)
    
    return tree


def valid_order(id):
    
    order_xml = """<orders><order><order_serial_no>%s</order_serial_no></order></orders>"""%str(id)
    
    tree = handle_demon(VALID,order_xml,PARTNER_ID,SECRET)
    
    return tree


def print_order(id):
    
    order_xml = """<orders><order><order_serial_no>%s</order_serial_no></order></orders>"""%str(id)
    
    tree = handle_demon(REPRINT,order_xml,PARTNER_ID,SECRET)
    
    return tree
    
if __name__ == '__main__':
    
    print sys.argv
    id     = sys.argv[1]
    option = sys.argv[2]
    if option == '1':
        create_order(id)
    
    if option == '2':
        modify_order(id)
         
    if option == '3':
        cancel_order(id)

    if option == '4':
        search_order(id)
        
    if option == '5':
        valid_order(id)
        
    if option == '6':
        print_order(id)
    
    #resave_order()
    #cancel_order()
    #request_print()   
