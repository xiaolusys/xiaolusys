# -*- coding:utf-8 -*-

# import os
# import sys,django
# sys.path.append("/home/fpcnm/myProjects/xiaoluMM4/xiaolusys/shopmanager/")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
# django.setup()

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
from exp_map import exp_map,reverse_map
from shopback.logistics.models import LogisticsCompany
from flashsale.pay.models import SaleTrade,SaleOrder
from shopback.trades.models import PackageSkuItem
import logging
import re

logger = logging.getLogger(__name__)
import simplejson


ua =  ["Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
"Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
"Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
"Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
"Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
"Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
"Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
"Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
"MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
"Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
"Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
"Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1&#43; (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1&#43",
"Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
"Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)"]

RANDOM_IP_POOL=['192.168.10.222/0']

def get_random_ip():                                                     #生成随机ip
  str_ip = RANDOM_IP_POOL[random.randint(0,len(RANDOM_IP_POOL) - 1)]
  str_ip_addr = str_ip.split('/')[0]
  str_ip_mask = str_ip.split('/')[1]
  ip_addr = struct.unpack('>I',socket.inet_aton(str_ip_addr))[0]
  mask = 0x0
  for i in range(31, 31 - int(str_ip_mask), -1):
    mask = mask | ( 1 << i)
  ip_addr_min = ip_addr & (mask & 0xffffffff)
  ip_addr_max = ip_addr | (~mask & 0xffffffff)
  return socket.inet_ntoa(struct.pack('>I', random.randint(ip_addr_min, ip_addr_max)))

def get_random_ua(ua):
    num = random.randint(0, len(ua))
    return ua[num]

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
EBusinessID = settings.KDN_EBUSINESSID #1264368
API_key = settings.KDN_APIKEY #"b2983220-a56b-4e28-8ca0-f88225ee2e0b"
exp_info = [expCode,expNo,API_key]
business_info = {"EBusinessID":str(EBusinessID),"API_key":API_key,"DataType":"2","requestType":"1002"}
business_info_sub = {"EBusinessID":str(EBusinessID),"API_key":API_key,"DataType":"2","requestType":"1008"}
class KdnBaseAPI(object):

    EBusinessID = settings.KDN_EBUSINESSID
    API_key = settings.KDN_APIKEY

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
        expNo = re.sub("\D","",expNo).strip()
        kwargs['expNo'] = expNo
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

def comfirm_get(out_sid,status):            #根据物流状态自动确认收货
    out_sid = str(out_sid)
    logging.warn("comfirm_get")
    logger.warn({'action': "kdn", 'info': "start_comfirm_get:"+ out_sid})
    tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid).order_by("-id")
    confirm_get_by_content(out_sid, tradewuliu.first().content)
    packageskuitem = PackageSkuItem.objects.filter(out_sid = out_sid).values("oid")
    logger.warn({'action': "kdn", 'info': "oid_by_out_sid:" + json.dumps(list(packageskuitem))})
    if packageskuitem and int(status) == 3:
        logger.warn({'action': "kdn", 'info': "exp_num:" + out_sid})
        packageskuitem = [i['oid'] for i in packageskuitem]
        so = SaleOrder.objects.filter(oid__in = packageskuitem,status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
        if so:
            for i in so:
                logger.warn({'action': "kdn", 'info': "change_get_goods:" + out_sid})
                i.confirm_sign_order()

def confirm_get_by_content(out_sid,content):   #根据物流内容自动确认收货
    out_sid = str(out_sid)
    logging.warn("confirm_get_by_content")
    logger.warn({'action': "kdn", 'info': "confirm_get_by_content:" + out_sid})
    if content.find("\u5df2\u7b7e\u6536")!=-1 or content.find("\u59a5\u6295") != -1:
        packageskuitem = PackageSkuItem.objects.filter(out_sid=out_sid).values("oid")
        if packageskuitem:
            packageskuitem = [i['oid'] for i in packageskuitem]
            so = SaleOrder.objects.filter(oid__in=packageskuitem, status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
            if so:
                for i in so:
                    logger.warn({'action': "kdn", 'info': "confirm_sign_order:" + out_sid})
                    i.confirm_sign_order()


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
    try:
        content = json.loads(content)
    except:
        content = eval(content)
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
    logger.warn({'action': "kdn", 'info': "run kdn_subscription_sub" + json.dumps(kwargs)})
    res = requests.post("http://api.kdniao.cc/api/dist",data=kwargs)
    result = res.text
    if res.status_code == 502:
        logging.warn("物流查询失败返回"+"502 Bad Gateway"+"快递鸟那边繁忙")
        return result
    result = json.loads(result.encode('UTF-8'))
    if result["Success"] == True:
        logger.warn({'action': "kdn", 'info': "run kdn_subscription_sub" + json.dumps(kwargs) + "success"})
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


def get_exp_by_kd100(company_name,out_sid):
    type = str(company_name)
    postid=str(out_sid)
    r=random.randint(30000000000000000, 99999999999999999)
    r="0."+str(r)
    # kd100_url = 'http://www.kuaidi100.com/query?type=%s&postid=%s&id=1&valicode='
    kd100_url = "http://baidu.kuaidi100.com/query?type=%s&postid=%s&id=4&valicode=&temp=%s&sessionid="
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "User-Agent": get_random_ua(ua),
        "X-Forwarded-For": get_random_ip(),
    }
    rq_url = kd100_url % (type,postid,r)
    print rq_url
    res = requests.get(rq_url,headers=headers).text
    res = json.loads(res)
    all_info = list()
    for i in res['data']:
        each_info = dict()
        each_info['AcceptTime'] = i['ftime']
        each_info['AcceptStation'] = i['context']
        all_info.append(each_info)
    all_info.reverse()

    write_info = {
        "out_sid":res["nu"],
        "logistics_company":res["com"],
        "status": res["state"],
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": all_info
    }
    logger.warn({'action': "kdn100", 'info': "get_exp_by_kd100:" + json.dumps(write_info)})
    return write_info



if __name__ == '__main__':
    # test_info = {"expName" : '韵达快递',"expNo":"3101131769194"}
    # kdn_subscription_sub(**test_info)
    # format_content()
    comfirm_get('402076604829','3')
    # get_exp_by_kd100("yunda","1202412171242")







