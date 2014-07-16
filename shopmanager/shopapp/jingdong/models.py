#-*- coding:utf8 -*-
import time
import json
import datetime
from django.db import models
from shopback.signals import user_logged_in
from shopapp.jingdong import apis
import logging

logger = logging.getLogger('django.request')

class JDShop(models.Model):
    
    shop_id   =  models.CharField(max_length=32,primary_key=True,verbose_name=u'店铺ID')
    vender_id =  models.CharField(max_length=32,blank=True,verbose_name=u'商家ID')
    shop_name =  models.CharField(max_length=32,blank=True,verbose_name=u'店铺名称')
    open_time =  models.DateTimeField(blank=True,null=True,verbose_name=u'开店时间')
    
    logo_url  =  models.CharField(max_length=512,blank=True,verbose_name=u'LOGO')
    brief     =  models.CharField(max_length=2000,blank=True,verbose_name=u'店铺简介')
    category_main = models.BigIntegerField(null=True,verbose_name=u'店铺简介')
    category_main_name = models.CharField(max_length=2000,blank=True,verbose_name=u'店铺简介')
    
    class Meta:
        db_table = 'shop_jingdong_shop'
        verbose_name=u'京东商铺'
        verbose_name_plural = u'京东商铺列表'

class JDOrder(models.Model):
    """
    {
        "pay_type": "4-\u5728\u7ebf\u652f\u4ed8", 
        "delivery_type": "\u4efb\u610f\u65f6\u95f4", 
        "order_type": "22", 
        "order_payment": "269.00", 
        "order_remark": "", 
        "order_id": "1630526312", 
        "item_info_list": [
          {
            "sku_id": "1136497777", 
            "sku_name": "**", 
            "jd_price": "279.00", 
            "ware_id": "1068177860", 
            "item_total": "1", 
            "outer_sku_id": "", 
            "gift_point": "0"
          }
        ], 
        "seller_discount": "10.00", 
        "modified": "2014-07-09 23:43:02", 
        "order_start_time": "2014-07-09 23:35:34", 
        "invoice_info": "\u4e0d\u9700\u8981\u5f00\u5177\u53d1\u7968", 
        "vender_id": "67243", 
        "freight_price": "0.00", 
        "order_state": "WAIT_SELLER_STOCK_OUT", 
        "consignee_info": {
          "province": "\u5e7f\u4e1c", 
          "city": "\u6df1\u5733\u5e02", 
          "mobile": "13603060735", 
          "telephone": "13603060735", 
          "full_address": "**", 
          "county": "\u9f99\u5c97\u533a", 
          "fullname": "\u6d2a\u82f1\u70c8"
        }, 
        "coupon_detail_list": [
          {
            "order_id": "1630526312", 
            "sku_id": "", 
            "coupon_price": "10.00", 
            "coupon_type": "35-\u6ee1\u8fd4\u6ee1\u9001(\u8fd4\u73b0)"
          }
        ], 
        "order_total_price": "279.00", 
        "order_seller_price": "269.00"
      }
    """
    order_id   =  models.CharField(max_length=32,primary_key=True,verbose_name=u'订单ID')
    shop       =  models.ForeignKey(JDShop,verbose_name=u'所属商铺')
    
    pay_type   =  models.CharField(max_length=16,blank=True,verbose_name=u'支付方式')
    order_total_price  =  models.FloatField(default=0.0,verbose_name=u'总金额')
    order_payment      =  models.FloatField(default=0.0,verbose_name=u'实付款')
    order_seller_price =  models.FloatField(default=0.0,verbose_name=u'货款金额')
    freight_price      =  models.FloatField(default=0.0,verbose_name=u'运费')
    seller_discount    =  models.FloatField(default=0.0,verbose_name=u'优惠金额')
    
    delivery_type        =  models.CharField(max_length=32,blank=True,verbose_name=u'送货类型')
    invoice_info         =  models.CharField(max_length=32,blank=True,verbose_name=u'发票信息')
    
    order_start_time     =  models.DateTimeField(blank=True,null=True,verbose_name=u'下单时间')
    order_end_time       =  models.DateTimeField(blank=True,null=True,verbose_name=u'结单时间')
    
    consignee_info       =  models.TextField(max_length=1000,blank=True,verbose_name=u'收货人信息')
    item_info_list       =  models.TextField(max_length=10000,blank=True,verbose_name=u'商品列表')
    coupon_detail_list   =  models.TextField(max_length=2000,blank=True,verbose_name=u'优惠列表')
    return_order         =  models.CharField(max_length=2,blank=True,verbose_name=u'换货标识')
    
    pin                  =  models.CharField(max_length=64,blank=True,verbose_name=u'账号信息')
    balance_used         =  models.FloatField(default=0.0,verbose_name=u'余额支付金额')
    modified             =  models.DateTimeField(blank=True,null=True,verbose_name=u'修改时间')
    payment_confirm_time =  models.DateTimeField(blank=True,null=True,verbose_name=u'付款时间')
    logistics_id       =  models.CharField(max_length=128,blank=True,verbose_name=u'物流公司ID')
    waybill            =  models.CharField(max_length=128,blank=True,verbose_name=u'运单号')
    vat_invoice_info   =  models.CharField(max_length=256,blank=True,verbose_name=u'增值税发票')
    
    parent_order_id    =  models.CharField(max_length=32,blank=True,verbose_name=u'父订单号')
    
    order_remark         =  models.CharField(max_length=512,blank=True,verbose_name=u'买家备注')
    vender_remark        =  models.CharField(max_length=1000,blank=True,verbose_name=u'卖家单号')
    
    order_type         =  models.CharField(max_length=8,blank=True,verbose_name=u'订单类型')
    order_state        =  models.CharField(max_length=32,blank=True,verbose_name=u'订单状态')
    order_state_remark =  models.CharField(max_length=128,blank=True,verbose_name=u'订单状态说明')
    
    class Meta:
        db_table = 'shop_jingdong_order'
        verbose_name=u'京东订单'
        verbose_name_plural = u'京东订单列表'
        

def add_jingdong_user(sender, user,top_session,
                      top_parameters, *args, **kwargs):
    """docstring for user_logged_in"""
    
    logger.debug('debug add_jingdong_user:%s'%sender)
    
    profile = user.get_profile()
    
    userdict = apis.jd_seller_vender_info_get(jd_user_id=top_parameters['uid'])

    profile.uid  = userdict['vender_id']
    profile.visitor_id = userdict['shop_id']
    profile.nick = userdict['shop_name']

    profile.save()
    
    #初始化系统数据
    #from shopback.users.tasks import initSystemDataFromAuthTask
    
    #initSystemDataFromAuthTask.delay(profile.visitor_id)
    
    
user_logged_in.connect(add_jingdong_user,
                       sender='jingdong',
                       dispatch_uid='jingdong_logged_in')
