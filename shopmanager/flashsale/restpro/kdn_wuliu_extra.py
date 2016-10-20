# -*- coding:utf-8 -*-

# import os
# import sys
# sys.path.append("/home/fpcnm/myProjects/xiaoluMM4/xiaolusys/shopmanager/")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")


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
import datetime
from exp_map import exp_map,reverse_map
from shopback.logistics.models import LogisticsCompany
from flashsale.pay.models import SaleTrade,SaleOrder
from shopback.trades.models import PackageSkuItem
import logging

logger = logging.getLogger(__name__)
import simplejson

#老版本物流查询接口的方法
#######################################################################
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



#第三方物流快递鸟查询接口方法  write_by huazi
#####################################################################################
expCode = 'SF'
expNo = '3100707578976'
EBusinessID = 1264368
API_key = "b2983220-a56b-4e28-8ca0-f88225ee2e0b"
exp_info = [expCode,expNo,API_key]
business_info = {"EBusinessID":str(EBusinessID),"API_key":API_key,"DataType":"2","requestType":"1002"}
business_info_sub = {"EBusinessID":str(EBusinessID),"API_key":API_key,"DataType":"2","requestType":"1008"}
class KdnBaseAPI(object):

    EBusinessID = 1264368
    API_key = "b2983220-a56b-4e28-8ca0-f88225ee2e0b"

    def __init__(self):
        pass

    #获取物流公司的expCode
    def __get_exp_code(self,LogisticName):
        LogisticCode = exp_map.get("LogisticName",None)
        if LogisticCode:
            return LogisticCode
        else:
            return "暂时还不支持%s的查询" % LogisticName

    #获得value的MD5加密
    def __get_md5_value(self,src):
        myMd5 = hashlib.md5()
        myMd5.update(src)
        myMd5_Digest = myMd5.hexdigest()
        return myMd5_Digest

    #把value进行base64编码
    def __get_base64_value(self,src):
        return base64.b64encode(src)

    #获得value的url编码
    @staticmethod
    def get_urlencode_value(src):
        return urllib.quote(src)

    #格式化expCode和expNo
    @staticmethod
    def format_exp_info(expCode,expNo):
        exp_info = "{'OrderCode':'','ShipperCode':'%s','LogisticCode':'%s'}" %(expCode, expNo)
        return exp_info

    #加入API_key并格式化
    @staticmethod
    def format_info(expCode,expNo,API_key):
        exp_info = "{'OrderCode':'','ShipperCode':'%s','LogisticCode':'%s'}" %(expCode, expNo)
        info = '%s%s' % (exp_info, API_key)
        return info

    #数字签名
    @staticmethod
    def get_data_signature(*exp_info):
        exp_info = list(exp_info)
        value = KdnBaseAPI.format_info(*exp_info)
        myMd5_Digest = KdnBaseAPI().__get_md5_value(value)
        base64 = KdnBaseAPI().__get_base64_value(myMd5_Digest)
        url_str = KdnBaseAPI.get_urlencode_value(base64)
        return url_str

    def __repr__(self):
        return self.EBusinessID,self.API_key


def add_business_info(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        kwargs.update(business_info)
        return f(*args,**kwargs)
    return wrapper

def add_business_info_sub(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        kwargs.update(business_info_sub)
        return f(*args,**kwargs)
    return wrapper

def get_exp_code(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        expName = kwargs.get('expName',None)
        assert expName is not None,'物流公司名字为空'
        exp_code = exp_map.get(expName,None)
        if exp_code:
            kwargs['expCode'] = exp_code
            return f(*args,**kwargs)
        else:
            for k,v in exp_map.iteritems():
                if k.startswith(expName.encode('gb2312').decode('gb2312')[0:2].encode('utf-8')):
                    exp_code = exp_map[k]
                    kwargs['expCode'] = exp_code
                    return f(*args,**kwargs)
            return {"info":"尚未提供此物流公司快递查询"}
    return wrapper


def add_requestData(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        expCode = kwargs.get('expCode',None)
        expNo = kwargs.get('expNo', None)
        if expNo and expCode:
            temp = KdnBaseAPI.format_exp_info(expCode,expNo)
            requestData = KdnBaseAPI.get_urlencode_value(temp)
            kwargs.update({"requestData":requestData})
        return f(*args, **kwargs)
    return wrapper


def add_DataSign(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        encryption_data = [kwargs.get('expCode',None),
                           kwargs.get('expNo',None),
                           kwargs.get('API_key',None)]
        if all(encryption_data):
            DataSign = KdnBaseAPI.get_data_signature(*encryption_data)
            kwargs.update({"DataSign":DataSign})
        return f(*args,**kwargs)
    return wrapper

def comfirm_get(out_sid,status):
    logger.warn({'action': "kdn", 'info': "start comfirm_get"})
    packageskuitem = PackageSkuItem.objects.filter(out_sid = out_sid).values("oid")
    if packageskuitem and status == 3:
        packageskuitem = [i['oid'] for i in packageskuitem]
        so = SaleOrder.objects.filter(oid__in = packageskuitem,status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS).first()
        if so:
            so.status = SaleOrder.TRADE_BUYER_SIGNED
            so.save()

def write_traces(kwargs):
    logger.warn({'action': "kdn", 'info': "start change status"})
    kwargs = json.loads(kwargs)
    write_info = {
        "out_sid": kwargs['LogisticCode'],
        "logistics_company": reverse_map().get(kwargs['ShipperCode'],None),
        "status": kwargs['State'],
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": json.dumps(kwargs['Traces'])
    }
    tradewuliu = TradeWuliu.objects.filter(logistics_company=write_info['logistics_company'],
                                           out_sid=write_info['out_sid'])
    logger.warn("准备写入数据库了")
    if tradewuliu.first() is None:
        TradeWuliu.objects.create(**write_info)
        comfirm_get(write_info["out_sid"],write_info["status"])
        psi = PackageSkuItem.objects.filter(out_sid=write_info["out_sid"]).first()
        if psi:
            psi.cancel_failed_time()
    elif write_info["content"] != tradewuliu.first().content:
        tradewuliu.update(**write_info)
        comfirm_get(write_info["out_sid"], write_info["status"])
    comfirm_get(write_info["out_sid"], write_info["status"])
    
def format_content(**kwargs):
    content = kwargs["content"]
    content = json.loads(content)
    all_data = {"status":kwargs["status"],
                "name":kwargs["name"],
                "errcode":kwargs["errcode"],
                "status_code":kwargs["status_code"],
                "id":"",
                "order": kwargs["out_sid"],
                "message":kwargs["message"]}
    data = []
    for i in content:
        temp = {}
        temp.update({'time':i['AcceptTime'].encode('utf-8')})
        temp.update({'content':i['AcceptStation'].encode('utf-8')})
        data.append(temp)
    data.reverse()
    all_data.update({"data":data})
    return all_data

@add_business_info                                #扩充参数,参数字典加入商户id和key等信息
@get_exp_code                                     #通过中文的物流公司获取相应的物流Code
@add_requestData                                  #把expCode和expNo进行url编码
@add_DataSign                                     #把请求数据加入API_key进行数字签名
def kdn_subscription(*args,**kwargs):
    logger.warn({'action': "kdn", 'info': "run kdn_subscription"})
    res = requests.post("http://api.kdniao.cc/api/dist",data=kwargs)
    result = res.text
    if res.status_code == 502:
        logging.warn("物流查询失败返回"+"502 Bad Gateway"+"快递鸟那边繁忙")
        return result
    result = json.loads(result.encode('UTF-8'))
    if result["Success"] == True:
        logging.warn("订阅成功")
        result.update({"info":"订阅成功"})
        print result
        if result['Traces']:
            logger.warn({'action':"kdn",'info':"start sub"})
            write_traces(json.dumps(result))
    else:
        print result
        result.update({"info":"订阅失败"})
        if PackageSkuItem.objects.filter(out_sid = kwargs['expNo']).first():
            PackageSkuItem.objects.filter(out_sid = kwargs['expNo']).first().set_failed_time()
        logger.warn("订阅失败")
        logging.warn(result['Reason'])
    return result

@add_business_info_sub                               #扩充参数,参数字典加入商户id和key等信息
@get_exp_code                                     #通过中文的物流公司获取相应的物流Code
@add_requestData                                  #把expCode和expNo进行url编码
@add_DataSign                                     #把请求数据加入API_key进行数字签名
def kdn_subscription_sub(*args,**kwargs):
    logging.warn(kwargs)
    logger.warn({'action': "kdn", 'info': "run kdn_subscription_sub"})
    res = requests.post("http://api.kdniao.cc/api/dist",data=kwargs)
    result = res.text
    if res.status_code == 502:
        logging.warn("物流查询失败返回"+"502 Bad Gateway"+"快递鸟那边繁忙")
        return result
    result = json.loads(result.encode('UTF-8'))
    if result["Success"] == True:
        logging.warn("订阅成功")
        result.update({"info":"订阅成功"})
        print result
    else:
        print result
        result.update({"info":"订阅失败"})
        if PackageSkuItem.objects.filter(out_sid = kwargs['expNo']).first():
            PackageSkuItem.objects.filter(out_sid = kwargs['expNo']).first().set_failed_time()
        logger.warn("订阅失败")
        logger.warn(result['Reason'])
    return result

def get_reverse_code(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        expName = reverse_map().get(kwargs['ShipperCode'],None)
        if expName:
            writing_info = {"out_sid": kwargs['LogisticCode'],
                            "logistics_company": expName,
                            "status": kwargs['State'],
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "content": kwargs['Traces']
                            }
            return f(*args,**writing_info)
        else:
            raise Exception("无法解析物流公司名%s,物流公司%s不存在" % (kwargs['ShipperCode'],kwargs['ShipperCode']))
    return wrapper

def get_logistics_name(company_code):
    try:
        company_code = int(company_code)
        lc = LogisticsCompany.objects.filter(id=int(company_code)).first()
        if lc is None:
            return lc
        else:
            return lc.name
    except:
        lc = LogisticsCompany.objects.filter(code=company_code).first()
        if lc is None:
            return lc
        else:
            return lc.name
        # assert lc is not None,"提供的物流公司编码有问题 么么哒~~ 物流公司名不存在"


def kdn_get_push(*args, **kwargs):
    logger.warn("开始接受推送物流信息了")
    tradewuliu = TradeWuliu.objects.filter(logistics_company=kwargs['logistics_company'],
                                           out_sid=kwargs['out_sid'])
    if tradewuliu.first() is None:
        TradeWuliu.objects.create(**kwargs)
        print "写入成功"
    else:
        tradewuliu.update(**kwargs)
        print "更新成功"




if __name__ == '__main__':
    test_info = {"expName" : '韵达快递',"expNo":"3101138251229"}
    kdn_subscription_sub(**test_info)
    # format_content()
    # comfirm_get(229785605639,4)






