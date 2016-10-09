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


session = '6100013704d43273f44071e4a2ae123429ba28420068f5e174265168'
secret = '5d845250d49aea44c3a07d8c1d513db5'
app_key = '12545735'
method = 'cainiao.waybill.ii.search'

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
    address_info = address_info["cainiao_waybill_ii_search_response"]["waybill_apply_subscription_cols"]\
    ["waybill_apply_subscription_info"][0]['branch_account_cols']["waybill_branch_account"][0]
    print address_info
    return address_info

@get_sign_param(method='cainiao.waybill.ii.get',session='6100013704d43273f44071e4a2ae123429ba28420068f5e174265168')
def get_exp_template(**kwargs):
    result = requests.post(url = 'http://gw.api.taobao.com/router/rest',data = kwargs)
    result = result.text
    if result.find("print_data") != -1:
        result = result.encode('UTF-8')
        result = json.loads(result)
        print_data = result['cainiao_waybill_ii_get_response']['modules']['waybill_cloud_print_response'][0]['print_data']
        waybill_code = result['cainiao_waybill_ii_get_response']['modules']['waybill_cloud_print_response'][0]['waybill_code']
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
        return True
    else:
        return False



if __name__ == '__main__':
    # get_delivery_address(cp_code='STO')
    # a = {'param_waybill_cloud_print_apply_new_request':json.dumps(constant_extra.param_waybill_cloud_print_apply_new_request)}
    # get_exp_template(**a)
    cancel_exp_number(cp_code='STO',waybill_code="3315387783334")
