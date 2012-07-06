#-*- coding:utf8 -*-
from pyExcelerator import Workbook,XFStyle,Font,Formula
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS
from shopback.amounts.models import TradeAmount,OrderAmount
from shopback.refunds.models import Refund ,REFUND_WILL_STATUS
from shopback.logistics.models import Logistics
from shopback.fenxiao.models import PurchaseOrder
from shopback.users.models import User


item_names = [
    '会员名称',        #buyer_nick
    '来源单号(分销ID)', #trade_id
    '发货日期',        #consign_time
    '物流运单号',       #logistics_id
    '物流公司',        #logisticscompany
    '物流费用',        #post_fee
    '付款金额',        #payment
    '积分',           #point
    '佣金',           #commission_fee
    '交易状态',        #trade_status
    '到帐金额',        #earnings
]

refund_item_names =[
    '会员名称',       #buyer_nick
    '退款单ID',       #refund_id
    '交易ID',         #tid
    '订单ID',        #oid
    '退货运单号',     #sid
    '物流公司',       #company_name
    '退货时间',       #created
    '总金额',        #total_fee
    '实付金额',      #payment
    '退款金额',      #refund_fee
    '退货原因',      #reason
    '商品退回',     #has_good_return
    '商品状态',     #good_status
    '订单状态',     #order_status
    '退货状态',     #status
]

TITLE_FIELDS = {
    "TRADE_FINISH_MSG":'发货已成功的交易',
    "TRADE_POST_UNFINISH_MSG":'发货但未完成的交易',
    "TRADE_FENXIAO_MSG":'来自淘宝分销的订单',
    "SELLER_TRADE_ACCOUNT_MSG":'%s合计：',
    "TRADE_REFUND_MSG":'部分退款交易(包含商城与分销)',
    "TRADE_REFUND_ACCOUNT_MSG":'%s退款金额合计',
    "SELLER_TOTAL_INCOME_MSG":'%s买家实付款-邮费-积分/100-佣金-部分退款金额',
    "TOTAL_SALE_MSG":'总销售额',
    "TOTAL_POST_FEE_MSG":'邮费',
    "TOTAL_POINT_FEE_MSG":'积分',
    "TOTAL_COMMISSION_FEE_MSG":'佣金',
    "TOTAL_REFUND_FEE_MSG":'退款',
    "MONTH_FINAL_AMOUNT":'到帐金额',
}


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
                seller_id=seller_id,status__in=ORDER_SUCCESS_STATUS)

            self.write_trades_to_sheet(sheet,seller_finish_trades,TITLE_FIELDS['TRADE_FINISH_MSG'])

            seller_purchase_trades = PurchaseOrder.objects.filter(
                seller_id=seller_id,consign_time__gte=dt_from
                ,consign_time__lte=dt_to,status__in = ORDER_SUCCESS_STATUS)

            self.write_purchase_to_sheet(sheet,seller_purchase_trades)

            self.cur_row += 1
            self.write_trade_account(sheet,3,self.cur_row,seller_nick)

            trade_sum_row = self.cur_row+1

            seller_refund_trades   = Refund.objects.filter(
                    seller_id=seller_id,trade__consign_time__gte=dt_from,
                    trade__consign_time__lt=dt_to,status__in=REFUND_WILL_STATUS,
                    trade__status__in = ORDER_SUCCESS_STATUS)

            self.write_refund_to_sheet(sheet,seller_refund_trades,seller_nick)

            refund_sum_row = self.cur_row+1

            seller_unfinish_trades = consign_trades.filter(
                seller_id=seller_id).exclude(status__in=ORDER_SUCCESS_STATUS)

            self.cur_row += 1
            self.write_trades_to_sheet(sheet,seller_unfinish_trades,TITLE_FIELDS['TRADE_POST_UNFINISH_MSG'])

            self.write_final_account(sheet,trade_sum_row,refund_sum_row,seller_nick)

        self.wb.save(file_name)



    def write_trades_to_sheet(self,sheet,trades,trade_finish_title):

        sheet.write_merge(self.cur_row,self.title_row,0,self.text_col,trade_finish_title,self.title_style)
        if trades.count()>0:
            self.cur_row += 1
            for col in xrange(0,self.col_items):
                sheet.write(self.text_row,self.text_col+col,item_names[col],self.title_style)

            for trade in trades:
                self.cur_row += 1

                logistics = self.get_logistics(trade.id)
                
                for data_num,data_tuple in enumerate(data_format):
                    try:
                        self.content_style.num_format_str = data_tuple[1]
                        sheet.write(self.cur_row,self.text_col+int(data_num),eval(data_tuple[0]),self.content_style)
                    except Exception,exc:
                        pass

                earning_formula = '%s%d-%s%d-%s%d/100-%s%d'%(self.payment_char,self.cur_row+1,self.post_char,self.cur_row+1,
                                self.point_char,self.cur_row+1,self.commission_char,self.cur_row+1)
                sheet.write(self.cur_row,self.text_col+self.col_items-1,Formula(earning_formula),self.content_style)




    def get_logistics(self,trade_id):

        try:
            logistics = Logistics.objects.get(tid=trade_id)
        except Exception,exc:
            logistics = Logistics()
            logistics.out_sid = u'\u672a\u627e\u5230\uff01'
            logistics.company_name = u'\u672a\u627e\u5230\uff01'

        return logistics



    def write_purchase_to_sheet(self,sheet,trades):

        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.title_row,0,2,
                          TITLE_FIELDS['TRADE_FENXIAO_MSG'],self.title_style)
        trades_len =  len(trades)
        if trades_len>0:
            for trade in trades:
                self.cur_row += 1
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



    def write_refund_to_sheet(self,sheet,refunds,seller_nick):

        self.cur_row += 1
        sheet.write_merge(self.cur_row,self.cur_row,0,2,TITLE_FIELDS['TRADE_REFUND_MSG'],self.title_style)
        self.cur_row += 1
        for col in xrange(0,len(refund_item_names)):
            sheet.write(self.cur_row,self.text_col+col,refund_item_names[col],self.title_style)

        sum_start = self.cur_row
        for refund in refunds:
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



