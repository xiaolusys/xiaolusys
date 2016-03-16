# coding:utf-8
""" 
订单支付方式列表
key: 表示支付类型；
type:0,表示折扣优惠;1,表示虚拟支付,如余额;2,表示实际支付；
"""
PAY_EXTRAS = {
    '1':{'pid':1,'type':0,'value':2,'name':'APP支付减2元'},
} 