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
from common.utils import getSignatureTaoBao, format_datetime, format_date, refresh_session
from .exceptions import *

import logging

logger = logging.getLogger('django.request')

reject_regex = re.compile(r'^isv.\w+-service-rejection$')

API_FIELDS = {
    'taobao.user.seller.get': 'user_id,uid,nick,sex,buyer_credit,seller_credit,location,created,last_visit,'
                              + 'birthday,type,has_more_pic,item_img_num,item_img_size,prop_img_num,prop_img_size,auto_repost,'
                              + 'promoted_type,status,alipay_bind,consumer_protection,alipay_account,alipay_no',
    'taobao.user.buyer.get': 'user_id,nick,sex,buyer_credit,avatar,has_shop,vip_info',
    'taobao.itemcats.get': 'cid,parent_cid,name,is_parent,status,sort_order',

    'taobao.itemcats.authorize.get': 'brand.vid,brand.name,item_cat.cid,item_cat.name,item_cat.status,'
                                     + 'item_cat.sort_order,item_cat.parent_cid,item_cat.is_parent,xinpin_item_cat.cid,xinpin_item_cat.name,'
                                     + 'xinpin_item_cat.status,xinpin_item_cat.sort_order,xinpin_item_cat.parent_cid,xinpin_item_cat.is_parent',

    'taobao.itemprops.get': 'pid, name, must, multi, prop_values',

    'taobao.itempropvalues.get': 'cid,pid,prop_name,vid,name,name_alias,status,sort_order',

    'taobao.item.get': 'has_showcase,detail_url,num_iid,title,outer_id,price,approve_status,delist_time,list_time,'
                       + 'modified,num,props_name,property_alias,nick,type,cid,pic_url,num,props,valid_thru,price,has_discount,'
                       + 'has_invoice,has_warranty,postage_id,seller_cids',
    'taobao.items.list.get': 'item',
    'taobao.items.get': 'num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee,volume,score,location'
                        + ',with_hold_quantity,delivery_time',

    'taobao.items.search': 'iid,num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee',

    'taobao.item.skus.get': 'sku_id,num_iid,created,modified,num_iid,outer_id,price,properties,quantity,sku_id,'
                            + 'status,properties_name,with_hold_quantity,sku_delivery_time',

    'taobao.products.get': 'product_id,outer_id,name,inner_name,created,modified,cid,cat_name,tsc,props,'
                           + 'props_str,binds,binds_str,sale_props,sale_props_str,collect_num,price,desc,pic_url,product_imgs,'
                           + 'product_prop_imgs,pic_path,vertical_market,customer_props,property_alias,level,status',

    'taobao.products.search': 'product_id,name,pic_url,cid,props,price,tsc',

    'taobao.items.inventory.get': 'approve_status,num_iid,title,nick,type,cid,pic_url,num,props,valid_thru,list_time'
                                  + ',price,has_discount,has_invoice,has_warranty,has_showcase, modified,delist_time,postage_id,seller_cids,outer_id',

    'taobao.items.onsale.get': 'num_iid,cid,outer_id,num,seller_cids,approve_status,type,valid_thru,price,postage_id,'
                               + 'has_showcase,list_time,delist_time,has_discount,props,title,has_invoice,pic_url,detail_url',

    'taobao.trades.sold.get': 'seller_nick,buyer_nick,title,type,created,tid,status,modified,payment,discount_fee,'
                              + 'adjust_fee,post_fee,total_fee,received_payment,commission_fee,buyer_obtain_point_fee,point_fee,real_point_fee,'
                              + 'pic_path,pay_time,end_time,consign_time,num_iid,num,price,shipping_type,receiver_name,receiver_state,'
                              + 'receiver_city,receiver_district,receiver_address,receiver_zip,receiver_mobile,receiver_phone,buyer_message,'
                              + 'buyer_memo,seller_memo,seller_flag,orders',

    'taobao.trade.get': 'seller_nick,buyer_nick,title, type,created,tid,seller_rate,buyer_rate,status,payment,discount_fee,'
                        + 'adjust_fee,post_fee,total_fee,pay_time,end_time,modified,consign_time,buyer_obtain_point_fee,point_fee,'
                        + 'real_point_fee,received_payment,commission_fee,buyer_memo,seller_memo,alipay_no,buyer_message,pic_path,'
                        + 'num_iid,num,price,cod_fee,cod_status,shipping_type,orders',

    'taobao.trade.fullinfo.get': 'seller_nick,buyer_nick,title,type,created,tid,status,modified,payment,discount_fee,'
                                 + 'adjust_fee,post_fee,total_fee,received_payment,commission_fee,buyer_obtain_point_fee,point_fee,real_point_fee,'
                                 + 'pic_path,pay_time,end_time,consign_time,num_iid,num,price,shipping_type,receiver_name,receiver_state,receiver_city,'
                                 + 'receiver_district,receiver_address,receiver_zip,receiver_mobile,receiver_phone,buyer_message,buyer_memo,'
                                 + 'seller_memo,seller_flag,orders,send_time,is_brand_sale,is_force_wlb,trade_from,is_lgtype,lg_aging,'
                                 + 'lg_aging_type,buyer_rate,seller_rate,seller_can_rate,is_part_consign,step_paid_fee,step_trade_status',
    # promotion_details,

    'taobao.trade.amount.get': 'tid,alipay_no,created,pay_time,end_time,total_fee,payment,post_fee,cod_fee,commission_fee,'
                               + 'buyer_obtain_point_fee,order_amounts,promotion_details',

    'taobao.logistics.companies.get': 'id,code,name,reg_mail_no',

    'taobao.logistics.orders.detail.get': 'tid,order_code,is_quick_cod_order,out_sid,company_name,seller_id,seller_nick,'
                                          + 'buyer_nick,item_title,delivery_start,delivery_end,receiver_name,receiver_phone,receiver_mobile,type,created,'
                                          + 'modified,seller_confirm,company_name,is_success,freight_payer,status,receiver_location',

    'taobao.logistics.orders.get': 'tid,seller_nick,buyer_nick,delivery_start,delivery_end,out_sid,item_title,receiver_name,'
                                   + 'created,modified,status,type,freight_payer,seller_confirm,company_name',

    'taobao.refunds.receive.get': 'refund_id,tid,title,buyer_nick,num_iid,seller_nick,total_fee,status,created,refund_fee,'
                                  + 'oid,good_status,company_name,sid,payment,reason,desc,has_good_return,modified,order_status',

    'taobao.refund.get': 'refund_id,alipay_no,tid,oid,buyer_nick,seller_nick,total_fee,created,refund_fee,has_good_return,'
                         + 'payment,reason,desc,num_iid,title,price,num,good_return_time,company_name,sid,address,shipping_type,'
                         + 'refund_remind_timeout,cs_status,status,good_status',

    'taobao.traderates.get': 'num_iid,tid,oid,role,nick,result,created,rated_nick,item_title,item_price,content,reply',
    'taobao.fenxiao.products.get': 'skus,images',
    'taobao.trade.close': 'tid,close_reason',
    'taobao.tmc.user.get': 'user_nick,topics,user_id,is_valid,created,modified'
}


def raise_except_or_ret_json(content):
    content = json.loads(content)

    if not isinstance(content, (dict,)):
        raise ContentNotRightException(sub_msg=content)
    elif content.has_key('error_response'):
        content = content['error_response']
        code = content.get('code', None)
        sub_code = str(content.get('sub_code', None))
        msg = content.get('msg', '400')
        sub_msg = content.get('sub_msg', '')

        if sub_code == u'isp.remote-connection-error':
            raise RemoteConnectionException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'isp.remote-service-timeout':
            raise APIConnectionTimeOutException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif reject_regex.match(sub_code):
            raise ServiceRejectionException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'isv.invalid-parameter:user_id_num':
            raise UserFenxiaoUnuseException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'accesscontrol.limited-by-app-access-count':
            raise AppCallLimitedException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'isv.permission-api-package-limit':
            raise InsufficientIsvPermissionsException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'session-expired':
            raise SessionExpiredException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'isv.logistics-offline-service-error:B04':
            raise LogisticServiceBO4Exception(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        elif sub_code == u'isv.logistics-offline-service-error:B60':
            raise LogisticServiceB60Exception(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
        else:
            raise TaobaoRequestException(
                code=code, msg=msg, sub_code=sub_code, sub_msg=sub_msg)
    return content


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
                'format': 'json',
                'v': '2.0',}

            if func_defaults:
                params.update(dict(zip(reversed(func_args), reversed(list(func_defaults)))))
            params.update(dict(zip(func_args, args)))
            params.update(kwargs)

            from shopback.users.models import User
            # refresh user taobao session
            tb_user_id = params.pop('tb_user_id')
            user = User.objects.get(visitor_id=tb_user_id)
            # refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
            # remove the field with value None
            params['access_token'] = user.top_session
            params_copy = dict(params)
            for k, v in params_copy.iteritems():
                if v == None:
                    params.pop(k)
                elif type(v) == bool:
                    params[k] = v and 'true' or 'false'
                elif type(v) == unicode:
                    params[k] = v.encode('utf8')
                elif type(v) == datetime.datetime:
                    params[k] = format_datetime(v)
                elif type(v) == datetime.date:
                    params[k] = format_date(v)

            params_copy = None
            url = settings.TAOBAO_API_ENDPOINT
            if method == 'GET':
                uri = '%s?%s' % (url, urllib.urlencode(params))
                req = urllib2.urlopen(uri)
                content = req.read()
            else:
                rst = urllib2.Request(url)
                req = urllib2.urlopen(rst, urllib.urlencode(params))
                content = req.read()

            return raise_except_or_ret_json(content)

        return decorate

    return decorator


############# user apis ###################
@apis('taobao.user.seller.get')
def taobao_user_seller_get(fields=API_FIELDS['taobao.user.seller.get'], tb_user_id=None):
    pass


@apis('taobao.user.buyer.get')
def taobao_user_buyer_get(nicks=None, fields=API_FIELDS['taobao.user.buyer.get'], tb_user_id=None):
    pass


@apis('taobao.users.get')
def taobao_users_get(nicks=None, fields=API_FIELDS['taobao.user.seller.get'], tb_user_id=None):
    pass


############# itemcats apis ###################
@apis('taobao.itemcats.authorize.get')
def taobao_itemcats_authorize_get(parent_cid=None, cids=None, fields=API_FIELDS['taobao.itemcats.authorize.get'],
                                  tb_user_id=None):
    pass


@apis('taobao.itemcats.get')
def taobao_itemcats_get(parent_cid=None, cids=None, fields=API_FIELDS['taobao.itemcats.get'], tb_user_id=None):
    pass


@apis('taobao.itemcats.increment.get')
def taobao_itemcats_increment_get(cids=None, type=None, days=None, tb_user_id=None):
    pass


@apis('taobao.itemprops.get')
def taobao_itemprops_get(cid=None, pid=None, fields=API_FIELDS['taobao.itemprops.get'], tb_user_id=None):
    pass


@apis('taobao.itempropvalues.get')
def taobao_itempropvalues_get(cid=None, pvs=None, fields=API_FIELDS['taobao.itempropvalues.get'], tb_user_id=None):
    pass


@apis('taobao.topats.itemcats.get')
def taobao_topats_itemcats_get(seller_type=None, cids=None, output_format='json', tb_user_id=None):
    pass


############# items apis ###################

@apis('taobao.item.get', max_retries=3, limit_rate=5)
def taobao_item_get(num_iid=None, fields=API_FIELDS['taobao.item.get'], tb_user_id=None):
    pass


@apis('taobao.item.update')
def taobao_item_update(num_iid=None, num=None, tb_user_id=None):
    pass


@apis('taobao.item.quantity.update')
def taobao_item_quantity_update(num_iid=None, quantity=None, sku_id=None, outer_id=None, type=1, tb_user_id=None):
    pass


@apis('taobao.item.update.delisting')
def taobao_item_update_delisting(num_iid=None, tb_user_id=None):
    pass


@apis('taobao.item.update.listing')
def taobao_item_update_listing(num_iid=None, num=0, tb_user_id=None):
    pass


@apis('taobao.items.list.get')
def taobao_items_list_get(num_iids=None, fields=API_FIELDS['taobao.items.list.get'], tb_user_id=None):
    pass


@apis('taobao.products.get')
def taobao_products_get(nick=None, page_no=1, page_size=20, fields=API_FIELDS['taobao.products.get'], tb_user_id=None):
    pass


@apis('taobao.items.search')
def taobao_items_search(q=None, cid=None, nicks=None, props=None, product_id=None, order_by=None, page_no=None,
                        page_size=None, fields=API_FIELDS['taobao.items.search'], tb_user_id=None):
    pass


@apis('taobao.items.get')
def taobao_items_get(q=None, cid=None, nicks=None, props=None, product_id=None, order_by=None, page_no=None,
                     page_size=None, fields=API_FIELDS['taobao.items.get'], tb_user_id=None):
    pass


@apis('taobao.item.sku.get')
def taobao_item_sku_get(num_iid=None, sku_id=None, fields=API_FIELDS['taobao.item.skus.get'], nick=None,
                        tb_user_id=None):
    pass


@apis('taobao.item.skus.get')
def taobao_item_skus_get(num_iids=None, fields=API_FIELDS['taobao.item.skus.get'], tb_user_id=None):
    pass


@apis('taobao.products.search')
def taobao_products_search(q=None, cid=None, props=None, fields=API_FIELDS['taobao.products.search'], tb_user_id=None):
    pass


@apis('taobao.items.inventory.get')
def taobao_items_inventory_get(q=None, banner=None, cid=None, seller_cids=None, page_no=None, page_size=None,
                               fields=API_FIELDS['taobao.items.inventory.get'], tb_user_id=None):
    pass


@apis('taobao.items.onsale.get')
def taobao_items_onsale_get(q=None, banner=None, cid=None, seller_cids=None, page_no=None, page_size=None,
                            fields=API_FIELDS['taobao.items.onsale.get'], tb_user_id=None):
    pass


@apis('taobao.item.recommend.add')
def taobao_item_recommend_add(num_iid=None, tb_user_id=None):
    pass


############# trades apis ###################
@apis('taobao.trade.get')
def taobao_trade_get(tid=None, fields=API_FIELDS['taobao.trade.get'], tb_user_id=None):
    pass


@apis('taobao.trades.sold.get', max_retries=20, limit_rate=10)
def taobao_trades_sold_get(start_created=None, end_created=None, page_no=None, page_size=None, use_has_next=None,
                           status=None, type=None,
                           fields=API_FIELDS['taobao.trades.sold.get'], tb_user_id=None):
    pass


@apis('taobao.trades.sold.increment.get', max_retries=20, limit_rate=10)
def taobao_trades_sold_increment_get(start_modified=None, end_modified=None, page_no=None, page_size=None,
                                     use_has_next=None, status=None, type=None,
                                     fields=API_FIELDS['taobao.trades.sold.get'], tb_user_id=None):
    pass


@apis('taobao.trade.fullinfo.get', max_retries=3, limit_rate=1)
def taobao_trade_fullinfo_get(tid=None, fields=API_FIELDS['taobao.trade.fullinfo.get'], tb_user_id=None):
    pass


@apis('taobao.topats.trades.fullinfo.get')
def taobao_topats_trades_fullinfo_get(tids=None, fields=API_FIELDS['taobao.trade.fullinfo.get'], tb_user_id=None):
    pass


@apis('taobao.trade.amount.get', max_retries=5, limit_rate=1)
def taobao_trade_amount_get(tid=None, fields=API_FIELDS['taobao.trade.amount.get'], tb_user_id=None):
    pass


@apis('taobao.trade.memo.update')
def taobao_trade_memo_update(tid=None, memo=None, flag=None, reset=None, tb_user_id=None):
    pass


@apis('taobao.trade.memo.add')
def taobao_trade_memo_add(tid=None, memo=None, flag=None, tb_user_id=None):
    pass


@apis('taobao.topats.trades.sold.get')
def taobao_topats_trades_sold_get(start_time=None, end_time=None, fields=API_FIELDS['taobao.trades.sold.get'],
                                  tb_user_id=None):
    pass


@apis('taobao.trade.postage.update')
def taobao_trade_postage_update(tid=None, post_fee=None, tb_user_id=None):
    pass


@apis('taobao.trade.shippingaddress.update')
def taobao_trade_shippingaddress_update(tid=None, receiver_name=None, receiver_phone=None, receiver_mobile=None,
                                        receiver_state=None
                                        , receiver_city=None, receiver_district=None, receiver_address=None,
                                        receiver_zip=None, tb_user_id=None):
    pass


@apis('taobao.trade.close')
def taobao_trade_close(tid=None, close_reason=None):
    pass


############# post apis ###################
@apis('taobao.logistics.companies.get')
def taobao_logistics_companies_get(fields=API_FIELDS['taobao.logistics.companies.get'], tb_user_id=None):
    pass


@apis('taobao.logistics.orders.detail.get', max_retries=10, limit_rate=5)
def taobao_logistics_orders_detail_get(tid=None, seller_confirm='yes', start_created=None, end_created=None,
                                       page_no=None, page_size=None,
                                       fields=API_FIELDS['taobao.logistics.orders.detail.get'], tb_user_id=None):
    pass


@apis('taobao.logistics.orders.get')
def taobao_logistics_orders_get(tid=None, seller_confirm='yes', start_created=None, end_created=None, page_no=None,
                                page_size=None,
                                fields=API_FIELDS['taobao.logistics.orders.get'], tb_user_id=None):
    pass


@apis('taobao.logistics.offline.send')
def taobao_logistics_offline_send(tid=None, out_sid=None, company_code=None, sender_id=None, cancel_id=None,
                                  feature=None, tb_user_id=None):
    pass


@apis('taobao.logistics.online.send')
def taobao_logistics_online_send(tid=None, out_sid=None, company_code=None, sender_id=None, cancel_id=None,
                                 feature=None, tb_user_id=None):
    pass


@apis('taobao.logistics.online.confirm')
def taobao_logistics_online_confirm(tid=None, out_sid=None, tb_user_id=None):
    pass


@apis('taobao.logistics.consign.resend')
def taobao_logistics_consign_resend(tid=None, out_sid=None, company_code=None, tb_user_id=None):
    pass


###############  fengxiao apis  ##################
@apis('taobao.fenxiao.orders.get', max_retries=20, limit_rate=20)
def taobao_fenxiao_orders_get(start_created=None, end_created=None, time_type=None, purchase_order_id=None,
                              trade_type=None,
                              page_no=None, page_size=None, status=None, tb_user_id=None):
    pass


@apis('taobao.fenxiao.products.get', max_retries=20, limit_rate=20)
def taobao_fenxiao_products_get(outer_id=None, productcat_id=None, status=None, pids=None, item_ids=None,
                                start_modified=None, end_modified=None,
                                page_no=None, page_size=None, fields=API_FIELDS['taobao.fenxiao.products.get'],
                                tb_user_id=None):
    pass


@apis('taobao.fenxiao.login.user.get')
def taobao_fenxiao_login_user_get(tb_user_id=None):
    pass


@apis('taobao.fenxiao.product.update')
def taobao_fenxiao_product_update(pid=None, outer_id=None, quantity=None,
                                  sku_ids=None, sku_quantitys=None, tb_user_id=None):
    pass


################  refund apis  ##################
@apis('taobao.refunds.receive.get', max_retries=20, limit_rate=20)
def taobao_refunds_receive_get(status=None, start_modified=None, end_modified=None,
                               type='guarantee_trade,auto_delivery,fenxiao',
                               page_no=None, page_size=None, fields=API_FIELDS['taobao.refunds.receive.get'],
                               tb_user_id=None):
    pass


@apis('taobao.refund.get')
def taobao_refund_get(refund_id=None, fields=API_FIELDS['taobao.refund.get'], tb_user_id=None):
    pass


################  topats result ################
@apis('taobao.topats.result.get')
def taobao_topats_result_get(task_id=None, tb_user_id=None):
    pass


################  increament service ###########

@apis('tmall.product.specs.get')
def tmall_product_specs_get(product_id=None, properties=None, cat_id=None, tb_user_id=None):
    pass


################  traderate api ###########

@apis('taobao.traderates.get')
def taobao_traderates_get(rate_type='get', role='buyer', tid=None, num_iid=None, result=None, page_no=None,
                          page_size=None, start_date=None
                          , end_date=None, use_has_next=False, fields=API_FIELDS['taobao.traderates.get'],
                          tb_user_id=None):
    pass


@apis('taobao.traderate.explain.add')
def taobao_traderate_explain_add(oid=None, reply=None, tb_user_id=None):
    pass


################## 主动通知接口 ####################
@apis('taobao.increment.authorize.message.get')
def taobao_increment_authorize_message_get(topic=None, status=None, nick=None, start_modified=None, end_modified=None,
                                           page_no=None, page_size=None, tb_user_id=None):
    pass


@apis('taobao.increment.customer.permit')
def taobao_increment_customer_permit(type='get,syn,notify', topics='trade;refund;item',
                                     status='all;all;ItemAdd,ItemUpdate', tb_user_id=None):
    pass


@apis('taobao.increment.customers.get')
def taobao_increment_customers_get(nicks=None, page_size=None, page_no=None, type=None,
                                   fields="nick,created,status,type,subscription", tb_user_id=None):
    pass


@apis('taobao.increment.customer.stop')
def taobao_increment_customer_stop(nick=None, type=None, tb_user_id=None):
    pass


@apis('taobao.comet.discardinfo.get')
def taobao_comet_discardinfo_get(types=None, user_id=None, start=None, end=None, tb_user_id=None):
    pass


@apis('taobao.increment.items.get')
def taobao_increment_items_get(status=None, nick=None, start_modified=None, end_modified=None, page_no=None,
                               page_size=None, tb_user_id=None):
    pass


@apis('taobao.increment.refunds.get')
def taobao_increment_refunds_get(status=None, nick=None, start_modified=None, end_modified=None, page_no=None,
                                 page_size=None, tb_user_id=None):
    pass


@apis('taobao.increment.trades.get')
def taobao_increment_trades_get(status=None, type=None, nick=None, start_modified=None, end_modified=None, page_no=None,
                                page_size=None, tb_user_id=None):
    pass


################## CRM ##################
@apis('taobao.crm.members.search')
def taobao_crm_members_search(buyer_nick=None, grade=None, province=None, city=None, page_size=None, current_page=None,
                              tb_user_id=None):
    pass


################## Message Service ##################
@apis('taobao.tmc.user.permit')
def taobao_tmc_user_permit(topics=None, tb_user_id=None):
    pass


@apis('taobao.tmc.messages.consume')
def taobao_tmc_messages_consume(group_name=None, quantity=None, tb_user_id=None):
    pass


@apis('taobao.tmc.messages.confirm')
def taobao_tmc_messages_confirm(group_name=None, s_message_ids=None, f_message_ids=None, tb_user_id=None):
    pass


@apis('taobao.tmc.user.cancel')
def taobao_tmc_user_cancel(nick=None, tb_user_id=None):
    pass


@apis('taobao.tmc.user.get')
def taobao_tmc_user_get(nick=None, fields=API_FIELDS['taobao.tmc.user.get'], tb_user_id=None):
    pass
