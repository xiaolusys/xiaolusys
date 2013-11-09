#-*- coding:utf-8 -*-
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade
from shopback.fenxiao.models import PurchaseOrder,SubPurchaseOrder
from shopback.monitor.models import SystemConfig
from shopback.users.models import User
from auth.utils import format_datetime
import MySQLdb
import logging

logger = logging.getLogger('trades.handler')

DB_HOST  = 'hzw01.rds.aliyuncs.com'
DB_USER  = 'jusrmn8bk5mn'
DB_PWD   = 'Iu4N_uO6A'
DB_NAME  = 'sys_info'


class DBConnect:
    def __init__(self,host=DB_HOST,user=DB_USER,pwd=DB_PWD,name=DB_NAME,charset='utf8'):
        
        self.host = host
        self.user = user
        self.pwd  = pwd
        self.name = name
        self.charset= charset
        self.conn = None
        
    def __enter__(self):
        self.conn = MySQLdb.connect(host=self.host, # your host, usually localhost
                             user=self.user, # your username
                             passwd=self.pwd, # your password
                             db=self.name,
                             charset=self.charset) # name of the data base
        return self.conn
    
    def __exit__(self, type, msg, traceback):
        
        if self.conn:
            try:
                self.conn.commit()
            except:
                self.conn.rollback()
            
            self.conn.close()
            
@task()
def pull_taobao_trade_task():
    
    dt = datetime.datetime.now()
    sysconf = SystemConfig.getconfig()
    df  = sysconf.mall_order_updated
    
    cells = ()
    with DBConnect() as conn:
        
        cur = conn.cursor()
        cur.execute("SELECT tid,seller_nick,jdp_response from jdp_tb_trade where jdp_modified > %s and jdp_modified < %s",
                    (format_datetime(df),
                     format_datetime(dt)))
        cells = cur.fetchall()
        cur.close()
    
    for cell in cells:
        try:
            tid = cell[0]
            seller_nick = cell[1]
            trade_dict  = json.loads(cell[2])
            
            seller_id   = User.objects.get(nick=seller_nick).visitor_id
            
            Trade.save_trade_through_dict(seller_id,trade_dict['trade_fullinfo_get_response']['trade'])
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
    
    sysconf.mall_order_updated = dt
    sysconf.save()
        
@task()
def pull_fenxiao_trade_task(): 
       
    dt = datetime.datetime.now()
    sysconf = SystemConfig.getconfig()
    df  = sysconf.fenxiao_order_updated
    
    cells = ()
    with DBConnect() as conn:
        
        cur = conn.cursor()
        cur.execute("SELECT fenxiao_id,supplier_username,jdp_response from jdp_fx_trade where jdp_modified > %s and jdp_modified < %s",
                    (format_datetime(df),
                     format_datetime(dt)))
        cells = cur.fetchall()
        cur.close()
    
    for cell in cells:
        try:
            tid = cell[0]
            seller_nick = cell[1]
            trade_dict  = json.loads(cell[2])
            print tid,seller_nick
            return seller_nick
            seller_id   = User.objects.get(nick=seller_nick).id
            
            PurchaseOrder.save_order_through_dict(seller_id,trade_dict[''])
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            
            
            