# -*- coding:utf8 -*-
""" 
韵达二维码对接接口
"""
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
from common.utils import valid_xml_string

from shopapp.yunda.options import get_addr_zones
from shopback.trades.models import MergeTrade

# demon_url = 'http://orderdev.yundasys.com:10209/cus_order/order_interface/'
demon_url = 'http://order.yundasys.com:10235/cus_order/order_interface/'

SELECT = 'select'
RECEIVE = 'receive'
RECEIVE_MAILNO = 'receive_mailno'
MODIFY = 'modify'
CANCEL = 'cancel'
REPRINT = 'reprint'
VALID = 'valid'
ACCEPT = 'accept'
TRANSITE = 'transite'
ORDERINFO = 'orderinfo'

RECEIVE_ACTION = 'data'
CANCEL_ACTION = 'cancel_order'
REPRINT_ACTION = 'reprint_order'
VALID_ACTION = 'valid_order'
ACCEPT_ACTION = 'accept_order'
TRANSITE_ACTION = 'transite_info'

SELECT_API = 'interface_select_reach_package.php'
RECEIVE_API = 'interface_receive_order.php'
MODIFY_API = 'interface_modify_order.php'
CANCEL_API = 'interface_cancel_order.php'
TRANSITE_API = 'interface_transite_search.php'
ORDERINFO_API = 'interface_order_info.php'
PRINTFILE_API = 'interface_print_file.php'
RECEIVER_MAILNO_API = 'interface_receive_order__mailno.php'

ACTION_DICT = {
    SELECT: RECEIVE_ACTION,
    RECEIVE: RECEIVE_ACTION,
    MODIFY: RECEIVE_ACTION,
    CANCEL: CANCEL_ACTION,
    ORDERINFO: RECEIVE_ACTION,
    TRANSITE: TRANSITE_ACTION,
    VALID: VALID_ACTION,
    REPRINT: REPRINT_ACTION,
    RECEIVE_MAILNO: RECEIVE_ACTION,
}

API_DICT = {
    SELECT: SELECT_API,
    RECEIVE: RECEIVE_API,
    MODIFY: MODIFY_API,
    CANCEL: CANCEL_API,
    ORDERINFO: ORDERINFO_API,
    TRANSITE: TRANSITE_API,
    VALID: CANCEL_API,
    REPRINT: PRINTFILE_API,
    RECEIVE_MAILNO: RECEIVER_MAILNO_API,
}

PARTNER_ID = "YUNDA"
SECRET = "123456"


################ 创建订单请求 ###############
def gen_orders_xml(objs):
    _xml_list = ['<orders>']

    for obj in objs:
        _xml_list.append('<order>')
        _xml_list.append('<order_serial_no>%s</order_serial_no>' % obj['id'])
        _xml_list.append('<khddh>%s</khddh>' % obj['id'])
        _xml_list.append('<nbckh></nbckh>')
        _xml_list.append("""<sender><name>%s</name><company>%s</company>
                            <city>%s</city><address>%s</address>
                            <postcode>%s</postcode><phone>%s</phone>
                            <mobile>%s</mobile><branch></branch></sender>""" % (obj['sender_name'],
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
                            <mobile>%s</mobile><branch></branch></receiver>""" % (obj['receiver_name'],
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
        _xml_list.append(u'<cus_area1>分拣号:%s</cus_area1>' % obj['zone'])
        _xml_list.append(u'<cus_area2>宝贝妈咪移动不便，请快递大哥帮忙送到家啦，谢谢!</cus_area2>')
        _xml_list.append('<callback_id></callback_id>')
        _xml_list.append('<wave_no></wave_no></order>')

    _xml_list.append('</orders>')

    return ''.join(_xml_list).encode('utf8')


def gen_select_xml(objs):
    _xml_list = ['<orders>']

    for obj in objs:
        _xml_list.append('<order>')
        _xml_list.append('<id>%s</id>' % obj['id'])
        _xml_list.append('<sender_address>%s</sender_address>' % ','.join([obj['sender_city'], obj['sender_address']]))
        _xml_list.append('<receiver_address>%s</receiver_address>' % obj['receiver_address'])
        _xml_list.append('</order>')

    _xml_list.append('</orders>')

    return ''.join(_xml_list).encode('utf8')


def get_objs_from_trade(trades):
    objs = []
    for trade in trades:
        zone = get_addr_zones(trade.receiver_state, trade.receiver_city, trade.receiver_district)

        objs.append({"id": trade.id,
                     "sender_name": u"优尼世界",
                     "sender_company": u"优尼世界旗舰店",
                     "sender_city": u"上海,上海市",
                     "sender_address": u"",
                     "sender_postcode": u"",
                     "sender_phone": u"021-37698479",
                     "sender_mobile": u"",
                     "receiver_name": valid_xml_string(trade.receiver_name),
                     "receiver_company": u'',
                     "receiver_city": valid_xml_string(
                         ','.join([trade.receiver_state, trade.receiver_city, trade.receiver_district])),
                     "receiver_address": valid_xml_string(','.join([trade.receiver_state, trade.receiver_city, (
                     trade.receiver_district + trade.receiver_address)])),
                     "receiver_postcode": valid_xml_string(trade.receiver_zip),
                     "receiver_phone": valid_xml_string(trade.receiver_phone),
                     "receiver_mobile": valid_xml_string(trade.receiver_mobile),
                     "zone": zone and zone.code or ''
                     })

    return objs


def parseTreeID2MailnoMap(doc):
    """ 订单查询结果转换成字典 """
    im_map = {}
    orders = doc.xpath('/responses/response')
    for order in orders:
        status = order.xpath('status')[0].text
        order_mail_no = order.xpath('mailno')

        if status != '1' and not order_mail_no:
            continue

        order_serial_no = order.xpath('order_serial_no')[0].text
        mailno = order_mail_no[0].text

        im_map[order_serial_no] = mailno

    return im_map


def handle_demon(action, xml_data, partner_id, secret):
    xml_data = base64.encodestring(xml_data).strip()
    validate = hashlib.md5(xml_data + partner_id + secret).hexdigest()

    params = {'partnerid': partner_id,
              'version': '1.0',
              'request': ACTION_DICT[action],
              'xmldata': xml_data,
              'validation': validate
              }

    req = urllib2.urlopen(demon_url + API_DICT[action], urllib.urlencode(params), timeout=60)
    rep = req.read()

    if action == REPRINT:
        return rep

    parser = etree.XMLParser()
    tree = etree.parse(StringIO(rep), parser)

    return tree


def select_order(ids):
    assert isinstance(ids, (list, tuple))

    trades = MergeTrade.objects.filter(id__in=ids)

    objs = get_objs_from_trade(trades)

    order_xml = gen_select_xml(objs)

    tree = handle_demon(SELECT, order_xml, PARTNER_ID, SECRET)

    return tree


def create_order(ids):
    assert isinstance(ids, (list, tuple))

    trades = MergeTrade.objects.filter(id__in=ids)

    objs = get_objs_from_trade(trades)

    order_xml = gen_orders_xml(objs)

    tree = handle_demon(RECEIVE_MAILNO, order_xml, PARTNER_ID, SECRET)

    return tree


def create_order_ret_mailno(ids):
    assert isinstance(ids, (list, tuple))

    trades = MergeTrade.objects.filter(id__in=ids)

    objs = get_objs_from_trade(trades)

    order_xml = gen_orders_xml(objs)

    tree = handle_demon(RECEIVE_MAILNO, order_xml, PARTNER_ID, SECRET)

    return tree


def modify_order(ids, partner_id=PARTNER_ID, secret=SECRET):
    assert isinstance(ids, (list, tuple))

    trades = MergeTrade.objects.filter(id__in=ids)

    objs = get_objs_from_trade(trades)

    order_xml = gen_orders_xml(objs, partner_id, secret)

    tree = handle_demon(MODIFY, order_xml, PARTNER_ID, SECRET)

    return tree


def cancel_order(ids, partner_id=PARTNER_ID, secret=SECRET):
    assert isinstance(ids, (list, tuple))

    order_xml = "<orders>"

    for i in ids:
        order_xml += "<order><order_serial_no>%s</order_serial_no></order>" % str(i)

    order_xml += "</orders>"

    tree = handle_demon(CANCEL, order_xml, partner_id, secret)

    return tree


def search_order(ids, partner_id=PARTNER_ID, secret=SECRET):
    assert isinstance(ids, (list, tuple))

    order_xml = "<orders>"

    for i in ids:
        order_xml += "<order><order_serial_no>%s</order_serial_no></order>" % str(i)

    order_xml += "</orders>"

    tree = handle_demon(ORDERINFO, order_xml, partner_id, secret)

    return tree


def valid_order(ids):
    assert isinstance(ids, (list, tuple))

    order_xml = "<orders>"

    for i in ids:
        order_xml += "<order><order_serial_no>%s</order_serial_no></order>" % str(i)

    order_xml += "</orders>"

    tree = handle_demon(VALID, order_xml, PARTNER_ID, SECRET)

    return tree


def print_order(ids):
    assert isinstance(ids, (list, tuple))

    order_xml = "<orders>"

    for i in ids:
        order_xml += "<order><order_serial_no>%s</order_serial_no></order>" % i

    order_xml += "</orders>"

    tree = handle_demon(REPRINT, order_xml, PARTNER_ID, SECRET)

    return tree


if __name__ == '__main__':

    print sys.argv
    id = sys.argv[1]
    option = sys.argv[2]
    if option == '1':
        create_order([id])

    if option == '2':
        modify_order([id])

    if option == '3':
        cancel_order([id])

    if option == '4':
        search_order([id])

    if option == '5':
        valid_order([id])

    if option == '6':
        print_order([id])

    if option == '7':
        create_order_ret_mailno([id])

    if option == '8':
        select_order([id])

        # resave_order()
        # cancel_order()
        # request_print()
