from django.conf import settings
from flashsale.pay.models import Customer, SaleTrade
from shopback.trades.models import TradeWuliu
from django.shortcuts import get_object_or_404
from shopback.items.models import Product
import hashlib
import base64
import urllib
import json
import functools
import requests
import datetime,socket,random,struct
from exp_map import exp_map,reverse_map,reverse_100_map
from shopback.logistics.models import LogisticsCompany
from flashsale.pay.models import SaleTrade,SaleOrder
from shopback.trades.models import PackageSkuItem
import logging
import re



def get_md5_value(src):
    myMd5 = hashlib.md5()
    myMd5.update(src)
    myMd5_Digest = myMd5.hexdigest()
    return myMd5_Digest



def kd100_instant_query(company, number,query_url = "http://poll.kuaidi100.com/poll/query.do",
                        key='ZIBQxfAP7615',customer="8C36E8E2B13783B6F08187AA24D86DBD"):
    company = str(company)
    number = str(number)
    param = '{"com":"%s","num":"%s","from":"","to":""}' %(company,number)
    sign = param + key + customer
    sign = get_md5_value(sign).upper()
    query_param_info = {"param":param,"sign":sign,"customer":customer}
    resp = requests.post(query_url,data=query_param_info)
    print resp.text
    return json.loads(resp.text)

def kd100_subscription(company, number,query_url = "http://poll.kuaidi100.com/poll",
                        key='ZIBQxfAP7615',callbackurl="http://admin.xiaolumm.com"):
    company = str(company)
    number = str(number)

    param = '''{"company":"%s","number":"%s","key":"%s","from":"","to":"","parameters":
        {"callbackurl":"%s","salt":"","resultv2":"0","autoCom":"0","interCom":"0","departureCountry":"",
         "departureCom":"","destinationCountry":"","destinationCom":""}}''' %(company,number,key,callbackurl)
    resp = requests.post(query_url,data=param)
    return resp.text

def create_or_update_tradewuliu(**wuliu_trace_data):
    out_sid = wuliu_trace_data.get("nu")
    logistics_company = wuliu_trace_data.get("com")
    status = wuliu_trace_data.get("status")
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = json.dumps(wuliu_trace_data.get("data","没有物流数据"))

    write_data = {
        "out_sid": out_sid,
        "logistics_company": logistics_company,
        "status": status,
        "time": time,
        "content": content
    }
    tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid)

    if tradewuliu.first() is None:
        TradeWuliu.objects.create(**write_data)
    else:
        tradewuliu.update(**write_data)

def kd100_callbackurl(**call_back_wuliu_data):
    sub_status = call_back_wuliu_data.get("status")
    sub_message = call_back_wuliu_data.get("message")
    wuliu_trace_data = call_back_wuliu_data.get("lastResult")
    create_or_update_tradewuliu(**wuliu_trace_data)


