import os
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from pyExcelerator import *
from shopback.orders.models import Order,Trade,Logistics,ORDER_FINISH_STATUS
from shopback.users.models import User
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime,refresh_session
from auth import apis

import logging

logger = logging.getLogger('hourly.saveorder')
BLANK_CHAR = ''
MONTH_TRADE_FILE_TEMPLATE = 'trade-month-%s.xls'

@task(max_retry=3)
def saveUserDuringOrders(user_id,days=0,s_dt_f=None,s_dt_t=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('SaveUserDuringOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    if not(s_dt_f and s_dt_t):
        dt = datetime.datetime.now()
        if days >0 :
            s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0))
            s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
        else:
            s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
            s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,dt.hour,59,59)-datetime.timedelta(0,3600,0))

    has_next = True
    cur_page = 1
    order = Order()

    while has_next:
        try:
            trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_created=s_dt_f,end_created=s_dt_t)

            trades = trades['trades_sold_get_response']
            if trades.has_key('trades'):
                for t in trades['trades']['trade']:

                    trade,state = Trade.objects.get_or_create(pk=t['tid'])
                    trade.save_trade_through_dict(user_id,t)

                    order.seller_nick = t['seller_nick']
                    order.buyer_nick  = t['buyer_nick']
                    order.trade       = trade

                    for o in t['orders']['order']:
                        for k,v in o.iteritems():
                            hasattr(order,k) and setattr(order,k,v)
                        order.save()

            has_next = trades['has_next']
            cur_page += 1
            time.sleep(5)
        except Exception,exc:
            logger.error('update trade sold task fail',exc_info=True)
            time.sleep(120)




@task()
def updateAllUserDuringOrders(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if hander_update:
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserDuringOrders(user.visitor_id,s_dt_f=update_from,s_dt_t=update_to)
        else:
            subtask(saveUserDuringOrders).delay(user.visitor_id,days=days)




@task(max_retry=3)
def saveUserDailyIncrementOrders(user_id,year=None,month=None,day=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('saveUserDailyIncrementOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    if year and month and day:
        s_dt_f = format_datetime(datetime.datetime(year,month,day,0,0,0))
        s_dt_t = format_datetime(datetime.datetime(year,month,day,23,59,59))
    else:
        dt = datetime.datetime.now()
        s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(1,0,0))
        s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0))

    has_next = True
    cur_page = 1
    order = Order()

    while has_next:
        try:
            trades = apis.taobao_trades_sold_increment_get(session=user.top_session,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_modified=s_dt_f,end_modified=s_dt_t)

            trades = trades['trades_sold_increment_get_response']
            if trades.has_key('trades'):
                for t in trades['trades']['trade']:

                    trade,state = Trade.objects.get_or_create(pk=t['tid'])
                    trade.save_trade_through_dict(user_id,t)

                    order.seller_nick = t['seller_nick']
                    order.buyer_nick  = t['buyer_nick']
                    order.trade       = trade

                    for o in t['orders']['order']:
                        for k,v in o.iteritems():
                            hasattr(order,k) and setattr(order,k,v)
                        order.save()

            has_next = trades['has_next']
            cur_page += 1
            time.sleep(3)
        except Exception,exc:
            logger.error('update trade sold increment fail',exc_info=True)
            time.sleep(120)





@task()
def updateAllUserDailyIncrementOrders(update_from=None,update_to=None):

    hander_update = update_from and update_to
    if hander_update:
        time_delta = update_to - update_from
        update_days  = time_delta.days+1

    users = User.objects.all()
    for user in users:
        if hander_update:
            for i in xrange(0,update_days):
                update_date = update_to - datetime.timedelta(i,0,0)
                saveUserDailyIncrementOrders(user.visitor_id,year=update_date.year
                                             ,month=update_date.month,day=update_date.day)
        else:
            subtask(saveUserDailyIncrementOrders).delay(user.visitor_id)




@task()
def updateOrdersAmountTask(user_id,f_dt,t_dt):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('updateOrdersAmountTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    finish_trades = Trade.objects.filter(seller_id=user_id,consign_time__gte=f_dt,consign_time__lt=t_dt,
                                         is_update_amount=False,status=ORDER_FINISH_STATUS)
    for trade in finish_trades:
        try:
            trade_amount = apis.taobao_trade_amount_get(tid=trade.id,session=user.top_session)

            if trade_amount.has_key('error_response'):
                logger.error('update trade amount fail:%s'%trade_amount)
                continue

            tamt = trade_amount['trade_amount_get_response']['trade_amount']
            trade.cod_fee = tamt['cod_fee']
            trade.total_fee = tamt['total_fee']
            trade.post_fee = tamt['post_fee']
            trade.commission_fee = tamt['commission_fee']
            trade.buyer_obtain_point_fee  = tamt['buyer_obtain_point_fee']
            trade.pay_time = parse_datetime(tamt['pay_time'])
            trade.is_update_amount = True
            trade.save()

            for o in tamt['order_amounts']['order_amount']:
                try:
                    order = Order.objects.get(oid=o['oid'])
                    order.discount_fee = o['discount_fee']
                    order.adjust_fee   = o['adjust_fee']
                    order.payment      = o['payment']
                    order.price        = o['price']
                    order.num          = o['num']
                    order.num_iid      = o['num_iid']
                    order.save()
                except Order.DoesNotExist:
                    logger.error('the order(id:%s) does not exist'%o['oid'])
            time.sleep(0.5)
        except Exception,exc:
            logger.error('%s'%exc,exc_info=True)




@task()
def updateAllUserOrdersAmountTask(days=0,dt_f=None,dt_t=None):

    hander_update = dt_f and dt_t
    if not hander_update:
        dt = datetime.datetime.now()
        dt_f = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)\
            - datetime.timedelta(days,0,0)
        dt_t = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)\
            - datetime.timedelta(1,0,0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            updateOrdersAmountTask(user.visitor_id,dt_f,dt_t)
        else:
            subtask(updateOrdersAmountTask).delay(user.visitor_id,dt_f,dt_t)





@task(max_retry=3)
def saveUserOrdersLogisticsTask(user_id,days=0,s_dt_f=None,s_dt_t=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('SaveUserDuringOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    if not(s_dt_f and s_dt_t):
        dt = datetime.datetime.now()
        s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0))
        s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))


    has_next = True
    cur_page = 1

    while has_next:
        try:

            logistics_list = apis.taobao_logistics_orders_get(session=user.top_session,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,start_created=s_dt_f,end_created=s_dt_t)

            logistics_list = logistics_list['logistics_orders_get_response']
            if logistics_list.has_key('shippings'):
                for t in logistics_list['shippings']['shipping']:

                    logistics,state = Logistics.objects.get_or_create(pk=t['tid'])
                    logistics.save_logistics_through_dict(user_id,t)

            total_nums = logistics_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1
            time.sleep(5)
        except Exception,exc:
            logger.error('update logistics fail',exc_info=True)
            time.sleep(120)




@task()
def updateAllUserOrdersLogisticsTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if hander_update:
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserOrdersLogisticsTask(user.visitor_id,s_dt_f=update_from,s_dt_t=update_to)
        else:
            subtask(saveUserOrdersLogisticsTask).delay(user.visitor_id,days=days)




def write_trades_to_sheet(sheet,trades,text_row,text_col,col_items,style_fat,data_format):
    payment_char = 'I';post_char='H';point_char='J';commission_char='K'

    for index,trade in enumerate(trades):
        row_index =  text_row+int(index)
        try:
            logistics = Logistics.objects.get(tid=trade.id)
        except Exception,exc:
            logistics = Logistics()
            logistics.out_sid = u'\u672a\u627e\u5230\uff01'
            logistics.company_name = u'\u672a\u627e\u5230\uff01'

        for data_num,data_tuple in enumerate(data_format):
            try:
                style_fat.num_format_str = data_tuple[1]
                sheet.write(row_index,text_col+int(data_num),eval(data_tuple[0]),style_fat)
            except Exception,exc:
                print exc
        formula_index = row_index+1
        earning_formula = '%s%d-%s%d-%s%d/100-%s%d'%(payment_char,formula_index,post_char,formula_index,point_char
                                                         ,formula_index,commission_char,formula_index)
        sheet.write(row_index,text_col+col_items-1,Formula(earning_formula))



def genMonthTradeStatisticXlsFile(dt_from,dt_to,file_name):

    item_names = [
            u'\u4f1a\u5458\u540d\u79f0', #buyer_nick
            u'\u6765\u6e90\u5355\u53f7', #trade_id
            u'\u53d1\u8d27\u65e5\u671f', #consign_time
            u'\u7269\u6d41\u8fd0\u5355\u53f7', #logistics_id
            u'\u7269\u6d41\u516c\u53f8',       #logisticscompany
            u'\u7269\u6d41\u8d39\u7528', #post_fee
            u'\u4ed8\u6b3e\u91d1\u989d', #payment
            u'\u79ef\u5206',             #point
            u'\u4f63\u91d1',             #commission_fee
            u'\u4ea4\u6613\u72b6\u6001',        #trade_status
            u'\u5230\u5e10\u91d1\u989d', #earnings
    ]

    data_format = [
            ('trade.buyer_nick','@'),             #C
            ('str(trade.id)','@'),                #D
            ('trade.consign_time','M/D'),         #E
            ('logistics.out_sid','general'),      #F
            ('logistics.company_name','@'),       #G
            ('float(trade.post_fee)','0.00'),     #H
            ('float(trade.payment)','0.00'),          #I
            ('int(trade.buyer_obtain_point_fee)','0'), #J
            ('float(trade.commission_fee)','0.00'),      #K
            ('trade.status','@'),                      #L
    ]

    title_col=2;title_row=1;text_col=2;text_row=2;col_items=11
    payment_char = 'I';post_char='H';point_char='J';commission_char='K';earning_char='M'

    font0 = Font()
    font0.name = 'AR PL UMing HK'
    font0.bold = True

    style0 = XFStyle()
    style0.font = font0

    w = Workbook()
    consign_trades = Trade.objects.filter(consign_time__gte=dt_from,consign_time__lte=dt_to)

    seller_ids_list = consign_trades.values('seller_id').distinct('seller_id')
    for seller_id_dict in seller_ids_list:
        seller_id = seller_id_dict['seller_id']
        seller_nick = consign_trades.filter(seller_id=seller_id)[0].seller_nick
        ws_xxsj = w.add_sheet(seller_nick)
        ws_xxsj.write_merge(0,0,0,13,u'\u53d1\u8d27\u5df2\u6210\u529f\u7684\u4ea4\u6613',style0)
        for col in xrange(0,col_items):
            ws_xxsj.write(title_row,title_col+col,item_names[col],style0)

        seller_finish_trades = consign_trades.filter(seller_id=seller_id,status=ORDER_FINISH_STATUS)
        style_fat = XFStyle()

        write_trades_to_sheet(ws_xxsj,seller_finish_trades,text_row,text_col,col_items,style_fat,data_format)

        end_row = text_row+len(seller_finish_trades)+1
        sum_start = text_row+1
        sum_end   = end_row
        post_formula = 'SUM(%s%d:%s%d)'%(post_char,sum_start,post_char,sum_end)
        payment_formula = 'SUM(%s%d:%s%d)'%(payment_char,sum_start,payment_char,sum_end)
        point_formula = 'SUM(%s%d:%s%d)'%(point_char,sum_start,point_char,sum_end)
        commission_formula = 'SUM(%s%d:%s%d)'%(commission_char,sum_start,commission_char,sum_end)
        earning_formula = 'SUM(%s%d:%s%d)'%(earning_char,sum_start,earning_char,sum_end)

        ws_xxsj.write_merge(end_row,end_row,0,6,u'%s\u5408\u8ba1\uff1a'%seller_nick,style0)
        ws_xxsj.write(end_row,7,Formula(post_formula),style0)
        ws_xxsj.write(end_row,8,Formula(payment_formula),style0)
        ws_xxsj.write(end_row,9,Formula(point_formula),style0)
        ws_xxsj.write(end_row,10,Formula(commission_formula),style0)
        ws_xxsj.write(end_row,12,Formula(earning_formula),style0)


        seller_unfinish_trades = consign_trades.filter(seller_id=seller_id).exclude(status=ORDER_FINISH_STATUS)
        ws_xxsj.write_merge(end_row+3,end_row+3,0,13,u'\u53d1\u8d27\u4f46\u672a\u5b8c\u6210\u7684\u4ea4\u6613',style0)
        if seller_unfinish_trades.count()>0:
            write_trades_to_sheet(ws_xxsj,seller_unfinish_trades,end_row+4,text_col,col_items,style_fat,data_format)

    w.save(file_name)



@task()
def updateMonthTradeXlsFileTask():

    dt = datetime.datetime.now()
    last_month_date = dt - datetime.timedelta(dt.day,0,0)
    year_month = format_year_month(last_month_date)

    file_name  = settings.DOWNLOAD_ROOT+'/'+MONTH_TRADE_FILE_TEMPLATE%year_month

    if os.path.isfile(file_name) or dt.day<10:
        return {'error':'%s is already exist or must be ten days from last month at lest!'%file_name}

    last_month_first_days = datetime.datetime(last_month_date.year,last_month_date.month,1,0,0,0)
    last_month_last_days = datetime.datetime(last_month_date.year,last_month_date.month,
                                                  last_month_date.day,23,59,59)
    excute_stage = 'start'
    try:
        updateAllUserDuringOrders(update_from=last_month_first_days,update_to=dt)
        excute_stage = 'order'
        updateAllUserOrdersAmountTask(dt_f=last_month_first_days,dt_t=dt)
        excute_stage = 'amount'
        updateAllUserOrdersLogisticsTask(update_from=last_month_first_days,update_to=dt)
        excute_stage = 'logistics'
        genMonthTradeStatisticXlsFile(last_month_first_days,last_month_last_days,file_name)
        excute_stage = 'file'
    except Exception,exc:
        logger.error('updateMonthTradeXlsFileTask excute error.',exc_info=True)
        return {'error':'%s'%exc,'stage':excute_stage}

    return {'update_from':last_month_first_days,'update_to':last_month_last_days}





