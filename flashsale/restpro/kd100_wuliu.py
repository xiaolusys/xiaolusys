# coding=utf-8
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
import logging,time
import re

wuliu_state = {"0":"在途中","1":"已揽件","2":"疑件","3":"已签收","4":"退签","5":"同城派送中","6":"退回","7":"转单"}
logger = logging.getLogger(__name__)

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
    time.sleep(0.5)
    resp.encoding = "utf-8"
    logger.warn({'action': "kd100", 'info': "kd100_instant_query:" + str(number)})
    return resp.text

# def kd100_subscription(company, number,query_url = "http://poll.kuaidi100.com/poll",
#                         key='ZIBQxfAP7615',callbackurl="http://admin.xiaolumm.com/rest/v1/wuliu/push_wuliu_data"):
#     company = str(company)
#     number = str(number)
#
#     param = '''{"company":"%s","number":"%s","key":"%s","from":"","to":"","parameters":
#         {"callbackurl":"%s","salt":"","resultv2":"0","autoCom":"0","interCom":"0","departureCountry":"",
#          "departureCom":"","destinationCountry":"","destinationCom":""}}''' %(company,number,key,callbackurl)
#     data = {"param":param}
#     resp = requests.post(query_url,data=data)
#     logger.warn({'action': "kd100", 'info': "kd100_subscription:" + str(number)})
#     return resp.text




def kd100_callbackurl(**call_back_wuliu_data):
    sub_status = call_back_wuliu_data.get("status")
    sub_message = call_back_wuliu_data.get("message")
    wuliu_trace_data = call_back_wuliu_data.get("lastResult")
    TradeWuliu.create_or_update_tradewuliu(**wuliu_trace_data)

def format_wuliu_data(wuliu_data):
    return_data = {}
    return_data["data"] = []
    wuliu_data = json.loads(wuliu_data)
    return_data["status"] = wuliu_state[wuliu_data["state"]]
    return_data["name"] = wuliu_data["com"]
    return_data["status_code"] = int(wuliu_data["state"])
    return_data["errcode"] = ''
    return_data["order"] = wuliu_data["nu"]
    return_data["message"] = wuliu_data["message"]
    for i in wuliu_data['data']:
        return_data["data"].append({"content" : i["context"],"time":i["time"]})
    return_data["id"] = ""
    return return_data

def fomat_wuliu_data_from_db(tradewuliu):
    format_exp_info = {
        "status": wuliu_state[str(tradewuliu.status)],
        "status_code": int(tradewuliu.status),
        "name": tradewuliu.logistics_company,
        "errcode": tradewuliu.errcode,
        "id": "",
        "message": "",
        "order": tradewuliu.out_sid
    }
    data = []
    try:
        content = json.loads(tradewuliu.content)
    except:
        if tradewuliu.content:
            content = eval(tradewuliu.content)
    for i in content:
        temp = {}
        # temp.update({'time':i['time'].encode('utf-8')})
        temp.update({'time': i.get('time',i.get("AcceptTime")).encode('utf-8')})
        # temp.update({'content':i['context'].encode('utf-8')})
        temp.update({'content': i.get('context',i.get("AcceptStation")).encode('utf-8')})
        data.append(temp)
        format_exp_info.update({"data":data})

    return format_exp_info

def confirm_get_by_state(out_sid,status):
    out_sid = str(out_sid)
    status = int(status)
    if not out_sid or not status or status != 3:
        return
    psi = PackageSkuItem.objects.filter(out_sid=out_sid, status='finish').first()
    if psi:
        logger.warn({'action': "kdn", 'info': "confirm_psi_finish_kd100:" + str(out_sid)})
        psi.set_status_finish()

    packageskuitem = PackageSkuItem.objects.filter(out_sid=out_sid).values("oid")
    if packageskuitem:
        packageskuitem = [i['oid'] for i in packageskuitem]
        so = SaleOrder.objects.filter(oid__in=packageskuitem, status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
        if so:
            for i in so:
                logger.warn({'action': "kdn", 'info': "confirm_sign_order_kd100:" + str(out_sid)})
                i.confirm_sign_order()






