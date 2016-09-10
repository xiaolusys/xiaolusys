# -*- coding:utf-8 -*-
from flashsale.pay.models import Customer, SaleTrade
from django.shortcuts import get_object_or_404
from shopback.items.models import Product
import hashlib
import base64
import urllib
import json
import functools
import requests
from exp_map import exp_map

def get_trade(tid):
    try:
        trade = get_object_or_404(SaleTrade, tid=tid)
    except:
        trade = get_object_or_404(SaleTrade, id=tid)
    return trade


def get_status_message(trade):
    """ 根据交易状态不同返回不同的物流提示信息 """
    res = {u'data': [], u'errcode': u'', u'id': u'', u'message': u'',
           u'name': u'', u'order': u'', u'status': None}
    if trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:  # 如果是已经付款状态
        for t in trade.sale_orders.all():
            pro = get_object_or_404(Product, id=t.item_id)
            if pro.shelf_status == Product.UP_SHELF:  # 上架状态
                res['message'] = "您的订单正在配货"
                return res
        res['message'] = "付款成功"
        return res
    elif trade.status in (SaleTrade.TRADE_CLOSED_BY_SYS,
                          SaleTrade.TRADE_NO_CREATE_PAY,
                          SaleTrade.WAIT_BUYER_PAY,
                          SaleTrade.TRADE_CLOSED):
        res['message'] = trade.get_status_display()
        return res
    return None


def get_owner_queryset(queryset,request):
    customer = get_object_or_404(Customer, user=request.user)
    queryset = queryset.filter(tid__in=(SaleTrade.objects.filter(buyer_id=customer.id).values('tid')))
    return queryset


def packet_data(queryset):
    res = {u'data': [], u'errcode': u'', u'id': u'', u'message': u'', u'name': u'', u'order': u'', u'status': None}
    for query in queryset:
        res['order'] = query.out_sid
        res['name'] = query.logistics_company
        res['status'] = query.get_status_display()
        res['errcode'] = query.errcode
        res["data"].append({"content": query.content, "time": query.time})
    return res
#####################################################################################

#####################################################################################
#第三方物流查询接口
expCode = 'SF'
expNo = '3100707578976'
EBusinessID = 1264368
API_key = "b2983220-a56b-4e28-8ca0-f88225ee2e0b"
exp_info = [expCode,expNo,API_key]

def get_exp_code(LogisticName):
    LogisticCode = exp_map.get("LogisticName",None)
    if LogisticCode:
        return LogisticCode
    else
        return "暂时还不支持%s的查询" % LogisticName

def format_exp_info(expCode,expNo):
    exp_info = "{'OrderCode':'','ShipperCode':'%s','LogisticCode':'%s'}" %(expCode, expNo)
    return exp_info

def format_info(expCode,expNo,API_key):
    exp_info = "{'OrderCode':'','ShipperCode':'%s','LogisticCode':'%s'}" %(expCode, expNo)
    info = '%s%s' % (exp_info, API_key)
    return info

def get_md5_value(src):
    myMd5 = hashlib.md5()
    myMd5.update(src)
    myMd5_Digest = myMd5.hexdigest()
    return myMd5_Digest


def get_base64_value(src):
    return base64.b64encode(src)

def get_urlencode_value(src):
    return urllib.quote(src)

def get_data_signature(*exp_info):
    value = format_info(expCode,expNo,API_key)
    myMd5_Digest = get_md5_value(value)
    base64 = get_base64_value(myMd5_Digest)
    url_str = get_urlencode_value(base64)
    return url_str

info = [EBusinessID,expCode,expNo,API_key]
info = {"EBusinessID":EBusinessID,"API_key":API_key,"expCode":expCode,"expNo":expNo}


def get_post_exp_info(**kwargs):
    exp_info_dict = {"ShipperCode":kwargs['expCode'],"LogisticCode":kwargs["expNo"],"EBusinessID":kwargs["EBusinessID"],"requestType":1002,'DataType':2}
    exp_info = format_exp_info(kwargs['expCode'],kwargs['expNo'])
    requestData = get_urlencode_value(exp_info)
    exp_info_dict.update({"requestData":requestData})
    DataSign = get_data_signature([kwargs['expCode'],kwargs['expNo'],kwargs['API_key']])
    exp_info_dict.update({"DataSign":DataSign})
    return exp_info_dict


def add_requestData(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        expCode = kwargs.get('expCode',None)
        expNo = kwargs.get('expNo', None)
        if expNo and expCode:
            temp = format_exp_info(expCode,expNo)
            requestData = get_urlencode_value(temp)
            kwargs.update({"requestData":requestData})
        return f(*args, **args)
    return wrapper


def add_DataSign(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        encryption_data = [kwargs.get('expCode',None),
                           kwargs.get('expNo',None),
                           kwargs.get('API_key',None)]
        if all(encryption_data):
            DataSign = get_data_signature(*encryption_data)
            kwargs.update({"DataSign":DataSign})
        return f(*args,**kwargs)
    return wrapper


@add_requestData
@add_DataSign
def wuliu_subscription(**kwargs):
    result = requests.post("http://api.kdniao.cc/api/dist",data=kwargs).text
    result = json.loads(result)
    if result["Success"] == True:
        result.update({"info":"订阅成功"})
    else:
        result.update({"info":"订阅失败"})










