# -*-coding:utf-8 -*-

try:import httplib
except ImportError:
    import http.client as httplib
import urllib
import time
import hashlib
import functools
import json
import requests
import datetime
import constant_extra
import logging
logger = logging.getLogger(__name__)

session = '6100013704d43273f44071e4a2ae123429ba28420068f5e174265168'
secret = '5d845250d49aea44c3a07d8c1d513db5'
app_key = '12545735'
method = 'cainiao.waybill.ii.search'

temp = []
def sign(secret, parameters):
    # ===========================================================================
    # '''签名方法
    # @param secret: 签名需要的密钥
    # @param parameters: 支持字典和string两种
    # '''
    # ===========================================================================
    # 如果parameters 是字典类的话
    if hasattr(parameters, "items"):
        keys = parameters.keys()
        keys.sort()

        parameters = "%s%s%s" % (secret,
                                 str().join('%s%s' % (key, parameters[key]) for key in keys),
                                 secret)
    sign = hashlib.md5(parameters).hexdigest().upper()
    return sign


def get_sign_param(method=method,session = session):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(**exp_code):
            param = dict(app_key = app_key,timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         v='2.0',method=method,sign_method = "md5",format = "json",session=session)
            param.update(exp_code)
            param.update({'sign':sign(secret,param)})
            return f(**param)
        return wrapper
    return decorator


@get_sign_param(method='cainiao.waybill.ii.search',session='6100013704d43273f44071e4a2ae123429ba28420068f5e174265168')
def get_delivery_address(*args,**kwargs):
    result = requests.get(url = 'http://gw.api.taobao.com/router/rest',params = kwargs)
    return format_delivery_address(result.text)

def format_delivery_address(address_info):
    address_info = address_info.encode('UTF-8')
    address_info = json.loads(address_info)
    print address_info
    address_info = address_info["cainiao_waybill_ii_search_response"]["waybill_apply_subscription_cols"]\
    ["waybill_apply_subscription_info"][0]['branch_account_cols']["waybill_branch_account"][0]
    print address_info
    return address_info

@get_sign_param(method='cainiao.waybill.ii.get',session='6100013704d43273f44071e4a2ae123429ba28420068f5e174265168')
def get_exp_template(**kwargs):
    print '开始向菜鸟获取单号了'
    result = requests.post(url = 'http://gw.api.taobao.com/router/rest',data = kwargs)
    result = result.text
    print {'result':result}
    if result.find("error_response") != -1:
        result = result.encode('UTF-8')
        result = json.loads(result)
        error_code = result['error_response']['code']
        logger.warn({"action":"cainiao_wuliu","error_code":error_code})
        return {"error_code":error_code}
    if result.find("print_data") != -1:
        result = result.encode('UTF-8')
        result = json.loads(result)
        print_data = result['cainiao_waybill_ii_get_response']['modules']['waybill_cloud_print_response'][0]['print_data']
        waybill_code = result['cainiao_waybill_ii_get_response']['modules']['waybill_cloud_print_response'][0]['waybill_code']
        print {"waybill_code":waybill_code}
        return {"print_data":print_data,"waybill_code":waybill_code}
    else:
        return False

@get_sign_param(method='cainiao.waybill.ii.cancel',session='6100013704d43273f44071e4a2ae123429ba28420068f5e174265168')
def cancel_exp_number(**kwargs):
    result = requests.post(url = 'http://gw.api.taobao.com/router/rest',data = kwargs)
    result = result.text
    result = result.encode('UTF-8')
    result = json.loads(result)
    if result["cainiao_waybill_ii_cancel_response"]["cancel_result"]:
        print "True"
        return True
    else:
        print "False"
        return False



# if __name__ == '__main__':
# a= {'city': '\xe8\xb5\xa4\xe5\xb3\xb0\xe5\xb8\x82',
#  'cp_code': 'STO',
#  'detail': '\xe6\x96\xb0\xe5\x9f\x8e\xe5\x8c\xba\xe4\xb8\xb4\xe6\xbd\xa2\xe5\xa4\xa7\xe8\xa1\x97\xe5\xae\x9d\xe9\x80\x9a\xe5\xa4\xa7\xe5\x8e\xa6\xe5\x9b\x9b\xe6\xa5\xbc',
#  'district': '\xe6\x9d\xbe\xe5\xb1\xb1\xe5\x8c\xba',
#  'mobile': '18804764040',
#  'name': '\xe6\x9d\x83\xe6\xb6\x9b',
#  'province': '\xe5\x86\x85\xe8\x92\x99\xe5\x8f\xa4',
#  'trade_id': 168016}


