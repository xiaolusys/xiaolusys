# coding=utf-8
__author__ = 'meron'
import os, sys, string
import MySQLdb
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from django.contrib.auth.models import User
from flashsale.pay.models import SaleTrade, SaleOrder ,Customer ,UserAddress
from flashsale.pay.tasks import notifyTradePayTask
import logging
logger = logging.getLogger(__name__)

TMPDB_HOST = 'staging.xiaolumm.com'
TMPDB_PORT = 30001
TMPDB_USER = 'qiyue'
TMPDB_PWD = 'youni_2014qy'

USER_FIELDS = ['id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined']

BUYER_FIELDS = ['created', 'modified', 'id', 'nick', 'thumbnail', 'mobile', 'email', 'phone', 'openid', 'unionid', 'status', 'user_id']

TRADE_FIELDS = ['created', 'modified', 'id', 'tid', 'buyer_id', 'buyer_nick', 'channel', 'payment', 'pay_cash',
                'post_fee', 'discount_fee', 'total_fee', 'has_budget_paid', 'buyer_message', 'seller_memo', 'pay_time',
                'consign_time', 'trade_type', 'order_type', 'out_sid', 'receiver_name', 'receiver_state',
                'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                'receiver_phone', 'user_address_id', 'openid', 'charge', 'extras_info', 'status',
                'logistics_company_id']

ORDER_FIELDS = ['created', 'modified', 'id', 'oid', 'item_id', 'title', 'price', 'sku_id', 'num', 'outer_id',
                'outer_sku_id', 'total_fee', 'payment', 'discount_fee', 'sku_name', 'pic_path', 'pay_time',
                'consign_time', 'sign_time', 'refund_id', 'refund_fee', 'refund_status', 'status', 'sale_trade_id',
                'buyer_id', 'extras']

def get_temp_conn():
    try:
        conn = MySQLdb.connect(host=TMPDB_HOST, port=TMPDB_PORT, user=TMPDB_USER, passwd=TMPDB_PWD, db='xiaoludb',charset="utf8")
        return conn
    except Exception, e:
        print e
        sys.exit()

def get_temp_trade_list():
    tmp_conn = get_temp_conn()
    t_cursor = tmp_conn.cursor()
    t_cursor.execute(
        "select %s from flashsale_trade where pay_time > '2016-05-15 00:00:00' " % (','.join(TRADE_FIELDS)))

    trade_tuples = t_cursor.fetchall()

    trade_dict_list = []
    for trade in trade_tuples:

        trade_dict = dict(zip(TRADE_FIELDS, trade))
        t_cursor.execute(
            "select %s from flashsale_order where sale_trade_id=%d " % (','.join(ORDER_FIELDS), trade_dict['id']))

        order_dict_list = []
        order_list = t_cursor.fetchall()
        for order in order_list:
            order_dict = dict(zip(ORDER_FIELDS, order))
            order_dict_list.append(order_dict)

        trade_dict['sale_orders'] = order_dict_list
        trade_dict_list.append(trade_dict)

    t_cursor.close()
    tmp_conn.close()
    return trade_dict_list

def get_or_create_customer(buyer_id):
    cus_conn = get_temp_conn()
    t_cursor = cus_conn.cursor()
    t_cursor.execute(
        "select %s from flashsale_customer where id=%d " % (','.join(BUYER_FIELDS), buyer_id))
    buyer_tuple = t_cursor.fetchone()
    buyer_dict = dict(zip(BUYER_FIELDS, buyer_tuple))
    t_cursor.execute(
        "select %s from auth_user where id=%d " % (','.join(USER_FIELDS), buyer_dict['user_id']))
    user_tuple = t_cursor.fetchone()
    user_dict = dict(zip(USER_FIELDS, user_tuple))
    t_cursor.close()
    cus_conn.close()
    buyer = Customer.objects.normal_customer.filter(unionid=buyer_dict['unionid']).first()
    if buyer:
        return buyer
    user = User.objects.filter(username=buyer_dict['unionid']).first()
    if not user:
        user = User()
        for k,v in user_dict.items():
            setattr(user,k,v)
        user.id = None
        user.save()
    buyer = Customer()
    for k,v in buyer_dict.items():
        setattr(buyer,k,v)
    buyer.id = None
    buyer.user = user
    buyer.save()
    return buyer

def update_address(addr_dict):
    address  = UserAddress.objects.filter(cus_uid=addr_dict['cus_uid'],
                                         receiver_name=addr_dict['receiver_name'],
                                         receiver_state=addr_dict['receiver_state'],
                                         receiver_mobile=addr_dict['receiver_mobile'],
                                         ).first()
    if address:
        return address

    address = UserAddress()
    for k,v in addr_dict.items():
        setattr(address,k,v)
    address.save()
    return address

import pingpp
pingpp.api_key = settings.PINGPP_APPKEY

def update_charge(charge_id):
    resp = pingpp.Charge.retrieve(charge_id)
    notifyTradePayTask(resp)

class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.debug('recover_saletrade_and_orders start ...')
        trade_list = get_temp_trade_list()
        logger.debug('debug temp trades len: %d'% len(trade_list) )
        logger.debug('trade dict:%s'% trade_list[0])

        for trade_dict in trade_list:
            buyer = get_or_create_customer(trade_dict['buyer_id'])
            addr_dict = {
                'cus_uid':buyer.id,
                'receiver_name':trade_dict['receiver_name'],
                'receiver_state': trade_dict['receiver_state'],
                'receiver_city': trade_dict['receiver_city'],
                'receiver_district': trade_dict['receiver_district'],
                'receiver_address': trade_dict['receiver_address'],
                'receiver_zip': trade_dict['receiver_zip'],
                'receiver_mobile': trade_dict['receiver_mobile'],
                'receiver_phone': trade_dict['receiver_phone'],
                'default': True,
            }
            update_address(addr_dict)

            strade = SaleTrade.objects.filter(tid=trade_dict['tid']).first()
            if strade:
               continue

            st = SaleTrade()
            for k,v in trade_dict.items():
                if k in ('id','sale_orders'):continue
                setattr( st, k, v)
            st.id = None
            st.buyer_id = buyer.id
            st.save()

            for order_dict in trade_dict['sale_orders']:
                so = SaleOrder()
                for k, v in order_dict.items():
                    setattr(so, k, v)
                so.id = None
                so.sale_trade = st
                so.save()

            try:
                update_charge(st.charge)
            except Exception,exc:
                logging.error('notify trade charge error:%s'%exc.message)




