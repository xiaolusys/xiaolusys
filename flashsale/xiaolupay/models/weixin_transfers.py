# encoding=utf8
from __future__ import unicode_literals

from django.db import models, transaction
from core.models import BaseModel


class WeixinTransfers(BaseModel):

    mch_id = models.CharField(max_length=32, verbose_name=u'商户号')
    wxappid = models.CharField(max_length=32, verbose_name=u'公众号appid')

    mch_billno = models.CharField(max_length=32, unique=True, verbose_name=u'商户订单号')
    payment_no = models.CharField(max_length=32, blank=True, verbose_name=u'微信订单号')

    openid = models.CharField(max_length=32, db_index=True, verbose_name=u'接收者openid')
    name = models.CharField(max_length=32, blank=True, verbose_name=u'收款人姓名')
    amount = models.IntegerField(default=0, verbose_name=u'金额(分)')
    desc = models.CharField(max_length=256, blank=True, verbose_name=u'企业付款描述信息')

    return_code = models.CharField(max_length=16, verbose_name=u'返回状态码')
    return_msg = models.CharField(max_length=128, blank=True, verbose_name=u'返回信息')

    result_code = models.CharField(max_length=16, blank=True, verbose_name=u'业务结果')
    err_code = models.CharField(max_length=32, blank=True, verbose_name=u'错误代码')
    err_code_des = models.CharField(max_length=128, blank=True, verbose_name=u'错误代码描述')

    request_body = models.TextField(verbose_name=u'请求参数')
    response_body = models.TextField(verbose_name=u'响应结果')

    class Meta:
        db_table = 'xiaolupay_weixin_transfers'
        app_label = 'xiaolupay'
        verbose_name = u'小鹿支付/微信企业转账'
        verbose_name_plural = u'小鹿支付/微信企业转账'

