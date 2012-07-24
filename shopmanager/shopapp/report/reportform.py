from pyExcelerator import Workbook,XFStyle,Font,Formula
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_REFUND_STATUS
from shopback.amounts.models import TradeAmount,OrderAmount
from shopback.refunds.models import Refund ,REFUND_WILL_STATUS
from shopback.logistics.models import Logistics
from shopback.fenxiao.models import PurchaseOrder
from shopback.users.models import User
from auth import apis


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

TITLE_FIELDS = {
    "TRADE_FINISH_MSG":u'\u53d1\u8d27\u5df2\u6210\u529f\u7684\u4ea4\u6613',
    "TRADE_POST_UNFINISH_MSG":u'\u53d1\u8d27\u4f46\u672a\u5b8c\u6210\u7684\u4ea4\u6613',
    "TRADE_FENXIAO_MSG":u'\u6765\u81ea\u6dd8\u5b9d\u5206\u9500\u7684\u8ba2\u5355',
    "SELLER_TRADE_ACCOUNT_MSG":u'%s\u5408\u8ba1\uff1a',
    "TRADE_REFUND_MSG":u'\u90e8\u5206\u9000\u6b3e\u4ea4\u6613(\u5305\u542b\u5546\u57ce\u4e0e\u5206\u9500)',
    "TRADE_REFUND_ACCOUNT_MSG":u'%s\u9000\u6b3e\u91d1\u989d\u5408\u8ba1',
    "SELLER_TOTAL_INCOME_MSG":u'%s\u4e70\u5bb6\u5b9e\u4ed8\u6b3e-\u90ae\u8d39-\u79ef\u5206/100-\u4f63\u91d1-\u90e8\u5206\u9000\u6b3e\u91d1\u989d',
    "TOTAL_SALE_MSG":u'\u603b\u9500\u552e\u989d',
    "TOTAL_POST_FEE_MSG":u'\u90ae\u8d39',
    "TOTAL_POINT_FEE_MSG":u'\u79ef\u5206',
    "TOTAL_COMMISSION_FEE_MSG":u'\u4f63\u91d1',
    "TOTAL_REFUND_FEE_MSG":u'\u9000\u6b3e',
    "MONTH_FINAL_AMOUNT":u'\u5230\u5e10\u91d1\u989d',
    "UNFOUND_MSG":u'\u672a\u627e\u5230\uff01',
}


data_format = [
    ('trade.buyer_nick','@'),             #C
    ('str(trade.id)','@'),                #D
    ('trade.consign_time','M/D'),         #E
    ('logistics.out_sid','general'),      #F
    ('logistics.company_name','@'),       #G
    ('float(trade_amount.post_fee)','0.00'),     #H
    ('float(trade_amount.payment)','0.00'),           #I
    ('int(trade_amount.buyer_obtain_point_fee)','0'), #J
    ('float(trade_amount.commission_fee)','0.00'),    #K
    ('trade.status','@'),                      #L
]


purchase_format = [
    ('trade.distributor_username','@'),           #C
    ('str(trade.id)','@'),                        #D
    ('trade.consign_time','M/D'),                 #E
    ('trade.logistics_id','general'),             #F
    ('trade.logistics_company_name','@'),         #G
    ('float(trade_amount.post_fee)','0.00'),             #H
    ('float(trade_amount.payment)','0.00'),  #I
    ('int(0)','0'),                               #J
    ('int(0)','0.00'),                            #K
    ('trade.status','@'),                         #L
]

refund_format = [
    ('refund.buyer_nick','@'),          #C
    ('str(refund.refund_id)','@'),      #D
    ('str(refund.tid)','@'),            #E
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

class TradesToXLSFile(object):

    def __init__(self,
                 title_row=0,
                 title_col=0,
                 text_row=1,
                 text_col=2,
                 col_items=11,
                 payment_char='I',
                 post_char='H',
                 point_char='J',
                 commission_char='K',
                 earning_char='M',
                 refund_char='L',
                 wb = Workbook(),
                 title_style = XFStyle(),
                 content_style = XFStyle(),):

        self.title_col = title_col
        self.title_row = title_row
        self.text_col  = text_col
        self.text_row  = text_row
        self.col_items = col_items
        self.payment_char = payment_char
        self.post_char    = post_char
        self.point_char   = point_char
        self.commission_char = commission_char
        self.earning_char = earning_char
        self.refund_char  = refund_char
        self.wb = wb
        self.title_style   = title_style
        self.content_style = content_style
        self.cur_row = 0

    def gen_report_file(self,dt_from,dt_to,file_name):

        consign_trades = Trade.objects.filter(consign_time__gte=dt_from,consign_time__lte=dt_to)
        seller_ids_list = consign_trades.values('seller_id').distinct('seller_id')
        for seller_id_dict in seller_ids_list:

            self.cur_row = 0
            seller_id = seller_id_dict['seller_id']
            seller_nick = consign_trades.filter(seller_id=seller_id)[0].seller_nick
            sheet = self.wb.add_sheet(seller_nick)

            seller_finish_trades = consign_trades.filter(
                user__visitor_id=seller_id,status__in=ORDER_SUCCESS_STATUS)

            self.write_trades_to_sheet(sheet,seller_id,seller_finish_trades,TITLE_FIELDS['TRADE_FINISH_MSG'])

            seller_purchase_trades = PurchaseOrder.objects.filter(
                user__visitor_id=seller_id,consign_time__gte=dt_from
                ,consign_time__lte=dt_to,status__in = ORDER_SUCCESS_STATUS)

            self.write_purchase_to_sheet(sheet,seller_id,seller_purchase_trades)

            self.cur_row += 1
            self.write_trade_account(sheet,3,self.cur_row,seller_nick)

            trade_sum_row = self.cur_row+1

            seller_refund_trades   = Refund.objects.filter(
                    user__visitor_id=seller_id,status__in=REFUND_WILL_STATUS)

            self.write_refund_to_sheet(sheet,seller_refund_trades,seller_nick,dt_from,dt_to)

            refund_sum_row = self.cur_row+1

            seller_unfinish_trades = consign_trades.filter(
                user__visitor_id=seller_id,status=ORDER_REFUND_STATUS)
            
            self.cur_row += 1
            self.write_trades_to_sheet(sheet,seller_id,seller_unfinish_trades,TITLE_FIELDS['TRADE_POST_UNFINISH_MSG'])

            self.write_final_account(sheet,trade_sum_row,refund_sum_row,seller_nick)

        self.wb.save(file_name)



    def write_trades_to_sheet(self,sheet,seller_id,trades,trade_finish_title):

        sheet.write_merge(self.cur_row,self.title_row,0,self.text_col,trade_finish_title,self.title_style)
        if trades.count()>0:
            self.cur_row += 1
            for col in xrange(0,self.col_items):
                sheet.write(self.cur_row,self.text_col+col,item_names[col],self.title_style)

            for trade in trades:
                self.cur_row += 1

                logistics = self.get_logistics(seller_id,trade.id)
                trade_amount = self.get_trade_amount(seller_id,trade.id)
                for data_num,data_tuple in enumerate(data_format):
                    try:
                        self.content_style.num_format_str = data_tuple[1]
                        sheet.write(self.cur_row,self.text_col+int(data_num),eval(data_tuple[0]),self.content_style)
                    except Exception,exc:
                        pass

                earning_formula = '%s%d-%s%d-%s%d/100-%s%d'%(self.payment_char,self.cur_row+1,self.post_char,self.cur_row+1,
                                self.point_char,self.cur_row+1,self.commission_char,self.cur_row+1)
                sheet.write(self.cur_row,self.text_col+self.col_items-1,Formula(earning_formula),self.content_style)




    def get_logistics(self,seller_id,trade_id):

        logistics = Logistics.get_or_create(seller_id,trade_id)
        logistics.out_sid = logistics.out_sid if logistics.out_sid else TITLE_FIELDS['UNFOUND_MSG']
        logistics.company_name = logistics.company_name if logistics.company_name else TITLE_FIELDS['UNFOUND_MSG']
        return logistics
    
    
    def get_trade_amount(self,seller_id,trade_id):

        trade_amount = TradeAmount.get_or_create(seller_id,trade_id)
        trade_amount.post_fee = trade_amount.post_fee if trade_amount.post_fee else '0.00'
        trade_amount.payment  = trade_amount.payment  if trade_amount.payment else '0.00'
        trade_amount.commission_fee  = trade_amount.commission_fee  if trade_amount.commission_fee else '0.00'
        trade_amount.buyer_obtain_point_fee  = trade_amount.buyer_obtain_point_fee\
            if trade_amount.buyer_obtain_point_fee else '0.00'
        return trade_amount


    def write_purchase_to_sheet(self,sheet,seller_id,trades):

        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.title_row,0,2,
                          TITLE_FIELDS['TRADE_FENXIAO_MSG'],self.title_style)
        trades_len =  len(trades)
        if trades_len>0:
            for trade in trades:
                self.cur_row += 1
                trade_amount = self.get_trade_amount(seller_id,trade.id)
                for data_num,data_tuple in enumerate(purchase_format):
                    try:
                        self.content_style.num_format_str = data_tuple[1]
                        sheet.write(self.cur_row,self.text_col+int(data_num),eval(data_tuple[0]),self.content_style)
                    except Exception,exc:
                        pass

                earning_formula = '%s%d-%s%d-%s%d/100-%s%d'%(self.payment_char,self.cur_row+1,self.post_char,self.cur_row+1,
                                self.point_char,self.cur_row+1,self.commission_char,self.cur_row+1)
                sheet.write(self.cur_row,self.text_col+self.col_items-1,Formula(earning_formula),self.content_style)



    def write_trade_account(self,sheet,sum_start,sum_end,seller_nick):

        sheet.write_merge(self.cur_row,self.title_row,0,2,
                         TITLE_FIELDS['SELLER_TRADE_ACCOUNT_MSG']%seller_nick,self.title_style)

        self.write_sum_formula(sheet,self.cur_row,7 ,sum_start,sum_end,self.post_char)
        self.write_sum_formula(sheet,self.cur_row,8 ,sum_start,sum_end,self.payment_char)
        self.write_sum_formula(sheet,self.cur_row,9 ,sum_start,sum_end,self.point_char)
        self.write_sum_formula(sheet,self.cur_row,10,sum_start,sum_end,self.commission_char)
        self.write_sum_formula(sheet,self.cur_row,12,sum_start,sum_end,self.earning_char)



    def write_refund_to_sheet(self,sheet,refunds,seller_nick,dt_from,dt_to):

        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.cur_row,0,2,TITLE_FIELDS['TRADE_REFUND_MSG'],self.title_style)
        self.cur_row += 1
        for col in xrange(0,len(refund_item_names)):
            sheet.write(self.cur_row,self.text_col+col,refund_item_names[col],self.title_style)

        sum_start = self.cur_row
        for refund in refunds:
            trade = self.get_trade_or_purchase_trade(refund.tid)
            if trade and trade.consign_time and trade.consign_time >=dt_from and trade.consign_time<=dt_to\
                and trade.status in ORDER_SUCCESS_STATUS:
                self.cur_row += 1
                for data_num,data_tuple in enumerate(refund_format):
                    try:
                        self.content_style.num_format_str = data_tuple[1]
                        sheet.write(self.cur_row,self.text_col+int(data_num),eval(data_tuple[0]),self.content_style)
                    except Exception,exc:
                        pass

        sum_end = self.cur_row
        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.cur_row,0,2,TITLE_FIELDS['TRADE_REFUND_ACCOUNT_MSG']%seller_nick,self.title_style)

        self.write_sum_formula(sheet,self.cur_row,11,sum_start,sum_end,self.refund_char)


    def get_trade_or_purchase_trade(self,trade_id):
        try:
            trade = Trade.objects.get(id=trade_id)
        except Trade.DoesNotExist:
            try:
                trade = PurchaseOrder.objects.get(id=trade_id)
            except PurchaseOrder.DoesNotExist:
                trade = None
        return trade


    def write_sum_formula(self,sheet,row,col,sum_start_row,sum_end_row,row_char):
        sum_formula = 'SUM(%s%d:%s%d)'%(row_char,sum_start_row,row_char,sum_end_row)
        sheet.write(row,col,Formula(sum_formula))



    def write_seller_formula(self,sheet,row,col,sum_row,sum_name,sum_char):
        sheet.write(row,col,sum_name,self.content_style)
        sell_formula = '%s%d'%(sum_char,sum_row)
        sheet.write(row,col+1,Formula(sell_formula))



    def write_final_account(self,sheet,trade_sum_row,refund_sum_row,seller_nick,formula_col=7,formula_char='I'):

        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.cur_row,0,3,TITLE_FIELDS['SELLER_TOTAL_INCOME_MSG']%seller_nick,self.title_style)

        self.cur_row += 1
        self.write_seller_formula(sheet,self.cur_row,formula_col,trade_sum_row,TITLE_FIELDS["TOTAL_SALE_MSG"],self.payment_char)
        self.cur_row += 1
        self.write_seller_formula(sheet,self.cur_row,formula_col,trade_sum_row,TITLE_FIELDS["TOTAL_POST_FEE_MSG"],self.post_char)
        self.cur_row += 1
        self.write_seller_formula(sheet,self.cur_row,formula_col,trade_sum_row,TITLE_FIELDS["TOTAL_POINT_FEE_MSG"],self.point_char)
        self.cur_row += 1
        self.write_seller_formula(sheet,self.cur_row,formula_col,trade_sum_row,TITLE_FIELDS["TOTAL_COMMISSION_FEE_MSG"],self.commission_char)
        self.cur_row += 1
        self.write_seller_formula(sheet,self.cur_row,formula_col,refund_sum_row,TITLE_FIELDS["TOTAL_REFUND_FEE_MSG"],self.refund_char)

        self.cur_row += 1
        sheet.write(self.cur_row,formula_col,TITLE_FIELDS["MONTH_FINAL_AMOUNT"],self.title_style)
        sell_formula = '%s%d-%s%d-%s%d/100-%s%d-%s%d'%(formula_char,self.cur_row-4,formula_char,self.cur_row-3,formula_char
                                                       ,self.cur_row-2,formula_char,self.cur_row-1,formula_char,self.cur_row-0)
        sheet.write(self.cur_row,formula_col+1,Formula(sell_formula))



