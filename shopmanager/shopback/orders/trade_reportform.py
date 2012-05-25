import datetime
from pyExcelerator import Workbook,XFStyle,Font,Formula
from shopback.orders.models import Order,Trade,Refund,Logistics,PurchaseOrder,ORDER_SUCCESS_STATUS,REFUND_WILL_STATUS

item_names = [
    u'\u4f1a\u5458\u540d\u79f0', #buyer_nick
    u'\u6765\u6e90\u5355\u53f7(\u5206\u9500ID)', #trade_id
    u'\u53d1\u8d27\u65e5\u671f', #consign_time
    u'\u7269\u6d41\u8fd0\u5355\u53f7', #logistics_id
    u'\u7269\u6d41\u516c\u53f8',       #logisticscompany
    u'\u7269\u6d41\u8d39\u7528', #post_fee
    u'\u4ed8\u6b3e\u91d1\u989d', #payment
    u'\u79ef\u5206',             #point
    u'\u4f63\u91d1',             #commission_fee
    u'\u4ea4\u6613\u72b6\u6001', #trade_status
    u'\u5230\u5e10\u91d1\u989d', #earnings
]

refund_item_names =[
    u'\u4f1a\u5458\u540d\u79f0', #buyer_nick
    u'\u9000\u6b3e\u5355ID',     #refund_id
    u'\u4ea4\u6613ID',           #tid
    u'\u8ba2\u5355ID',           #oid
    u'\u9000\u8d27\u8fd0\u5355\u53f7', #sid
    u'\u7269\u6d41\u516c\u53f8',  #company_name
    u'\u9000\u8d27\u65f6\u95f4',  #created
    u'\u603b\u91d1\u989d',       #total_fee
    u'\u5b9e\u4ed8\u91d1\u989d', #payment
    u'\u9000\u6b3e\u91d1\u989d', #refund_fee
    u'\u9000\u8d27\u539f\u56e0', #reason
    u'\u5546\u54c1\u9000\u56de', #has_good_return
    u'\u5546\u54c1\u72b6\u6001', #good_status
    u'\u8ba2\u5355\u72b6\u6001', #order_status
    u'\u9000\u8d27\u72b6\u6001', #status
]

data_format = [
    ('trade.buyer_nick','@'),             #C
    ('str(trade.id)','@'),                #D
    ('trade.consign_time','M/D'),         #E
    ('logistics.out_sid','general'),      #F
    ('logistics.company_name','@'),       #G
    ('float(trade.post_fee)','0.00'),     #H
    ('float(trade.payment)','0.00'),           #I
    ('int(trade.buyer_obtain_point_fee)','0'), #J
    ('float(trade.commission_fee)','0.00'),    #K
    ('trade.status','@'),                      #L
]


purchase_format = [
    ('trade.distributor_username','@'),           #C
    ('str(trade.fenxiao_id)','@'),                #D
    ('trade.consign_time','M/D'),                 #E
    ('trade.logistics_id','general'),             #F
    ('trade.logistics_company_name','@'),         #G
    ('float(trade.post_fee)','0.00'),             #H
    ('float(trade.distributor_payment)','0.00'),  #I
    ('int(0)','0'),                               #J
    ('int(0)','0.00'),                            #K
    ('trade.status','@'),                         #L
]

refund_format = [
    ('refund.buyer_nick','@'),          #C
    ('str(refund.refund_id)','@'),      #D
    ('str(refund.trade)','@'),          #E
    ('str(refund.oid)','@'),            #F
    ('str(refund.sid)','@'),            #G
    ('refund.company_name','@'),        #H
    ('refund.created','M/D'),           #I
    ('float(refund.total_fee)','0.00'),    #J
    ('float(refund.payment)','0.00'),      #K
    ('float(refund.refund_fee)','0.00'),   #L
    ('refund.reason','@'),                 #M
    ('str(refund.has_good_return)','@'),   #N
    ('refund.good_status','@'),            #O
    ('refund.order_status','@'),           #P
    ('refund.status','@'),                 #Q
]

title_col=2;title_row=1;text_col=2;text_row=2;col_items=11;refund_fee_row=11;
payment_char='I';post_char='H';point_char='J';commission_char='K';earning_char='M';refund_char='L';

TRADE_FINISH_MSG  = u'\u53d1\u8d27\u5df2\u6210\u529f\u7684\u4ea4\u6613'
TRADE_POST_UNFINISH_MSG = u'\u53d1\u8d27\u4f46\u672a\u5b8c\u6210\u7684\u4ea4\u6613'
TRADE_FENXIAO_MSG = u'\u6765\u81ea\u6dd8\u5b9d\u5206\u9500\u7684\u8ba2\u5355'
SELLER_TRADE_ACCOUNT_MSG = u'%s\u5408\u8ba1\uff1a'
TRADE_REFUND_MSG  = u'\u90e8\u5206\u9000\u6b3e\u4ea4\u6613(\u5305\u542b\u5546\u57ce\u4e0e\u5206\u9500)'
TRADE_REFUND_ACCOUNT_MSG = u'%s\u9000\u6b3e\u91d1\u989d\u5408\u8ba1'
SELLER_TOTAL_INCOME_MSG  = u'%s\u4e70\u5bb6\u5b9e\u4ed8\u6b3e-\u90ae\u8d39-\u79ef\u5206/100-\u4f63\u91d1-\u90e8\u5206\u9000\u6b3e\u91d1\u989d'

TOTAL_STATISTIC  = [u'\u603b\u9500\u552e\u989d',u'\u90ae\u8d39',u'\u79ef\u5206',u'\u4f63\u91d1',u'\u9000\u6b3e',u'\u5230\u5e10\u91d1\u989d']


def write_trades_to_sheet(sheet,trades,text_row,text_col,col_items,style_fat):

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



def write_purchase_to_sheet(sheet,trades,text_row,text_col,col_items,style_fat):

    for index,trade in enumerate(trades):
        row_index =  text_row+int(index)

        for data_num,data_tuple in enumerate(purchase_format):
            try:
                style_fat.num_format_str = data_tuple[1]
                sheet.write(row_index,text_col+int(data_num),eval(data_tuple[0]),style_fat)
            except Exception,exc:
                pass
        formula_index = row_index+1
        earning_formula = '%s%d-%s%d-%s%d/100-%s%d'%(payment_char,formula_index,post_char,formula_index,point_char
                                                         ,formula_index,commission_char,formula_index)
        sheet.write(row_index,text_col+col_items-1,Formula(earning_formula))



def write_refund_to_sheet(sheet,refunds,text_row,text_col,col_items,style_fat):

    for index,refund in enumerate(refunds):
        row_index =  text_row+int(index)

        for data_num,data_tuple in enumerate(refund_format):
            try:
                style_fat.num_format_str = data_tuple[1]
                sheet.write(row_index,text_col+int(data_num),eval(data_tuple[0]),style_fat)
            except Exception,exc:
                print exc




def write_sum_formula(sheet,row,col,sum_start_row,sum_end_row,row_char,style=XFStyle()):
    sum_formula = 'SUM(%s%d:%s%d)'%(row_char,sum_start_row,row_char,sum_end_row)
    sheet.write(row,col,Formula(sum_formula),style)


def write_seller_formula(sheet,row,col,sum_row,sum_name,sum_char,style=XFStyle()):
    sheet.write(row,col,sum_name,style)
    sell_formula = '%s%d'%(sum_char,sum_row)
    sheet.write(row,col+1,Formula(sell_formula),style)




def genMonthTradeStatisticXlsFile(dt_from,dt_to,file_name):

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
        #taobao trades
        ws_xxsj.write_merge(0,0,0,13,TRADE_FINISH_MSG,style0)
        for col in xrange(0,col_items):
            ws_xxsj.write(title_row,title_col+col,item_names[col],style0)

        seller_finish_trades = consign_trades.filter(
                seller_id=seller_id,status__in=ORDER_SUCCESS_STATUS)
        style_fat = XFStyle()

        write_trades_to_sheet(ws_xxsj,seller_finish_trades,text_row,text_col,col_items,style_fat)
        end_row = text_row+len(seller_finish_trades)

        ws_xxsj.write_merge(end_row,end_row,0,1,TRADE_FENXIAO_MSG,style0)
        seller_purchase_trades = PurchaseOrder.objects.filter(
                seller_id=seller_id,consign_time__gte=dt_from
                ,consign_time__lte=dt_to,status__in = ORDER_SUCCESS_STATUS)
        #fenxiao trades
        purchase_trades_len =  seller_purchase_trades.count()
        if purchase_trades_len>0:
            write_purchase_to_sheet(ws_xxsj,seller_purchase_trades,end_row+1,text_col,col_items,style_fat)

        end_row = end_row+purchase_trades_len+1

        ws_xxsj.write_merge(end_row,end_row,0,6,SELLER_TRADE_ACCOUNT_MSG%seller_nick,style0)

        sum_start = text_row+1
        sum_end   = end_row
        total_trade_sum_row = end_row+1

        write_sum_formula(ws_xxsj,end_row,7,sum_start,sum_end,post_char,style=style0)
        write_sum_formula(ws_xxsj,end_row,8,sum_start,sum_end,payment_char,style=style0)
        write_sum_formula(ws_xxsj,end_row,9,sum_start,sum_end,point_char,style=style0)
        write_sum_formula(ws_xxsj,end_row,10,sum_start,sum_end,commission_char,style=style0)
        write_sum_formula(ws_xxsj,end_row,12,sum_start,sum_end,earning_char,style=style0)

        #refund trades
        ws_xxsj.write_merge(end_row+1,end_row+1,0,13,TRADE_REFUND_MSG,style0)

        for col in xrange(0,len(refund_item_names)):
            ws_xxsj.write(end_row+2,title_col+col,refund_item_names[col],style0)
        end_row = end_row + 3
        seller_refund_trades   = Refund.objects.filter(seller_id=seller_id,trade__consign_time__gte=dt_from,
                trade__consign_time__lt=dt_to,status__in=REFUND_WILL_STATUS,trade__status__in = ORDER_SUCCESS_STATUS)
        write_refund_to_sheet(ws_xxsj,seller_refund_trades,end_row,text_col,col_items,style_fat)

        refund_trades_len = len(seller_refund_trades)
        end_row = end_row + refund_trades_len
        ws_xxsj.write_merge(end_row+1,end_row,0,6,TRADE_REFUND_ACCOUNT_MSG%seller_nick,style0)

        total_refund_sum_row = end_row+1

        sum_start = end_row - refund_trades_len+1
        sum_end   = end_row

        write_sum_formula(ws_xxsj,end_row,refund_fee_row,sum_start,sum_end,refund_char,style=style0)

        #unfinish trades
        seller_unfinish_trades = consign_trades.filter(
                seller_id=seller_id).exclude(status__in=ORDER_SUCCESS_STATUS)
        ws_xxsj.write_merge(end_row+3,end_row+3,0,13,TRADE_POST_UNFINISH_MSG,style0)
        for col in xrange(0,col_items):
            ws_xxsj.write(end_row+4,title_col+col,item_names[col],style0)

        if seller_unfinish_trades.count()>0:
            write_trades_to_sheet(ws_xxsj,seller_unfinish_trades,end_row+5,text_col,col_items,style_fat)

        end_row = end_row +len(seller_unfinish_trades)+6
        ws_xxsj.write_merge(end_row,end_row,0,8,SELLER_TOTAL_INCOME_MSG%seller_nick,style0)

        write_seller_formula(ws_xxsj,end_row+1,7,total_trade_sum_row,TOTAL_STATISTIC[0],payment_char,style=style0)
        write_seller_formula(ws_xxsj,end_row+2,7,total_trade_sum_row,TOTAL_STATISTIC[1],post_char,style=style0)
        write_seller_formula(ws_xxsj,end_row+3,7,total_trade_sum_row,TOTAL_STATISTIC[2],point_char,style=style0)
        write_seller_formula(ws_xxsj,end_row+4,7,total_trade_sum_row,TOTAL_STATISTIC[3],commission_char,style=style0)
        write_seller_formula(ws_xxsj,end_row+5,7,total_refund_sum_row,TOTAL_STATISTIC[4],refund_char,style=style0)

        ws_xxsj.write(end_row+6,7,TOTAL_STATISTIC[5],style0)
        sell_formula = '%s%d-%s%d-%s%d/100-%s%d-%s%d'%('I',end_row+2,'I',end_row+3,'I',end_row+4,'I',end_row+5,'I',end_row+6)
        ws_xxsj.write(end_row+6,8,Formula(sell_formula),style0)

    w.save(file_name)


#from django.conf import settings
#
#dt_f = datetime.datetime(2012,4,1,0,0,0)
#dt_t = datetime.datetime(2012,4,30,23,59,59)
#file_name = settings.DOWNLOAD_ROOT +'/2012-04-30.xls'
#
#genMonthTradeStatisticXlsFile(dt_f,dt_t,file_name)