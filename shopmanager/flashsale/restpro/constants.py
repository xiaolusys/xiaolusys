# coding:utf-8
""" 
订单支付方式列表
key: 表示支付类型；
type:0,表示折扣优惠;1,表示虚拟支付,如余额;2,表示实际支付；
"""
ETS_APPCUT = '1'
ETS_COUPON = '2'
ETS_BUDGET = '3'

DISCOUNT = 0
BUDGET   = 1
REALPAY  = 2

PAY_EXTRAS = {
    ETS_APPCUT:{'pid':1,'type':DISCOUNT,'value':2,'name':'APP支付减2元'},
    ETS_COUPON:{'pid':2,'type':DISCOUNT,'value':1,'name':'优惠券'}, #1,能使用优惠券,0,不能使用
    ETS_BUDGET:{'pid':3,'type':BUDGET,'value':0,'name':'余额支付'},
} 


SHARE_LINK = ""
PYQ_TITLES = [
    '告诉你，今年元宵其实要这样过。。。#脸红心跳',
    '哈哈，老公好不好，抢了睡袋就知道！',
    '哈哈，只有1%的人知道，原来这两个我都想要～'
]