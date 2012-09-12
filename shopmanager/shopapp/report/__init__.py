#-*- coding:utf8 -*-
__author__ = 'meixqhi'


"""
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
"""
