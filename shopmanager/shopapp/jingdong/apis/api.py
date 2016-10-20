# -*- coding:utf8 -*-
__author__ = 'meixqhi'
import re
import inspect
import copy
import time
import datetime
import json
import urllib
import urllib2
from django.conf import settings
from celery.task import task
from celery.app.task import BaseTask
from common.utils import format_datetime, format_date
from shopapp.jingdong.utils import getJDSignature
from .exceptions import JDRequestException, JDAuthTokenException

API_FIELDS = {
    '360buy.order.search': 'order_id,vender_id,pay_type,order_total_price,order_payment,order_seller_price'
                           + ',order_state,delivery_type,invoice_info,order_remark,order_start_time,item_info_list,seller_discount'
                           + ',modified,freight_price,pin,return_order,vender_remark,pin,balance_used,payment_confirm_time'
                           + ',logistics_id,waybill,vat_invoice_info,parent_order_id,order_type,consignee_info',
    '360buy.ware.get': 'ware_id,skus,spu_id,cid,vender_id,shop_id,ware_status,title,item_num,upc_code,transport_id'
                       + ',online_time,offline_time,attributes,cost_price,market_price,jd_price,stock_num,logo,creator'
                       + ',status,weight,created,modified,outer_id,is_pay_first,is_can_vat,shop_categorys'
                       + ',ware_big_small_model,ware_pack_type'
}


def raise_except_or_ret_json(content):
    respc = json.loads(content)

    if respc.has_key('error_response'):
        error_resp = respc['error_response']
        raise JDRequestException(code=error_resp['code'],
                                 msg=error_resp['zh_desc'])

    response_body = respc.items()[0][1]

    if response_body.has_key('code'):

        code = response_body.pop('code')
        if code != u'0':
            raise JDRequestException(code=code,
                                     msg=response_body['error_description'])

    if len(response_body.items()) != 1:
        return response_body

    return response_body.items()[0][1]


def refreshAccessToken(jd_user):
    top_params = json.loads(jd_user.top_parameters)
    if (int(top_params['time']) / 1000 + top_params['expires_in']) > time.time() + 600:
        return top_params['access_token']

    params = {
        'client_id': settings.JD_APP_KEY,
        'client_secret': settings.JD_APP_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': top_params['refresh_token'],
        'state': 'jingdong',
        'scope': 'read'
    }

    req = urllib2.urlopen(settings.JD_AUTHRIZE_TOKEN_URL,
                          urllib.urlencode(params))
    resp = req.read()

    top_parameters = json.loads(resp.decode('gbk'))

    if top_parameters.get('code', None):
        raise JDAuthTokenException(code=top_parameters['code'],
                                   msg=top_parameters['error_description'])

    jd_user.top_session = top_parameters['access_token']
    jd_user.top_parameters = json.dumps(top_parameters)
    jd_user.save()

    return jd_user.top_session


def apis(api_method, method='GET', max_retries=3, limit_rate=0.5):
    """ docstring for tengxun apis """

    def decorator(func):
        """ docstring for decorator """

        func_args = copy.copy(inspect.getargspec(func).args)
        func_defaults = copy.copy(inspect.getargspec(func).defaults)

        def decorate(*args, **kwargs):
            """ docstring for decorate """

            params = {
                'method': api_method,
                'app_key': settings.JD_APP_KEY,
                'timestamp': format_datetime(datetime.datetime.now()),
                'v': '2.0'}

            app_params = {}
            if func_defaults:
                app_params.update(dict(zip(reversed(func_args),
                                           reversed(list(func_defaults)))))
            app_params.update(dict(zip(func_args, args)))
            app_params.update(kwargs)

            from shopback.users.models import User
            # refresh user taobao session
            if not app_params.has_key('access_token'):
                jd_user_id = app_params.pop('jd_user_id')
                user = User.objects.get(visitor_id=jd_user_id)
                access_token = refreshAccessToken(user)
            else:
                access_token = app_params.pop('access_token')
            # remove the field with value None
            params['access_token'] = access_token
            params_copy = dict(app_params)
            for k, v in params_copy.iteritems():
                if v == None:
                    app_params.pop(k)
                elif type(v) == bool:
                    app_params[k] = v and 'true' or 'false'
                elif type(v) == unicode:
                    app_params[k] = v.encode('utf8')
                elif type(v) == datetime.datetime:
                    app_params[k] = format_datetime(v)
                elif type(v) == datetime.date:
                    app_params[k] = format_date(v)

            params['360buy_param_json'] = json.dumps(app_params)
            params['sign'] = getJDSignature(params,
                                            settings.JD_APP_SECRET,
                                            both_side=True)
            params = urllib.urlencode(params)
            url = settings.JD_API_ENDPOINT

            if method == 'GET':
                uri = '%s?%s' % (url, params)
                req = urllib2.urlopen(uri)
                content = req.read()
            else:
                rst = urllib2.Request(url)
                req = urllib2.urlopen(rst, params)
                content = req.read()

            return raise_except_or_ret_json(content)

        return decorate

    return decorator


###################### 京东用户处理 ###################
@apis('jingdong.seller.vender.info.get')
def jd_seller_vender_info_get(jd_user_id=None):
    pass


@apis('jingdong.vender.shop.query')
def jd_vender_shop_query(jd_user_id=None):
    pass


###################### 京东用户处理 ###################
@apis('360buy.delivery.logistics.get')
def jd_delivery_logistics_get(jd_user_id=None):
    pass


###################### 京东订单处理 ###################
@apis('360buy.order.search', method='POST')
def jd_order_search(start_date=None, end_date=None, dateType=None,
                    order_state=None, page=None, page_size=None, sortType=None,
                    optional_fields=API_FIELDS['360buy.order.search'], jd_user_id=None):
    pass


@apis('360buy.order.get', method='POST')
def jd_order_get(order_id=None, order_state=None,
                 optional_fields=API_FIELDS['360buy.order.search'], jd_user_id=None):
    pass


@apis('360buy.order.sop.outstorage', method='POST')
def jd_order_sop_outstorage(order_id=None, logistics_id=None, waybill=None,
                            trade_no=None, jd_user_id=None):
    pass


@apis('360buy.order.sop.waybill.update', method='POST')
def jd_order_sop_waybill_update(order_id=None, logistics_id=None, waybill=None,
                                trade_no=None, jd_user_id=None):
    pass


###################### 商品管理 ###################
@apis('360buy.ware.get', method='POST')
def jd_ware_get(ware_id=None, fields=API_FIELDS['360buy.ware.get'], jd_user_id=None):
    pass


@apis('360buy.wares.list.get', method='POST')
def jd_wares_list_get(ware_ids=None, fields=API_FIELDS['360buy.ware.get'], jd_user_id=None):
    pass


@apis('360buy.wares.search', method='POST')
def jd_wares_search(cid=None, start_price=None, end_price=None, page=None, page_size=None
                    , title=None, order_by=None, start_time=None, end_time=None, ware_status=None
                    , start_modified=None, end_modified=None, itemNum=None, shopCategoryId=None
                    , parentShopCategoryId=None, fields=None, jd_user_id=None):
    pass


@apis('360buy.ware.update', method='POST')
def jd_ware_update(ware_id=None, upc_code=None, item_num=None, outer_id=None, stock_num=None
                   , sku_properties=None, sku_stocks=None, jd_user_id=None):
    pass


@apis('360buy.sku.stock.update')
def jd_sku_stock_update(sku_id=None, outer_id=None, quantity=None, jd_user_id=None):
    pass


@apis('jingdong.afsservice.waitaudit.get', method='POST')
def jd_afsservice_waitaudit_get(afsServiceId=None, pageNumber=None, pageSize=None, customerPin=None
                                , orderId=None, afsApplyTimeBegin=None, afsApplyTimeEnd=None, fields=None,
                                jd_user_id=None):
    pass


@apis('jingdong.afsservice.waitprocesstask.get', method='POST')
def jd_afsservice_waitfetch_get(afsServiceId=None, pageNumber=None, pageSize=None, customerPin=None
                                , orderId=None, afsApplyTimeBegin=None, afsApplyTimeEnd=None, fields=None
                                , approvedDateBegin=None, approvedDateEnd=None, expressCode=None, jd_user_id=None):
    pass
